"""
License views for the asset management system.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, F, Case, When, DecimalField
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from datetime import timedelta

from .models import License, LicenseAssignment
from .serializers import (
    LicenseSerializer, LicenseListSerializer, LicenseAssignmentSerializer,
    LicenseAssignmentCreateSerializer, LicenseUsageStatsSerializer,
    LicenseCostAnalysisSerializer
)
from apps.employees.models import Employee
from common.permissions import IsAdminOrReadOnly


class LicenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing software licenses with CRUD operations and advanced features.
    
    Provides:
    - Standard CRUD operations for licenses
    - License assignment and revocation
    - Usage statistics and alerts
    - Cost analysis and reporting
    - Expiry monitoring and notifications
    """
    
    queryset = License.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LicenseListSerializer
        return LicenseSerializer
    
    def get_queryset(self):
        """
        Filter licenses based on query parameters.
        
        Supported filters:
        - software_name: Filter by software name (case-insensitive contains)
        - license_type: Filter by license type
        - pricing_model: Filter by pricing model
        - expiring_soon: Show licenses expiring within 30 days
        - expired: Show expired licenses
        - fully_utilized: Show fully utilized licenses
        - department: Filter by assigned employee department
        """
        queryset = License.objects.all()
        
        # Text filters
        software_name = self.request.query_params.get('software_name')
        if software_name:
            queryset = queryset.filter(software_name__icontains=software_name)
        
        license_type = self.request.query_params.get('license_type')
        if license_type:
            queryset = queryset.filter(license_type__icontains=license_type)
        
        pricing_model = self.request.query_params.get('pricing_model')
        if pricing_model:
            queryset = queryset.filter(pricing_model=pricing_model)
        
        # Status filters
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon and expiring_soon.lower() == 'true':
            expiry_threshold = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(expiry_date__lte=expiry_threshold, expiry_date__gte=timezone.now().date())
        
        expired = self.request.query_params.get('expired')
        if expired and expired.lower() == 'true':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date())
        
        fully_utilized = self.request.query_params.get('fully_utilized')
        if fully_utilized and fully_utilized.lower() == 'true':
            queryset = queryset.filter(available_count=0)
        
        # Department filter (through assignments)
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(
                assignments__employee__department__icontains=department,
                assignments__status='ACTIVE'
            ).distinct()
        
        return queryset.order_by('software_name', 'license_type')
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign license to an employee.
        
        Expected payload:
        {
            "employee_id": "uuid",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD" (optional),
            "purpose": "string",
            "notes": "string" (optional)
        }
        """
        license_obj = self.get_object()
        
        # Validate license availability
        if not license_obj.can_assign():
            if license_obj.is_expired:
                return Response(
                    {'error': '期限切れのライセンスは割り当てできません。'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': f'利用可能なライセンス数が不足しています。利用可能: {license_obj.available_count}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get employee
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response(
                {'error': '社員IDが必要です。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if employee is active
        if not employee.is_active:
            return Response(
                {'error': '非アクティブな社員にはライセンスを割り当てできません。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing active assignment
        existing_assignment = LicenseAssignment.objects.filter(
            license=license_obj,
            employee=employee,
            status='ACTIVE'
        ).first()
        
        if existing_assignment:
            return Response(
                {'error': 'この社員には既に同じライセンスが割り当てられています。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create assignment
        assignment_data = {
            'license': license_obj.id,
            'employee': employee.id,
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'purpose': request.data.get('purpose', ''),
            'notes': request.data.get('notes', '')
        }
        
        serializer = LicenseAssignmentCreateSerializer(
            data=assignment_data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                assignment = serializer.save()
                return Response(
                    LicenseAssignmentSerializer(assignment, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke license assignment from an employee.
        
        Expected payload:
        {
            "employee_id": "uuid",
            "notes": "string" (optional)
        }
        """
        license_obj = self.get_object()
        
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response(
                {'error': '社員IDが必要です。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find active assignment
        assignment = LicenseAssignment.objects.filter(
            license=license_obj,
            employee=employee,
            status='ACTIVE'
        ).first()
        
        if not assignment:
            return Response(
                {'error': 'アクティブなライセンス割当が見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Revoke assignment
        try:
            with transaction.atomic():
                assignment.revoke(
                    revoked_by=request.user,
                    notes=request.data.get('notes')
                )
                return Response(
                    LicenseAssignmentSerializer(assignment, context={'request': request}).data,
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get all assignments for a specific license."""
        license_obj = self.get_object()
        assignments = license_obj.assignments.all().order_by('-assigned_date')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        
        serializer = LicenseAssignmentSerializer(
            assignments, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def usage_stats(self, request):
        """
        Get comprehensive license usage statistics and alerts.
        
        Returns:
        - Total license counts by status
        - Cost analysis
        - Expiring licenses alert
        - Over-utilized licenses alert
        """
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=30)
        
        # Basic statistics
        total_licenses = License.objects.count()
        active_licenses = License.objects.filter(expiry_date__gte=today).count()
        expired_licenses = License.objects.filter(expiry_date__lt=today).count()
        expiring_soon_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).count()
        fully_utilized_licenses = License.objects.filter(available_count=0).count()
        
        # Cost calculations
        licenses_with_costs = License.objects.annotate(
            monthly_cost=Case(
                When(pricing_model='MONTHLY', then=F('unit_price') * (F('total_count') - F('available_count'))),
                When(pricing_model='YEARLY', then=(F('unit_price') * (F('total_count') - F('available_count'))) / 12),
                default=0,
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            yearly_cost=Case(
                When(pricing_model='MONTHLY', then=F('unit_price') * (F('total_count') - F('available_count')) * 12),
                When(pricing_model='YEARLY', then=F('unit_price') * (F('total_count') - F('available_count'))),
                default=0,
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        
        total_monthly_cost = licenses_with_costs.aggregate(
            total=Sum('monthly_cost')
        )['total'] or Decimal('0.00')
        
        total_yearly_cost = licenses_with_costs.aggregate(
            total=Sum('yearly_cost')
        )['total'] or Decimal('0.00')
        
        # Alert data
        expiring_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).order_by('expiry_date')
        
        over_utilized_licenses = License.objects.filter(available_count=0)
        
        stats_data = {
            'total_licenses': total_licenses,
            'active_licenses': active_licenses,
            'expired_licenses': expired_licenses,
            'expiring_soon_licenses': expiring_soon_licenses,
            'fully_utilized_licenses': fully_utilized_licenses,
            'total_monthly_cost': total_monthly_cost,
            'total_yearly_cost': total_yearly_cost,
            'expiring_licenses': LicenseListSerializer(expiring_licenses, many=True).data,
            'over_utilized_licenses': LicenseListSerializer(over_utilized_licenses, many=True).data
        }
        
        return Response(stats_data)
    
    @action(detail=False, methods=['get'])
    def cost_analysis(self, request):
        """
        Get detailed cost analysis by software, department, etc.
        
        Query parameters:
        - group_by: 'software' (default), 'department', 'license_type'
        - department: Filter by specific department
        """
        group_by = request.query_params.get('group_by', 'software')
        department_filter = request.query_params.get('department')
        
        # Base queryset with cost calculations
        queryset = License.objects.annotate(
            used_licenses=F('total_count') - F('available_count'),
            monthly_cost=Case(
                When(pricing_model='MONTHLY', then=F('unit_price') * (F('total_count') - F('available_count'))),
                When(pricing_model='YEARLY', then=(F('unit_price') * (F('total_count') - F('available_count'))) / 12),
                default=0,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            yearly_cost=Case(
                When(pricing_model='MONTHLY', then=F('unit_price') * (F('total_count') - F('available_count')) * 12),
                When(pricing_model='YEARLY', then=F('unit_price') * (F('total_count') - F('available_count'))),
                default=0,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        
        if group_by == 'department':
            # Group by department through assignments
            analysis_data = []
            departments = Employee.objects.values_list('department', flat=True).distinct()
            
            for dept in departments:
                if department_filter and dept != department_filter:
                    continue
                
                # Get licenses used by this department
                dept_licenses = queryset.filter(
                    assignments__employee__department=dept,
                    assignments__status='ACTIVE'
                ).distinct()
                
                dept_stats = {
                    'department': dept,
                    'software_name': f'{dept} 部署',
                    'license_type': '部署別集計',
                    'total_licenses': dept_licenses.aggregate(Sum('total_count'))['total_count__sum'] or 0,
                    'used_licenses': dept_licenses.aggregate(Sum('used_licenses'))['used_licenses__sum'] or 0,
                    'monthly_cost': dept_licenses.aggregate(Sum('monthly_cost'))['monthly_cost__sum'] or Decimal('0.00'),
                    'yearly_cost': dept_licenses.aggregate(Sum('yearly_cost'))['yearly_cost__sum'] or Decimal('0.00'),
                    'usage_percentage': 0.0
                }
                
                if dept_stats['total_licenses'] > 0:
                    dept_stats['usage_percentage'] = (dept_stats['used_licenses'] / dept_stats['total_licenses']) * 100
                
                analysis_data.append(dept_stats)
        
        elif group_by == 'license_type':
            # Group by license type
            analysis_data = []
            license_types = queryset.values_list('license_type', flat=True).distinct()
            
            for lt in license_types:
                type_licenses = queryset.filter(license_type=lt)
                
                type_stats = {
                    'software_name': f'{lt} ライセンス',
                    'license_type': lt,
                    'total_licenses': type_licenses.aggregate(Sum('total_count'))['total_count__sum'] or 0,
                    'used_licenses': type_licenses.aggregate(Sum('used_licenses'))['used_licenses__sum'] or 0,
                    'monthly_cost': type_licenses.aggregate(Sum('monthly_cost'))['monthly_cost__sum'] or Decimal('0.00'),
                    'yearly_cost': type_licenses.aggregate(Sum('yearly_cost'))['yearly_cost__sum'] or Decimal('0.00'),
                    'usage_percentage': 0.0
                }
                
                if type_stats['total_licenses'] > 0:
                    type_stats['usage_percentage'] = (type_stats['used_licenses'] / type_stats['total_licenses']) * 100
                
                analysis_data.append(type_stats)
        
        else:  # group_by == 'software' (default)
            # Group by individual software
            analysis_data = []
            for license_obj in queryset:
                license_stats = {
                    'software_name': license_obj.software_name,
                    'license_type': license_obj.license_type,
                    'total_licenses': license_obj.total_count,
                    'used_licenses': license_obj.used_licenses,
                    'monthly_cost': license_obj.monthly_cost,
                    'yearly_cost': license_obj.yearly_cost,
                    'usage_percentage': float(license_obj.usage_percentage)
                }
                analysis_data.append(license_stats)
        
        return Response(analysis_data)
    
    @action(detail=False, methods=['get'])
    def expiring_alerts(self, request):
        """
        Get licenses that are expiring within specified days (default: 30).
        
        Query parameters:
        - days: Number of days to look ahead (default: 30)
        """
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days)
        
        expiring_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).order_by('expiry_date')
        
        serializer = LicenseListSerializer(expiring_licenses, many=True)
        return Response({
            'days_ahead': days,
            'count': expiring_licenses.count(),
            'licenses': serializer.data
        })


class LicenseAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing license assignments.
    
    Provides:
    - CRUD operations for license assignments
    - Filtering by license, employee, status, etc.
    - Bulk operations for assignments
    """
    
    queryset = LicenseAssignment.objects.all()
    serializer_class = LicenseAssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return LicenseAssignmentCreateSerializer
        return LicenseAssignmentSerializer
    
    def get_queryset(self):
        """
        Filter assignments based on query parameters.
        
        Supported filters:
        - license: Filter by license ID
        - employee: Filter by employee ID
        - status: Filter by assignment status
        - department: Filter by employee department
        - expiring_soon: Show assignments expiring within 30 days
        """
        queryset = LicenseAssignment.objects.select_related(
            'license', 'employee', 'assigned_by'
        ).all()
        
        # Filter by license
        license_id = self.request.query_params.get('license')
        if license_id:
            queryset = queryset.filter(license_id=license_id)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(employee__department__icontains=department)
        
        # Filter expiring soon
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon and expiring_soon.lower() == 'true':
            expiry_threshold = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                end_date__lte=expiry_threshold,
                end_date__gte=timezone.now().date(),
                status='ACTIVE'
            )
        
        return queryset.order_by('-assigned_date')
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke a specific license assignment.
        
        Expected payload:
        {
            "notes": "string" (optional)
        }
        """
        assignment = self.get_object()
        
        if assignment.status != 'ACTIVE':
            return Response(
                {'error': 'アクティブでない割当は取り消しできません。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                assignment.revoke(
                    revoked_by=request.user,
                    notes=request.data.get('notes')
                )
                serializer = self.get_serializer(assignment)
                return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get assignments for the current user (if they have an employee profile)."""
        try:
            employee = request.user.employee_profile
            assignments = self.get_queryset().filter(employee=employee)
            serializer = self.get_serializer(assignments, many=True)
            return Response(serializer.data)
        except AttributeError:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
