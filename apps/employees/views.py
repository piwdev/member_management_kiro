"""
Employee management API views.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from common.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from common.pagination import StandardResultsSetPagination
from .models import Employee, EmployeeHistory
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer,
    EmployeeCreateSerializer, EmployeeUpdateSerializer,
    EmployeeTerminationSerializer, EmployeeHistorySerializer
)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees.
    
    Provides CRUD operations for employee records with proper permissions
    and history tracking.
    """
    
    queryset = Employee.objects.select_related('user', 'created_by', 'updated_by').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    
    # Search fields
    search_fields = ['name', 'name_kana', 'employee_id', 'email', 'department', 'position']
    
    # Ordering options
    ordering_fields = ['employee_id', 'name', 'department', 'position', 'hire_date', 'created_at']
    ordering = ['employee_id']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        elif self.action == 'terminate':
            return EmployeeTerminationSerializer
        else:
            return EmployeeDetailSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        """
        queryset = super().get_queryset()
        
        # Non-admin users can only see active employees
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='ACTIVE')
        
        # Manual filtering based on query parameters
        # Department filter
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        # Position filter
        position = self.request.query_params.get('position', None)
        if position:
            queryset = queryset.filter(position__icontains=position)
        
        # Location filter
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location=location)
        
        # Status filter
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Active only filter
        active_only = self.request.query_params.get('active_only', None)
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(
                status='ACTIVE',
                termination_date__isnull=True
            )
        
        # Hire date filters
        hire_date_from = self.request.query_params.get('hire_date_from', None)
        if hire_date_from:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(hire_date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(hire_date__gte=date_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        hire_date_to = self.request.query_params.get('hire_date_to', None)
        if hire_date_to:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(hire_date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(hire_date__lte=date_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Filter by department if user is not admin (optional business rule)
        if not self.request.user.is_staff and hasattr(self.request.user, 'employee_profile'):
            user_department = self.request.user.employee_profile.department
            department_filter = self.request.query_params.get('department_filter', None)
            if department_filter and department_filter.lower() == 'same':
                queryset = queryset.filter(department=user_department)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating employee."""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating employee."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def terminate(self, request, pk=None):
        """
        Terminate an employee and mark resources for recovery.
        
        This action handles the business logic for employee termination
        including resource recovery marking.
        """
        employee = self.get_object()
        
        # Check if employee is already terminated
        if employee.status == 'INACTIVE':
            return Response(
                {'error': 'この社員は既に退職処理済みです。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            terminated_employee = serializer.save(employee)
            
            # TODO: Mark resources for recovery (will be implemented in device/license tasks)
            # This is where we would trigger resource recovery processes
            
            return Response(
                {
                    'message': '退職処理が完了しました。',
                    'employee': EmployeeDetailSerializer(terminated_employee).data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reactivate(self, request, pk=None):
        """
        Reactivate a terminated employee.
        """
        employee = self.get_object()
        
        # Check if employee is terminated
        if employee.status != 'INACTIVE':
            return Response(
                {'error': 'この社員は退職していません。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reactivate employment
        employee.reactivate_employment(reactivated_by=request.user)
        
        return Response(
            {
                'message': '雇用が再開されました。',
                'employee': EmployeeDetailSerializer(employee).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get employee change history.
        """
        employee = self.get_object()
        history_records = employee.history_records.all()
        
        # Apply pagination to history records
        page = self.paginate_queryset(history_records)
        if page is not None:
            serializer = EmployeeHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EmployeeHistorySerializer(history_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get employee statistics for dashboard.
        """
        # Only allow admin users to access statistics
        if not request.user.is_staff:
            return Response(
                {'error': '統計情報へのアクセス権限がありません。'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_employees = queryset.count()
        active_employees = queryset.filter(status='ACTIVE').count()
        inactive_employees = queryset.filter(status='INACTIVE').count()
        
        # Department breakdown
        department_stats = {}
        departments = queryset.values_list('department', flat=True).distinct()
        for dept in departments:
            dept_count = queryset.filter(department=dept).count()
            active_count = queryset.filter(department=dept, status='ACTIVE').count()
            department_stats[dept] = {
                'total': dept_count,
                'active': active_count,
                'inactive': dept_count - active_count
            }
        
        # Location breakdown
        location_stats = {}
        for location_code, location_name in Employee.LOCATION_CHOICES:
            loc_count = queryset.filter(location=location_code).count()
            active_count = queryset.filter(location=location_code, status='ACTIVE').count()
            location_stats[location_code] = {
                'name': location_name,
                'total': loc_count,
                'active': active_count,
                'inactive': loc_count - active_count
            }
        
        # Recent hires (last 30 days)
        thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
        recent_hires = queryset.filter(hire_date__gte=thirty_days_ago).count()
        
        # Recent terminations (last 30 days)
        recent_terminations = queryset.filter(
            termination_date__gte=thirty_days_ago,
            termination_date__isnull=False
        ).count()
        
        return Response({
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'department_breakdown': department_stats,
            'location_breakdown': location_stats,
            'recent_hires': recent_hires,
            'recent_terminations': recent_terminations,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Get current user's employee profile.
        """
        try:
            employee = request.user.employee_profile
            serializer = EmployeeDetailSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'ユーザーに関連する社員プロファイルが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """
        Get search suggestions for employee search.
        """
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        # Search in various fields and return suggestions
        employees = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(name_kana__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(email__icontains=query) |
            Q(department__icontains=query)
        )[:10]  # Limit to 10 suggestions
        
        suggestions = []
        for emp in employees:
            suggestions.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'name': emp.name,
                'department': emp.department,
                'position': emp.position,
                'email': emp.email
            })
        
        return Response({'suggestions': suggestions})


class EmployeeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing employee history records.
    Read-only access for audit purposes.
    """
    
    queryset = EmployeeHistory.objects.select_related('employee', 'changed_by').all()
    serializer_class = EmployeeHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    
    # Ordering options
    ordering_fields = ['changed_at', 'change_type']
    ordering = ['-changed_at']
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        """
        queryset = super().get_queryset()
        
        # Non-admin users can only see history for employees in their department
        if not self.request.user.is_staff:
            if hasattr(self.request.user, 'employee_profile'):
                user_department = self.request.user.employee_profile.department
                queryset = queryset.filter(employee__department=user_department)
            else:
                # If user has no employee profile, they can't see any history
                queryset = queryset.none()
        
        # Manual filtering based on query parameters
        # Employee filter
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee__id=employee_id)
        
        # Change type filter
        change_type = self.request.query_params.get('change_type', None)
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        
        # Changed by filter
        changed_by = self.request.query_params.get('changed_by', None)
        if changed_by:
            queryset = queryset.filter(changed_by__id=changed_by)
        
        # Date range filters
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(changed_at__date__gte=date_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(changed_at__date__lte=date_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        return queryset
