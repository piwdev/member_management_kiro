"""
Views for permission management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import PermissionPolicy, PermissionOverride, PermissionAuditLog
from .serializers import (
    PermissionPolicySerializer, PermissionOverrideSerializer, 
    PermissionAuditLogSerializer, EmployeePermissionSummarySerializer
)
from .services import PermissionService
from apps.employees.models import Employee
from common.permissions import IsAdminOrReadOnly


class PermissionPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing permission policies.
    """
    
    queryset = PermissionPolicy.objects.all()
    serializer_class = PermissionPolicySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'target_department', 'target_position']
    ordering_fields = ['name', 'priority', 'created_at', 'updated_at']
    ordering = ['priority', 'name']
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by effectiveness
        effective_only = self.request.query_params.get('effective_only')
        if effective_only and effective_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                is_active=True,
                effective_from__lte=today
            ).filter(
                Q(effective_until__isnull=True) | Q(effective_until__gte=today)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a permission policy."""
        policy = self.get_object()
        policy.is_active = True
        policy.updated_by = request.user
        policy.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        
        return Response({'status': 'ポリシーが有効化されました'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a permission policy."""
        policy = self.get_object()
        policy.is_active = False
        policy.updated_by = request.user
        policy.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        
        return Response({'status': 'ポリシーが無効化されました'})
    
    @action(detail=False, methods=['get'])
    def applicable_to_employee(self, request):
        """Get policies applicable to a specific employee."""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        policies = PermissionService.get_applicable_policies(employee)
        serializer = self.get_serializer(policies, many=True)
        
        return Response(serializer.data)


class PermissionOverrideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing permission overrides.
    """
    
    queryset = PermissionOverride.objects.all()
    serializer_class = PermissionOverrideSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'employee__name', 'employee__employee_id', 'resource_identifier', 'reason'
    ]
    ordering_fields = ['effective_from', 'effective_until', 'created_at']
    ordering = ['-effective_from']
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by effectiveness
        effective_only = self.request.query_params.get('effective_only')
        if effective_only and effective_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                is_active=True,
                effective_from__lte=today,
                effective_until__gte=today
            )
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee__employee_id=employee_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a permission override."""
        override = self.get_object()
        override.is_active = True
        override.save(update_fields=['is_active', 'updated_at'])
        
        return Response({'status': 'オーバーライドが有効化されました'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a permission override."""
        override = self.get_object()
        override.is_active = False
        override.save(update_fields=['is_active', 'updated_at'])
        
        return Response({'status': 'オーバーライドが無効化されました'})


class PermissionAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing permission audit logs (read-only).
    """
    
    queryset = PermissionAuditLog.objects.all()
    serializer_class = PermissionAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'employee__name', 'employee__employee_id', 'resource_identifier',
        'performed_by__username'
    ]
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee__employee_id=employee_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset


class PermissionCheckViewSet(viewsets.ViewSet):
    """
    ViewSet for permission checking operations.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def check_access(self, request):
        """
        Check if an employee can access a specific resource.
        
        Expected payload:
        {
            "employee_id": "EMP001",
            "resource_type": "DEVICE" or "SOFTWARE",
            "resource_identifier": "LAPTOP" or "Microsoft Office"
        }
        """
        employee_id = request.data.get('employee_id')
        resource_type = request.data.get('resource_type')
        resource_identifier = request.data.get('resource_identifier')
        
        if not all([employee_id, resource_type, resource_identifier]):
            return Response(
                {'error': 'employee_id, resource_type, resource_identifier が必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        can_access = PermissionService.check_resource_access_and_log(
            employee, resource_type, resource_identifier, performed_by=request.user
        )
        
        if resource_type.upper() == 'DEVICE':
            can_access, reason = PermissionService.can_access_device_type(
                employee, resource_identifier, log_check=False
            )
        elif resource_type.upper() == 'SOFTWARE':
            can_access, reason = PermissionService.can_access_software(
                employee, resource_identifier, log_check=False
            )
        else:
            return Response(
                {'error': '不明なリソース種別です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'employee_id': employee_id,
            'resource_type': resource_type,
            'resource_identifier': resource_identifier,
            'can_access': can_access,
            'reason': reason
        })
    
    @action(detail=False, methods=['get'])
    def employee_summary(self, request):
        """Get comprehensive permission summary for an employee."""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        summary = PermissionService.get_employee_permission_summary(employee)
        serializer = EmployeePermissionSummarySerializer(summary)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_check(self, request):
        """
        Bulk permission check for multiple resources.
        
        Expected payload:
        {
            "employee_id": "EMP001",
            "resources": [
                {"resource_type": "DEVICE", "resource_identifier": "LAPTOP"},
                {"resource_type": "SOFTWARE", "resource_identifier": "Microsoft Office"}
            ]
        }
        """
        employee_id = request.data.get('employee_id')
        resources = request.data.get('resources', [])
        
        if not employee_id or not resources:
            return Response(
                {'error': 'employee_id と resources が必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        results = []
        
        for resource in resources:
            resource_type = resource.get('resource_type')
            resource_identifier = resource.get('resource_identifier')
            
            if not resource_type or not resource_identifier:
                results.append({
                    'resource_type': resource_type,
                    'resource_identifier': resource_identifier,
                    'can_access': False,
                    'reason': 'リソース情報が不完全です'
                })
                continue
            
            if resource_type.upper() == 'DEVICE':
                can_access, reason = PermissionService.can_access_device_type(
                    employee, resource_identifier, log_check=False
                )
            elif resource_type.upper() == 'SOFTWARE':
                can_access, reason = PermissionService.can_access_software(
                    employee, resource_identifier, log_check=False
                )
            else:
                can_access, reason = False, '不明なリソース種別'
            
            results.append({
                'resource_type': resource_type,
                'resource_identifier': resource_identifier,
                'can_access': can_access,
                'reason': reason
            })
        
        return Response({
            'employee_id': employee_id,
            'results': results
        })
