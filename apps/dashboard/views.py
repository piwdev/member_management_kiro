"""
Dashboard views for the asset management system.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
import logging

from .models import ResourceRequest, ReturnRequest, Notification
from .serializers import (
    ResourceRequestSerializer, ResourceRequestCreateSerializer,
    ReturnRequestSerializer, ReturnRequestCreateSerializer,
    NotificationSerializer, EmployeeResourceSummarySerializer,
    ResourceRequestApprovalSerializer, ResourceRequestFulfillmentSerializer
)
from apps.devices.models import DeviceAssignment
from apps.licenses.models import LicenseAssignment

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'checks': {}
    }
    
    overall_status = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 30)
        cached_value = cache.get(cache_key)
        if cached_value == 'test':
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            raise Exception("Cache test failed")
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # Set overall status
    if not overall_status:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes deployments.
    """
    # Check if all required services are ready
    readiness_status = {
        'status': 'ready',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    overall_ready = True
    
    # Database migrations check
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            readiness_status['checks']['migrations'] = {
                'status': 'not_ready',
                'pending_migrations': len(plan)
            }
            overall_ready = False
        else:
            readiness_status['checks']['migrations'] = {'status': 'ready'}
    except Exception as e:
        readiness_status['checks']['migrations'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_ready = False
    
    # Static files check
    try:
        import os
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            readiness_status['checks']['static_files'] = {'status': 'ready'}
        else:
            readiness_status['checks']['static_files'] = {
                'status': 'not_ready',
                'error': 'Static files not collected'
            }
            overall_ready = False
    except Exception as e:
        readiness_status['checks']['static_files'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_ready = False
    
    # Set overall status
    if not overall_ready:
        readiness_status['status'] = 'not_ready'
        return Response(readiness_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(readiness_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check endpoint for Kubernetes deployments.
    """
    # Simple liveness check - just return OK if the application is running
    return Response({
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)


class EmployeeDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for employee dashboard data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeResourceSummarySerializer
    
    def get_queryset(self):
        """Return dashboard data for the current user's employee profile."""
        return None  # Not used for this viewset
    
    def list(self, request):
        """Get dashboard summary for the current employee."""
        try:
            employee = request.user.employee_profile
        except AttributeError:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active assignments
        active_device_assignments = DeviceAssignment.objects.filter(
            employee=employee,
            status='ACTIVE'
        ).select_related('device')
        
        active_license_assignments = LicenseAssignment.objects.filter(
            employee=employee,
            status='ACTIVE'
        ).select_related('license')
        
        # Get pending requests
        pending_resource_requests = ResourceRequest.objects.filter(
            employee=employee,
            status__in=['PENDING', 'APPROVED']
        )
        
        pending_return_requests = ReturnRequest.objects.filter(
            employee=employee,
            status__in=['PENDING', 'APPROVED']
        )
        
        # Prepare summary data
        dashboard_data = {
            'active_device_assignments': active_device_assignments,
            'device_count': active_device_assignments.count(),
            'active_license_assignments': active_license_assignments,
            'license_count': active_license_assignments.count(),
            'pending_resource_requests': pending_resource_requests,
            'pending_return_requests': pending_return_requests,
            'expiring_licenses': [],  # TODO: Implement expiring licenses logic
            'overdue_devices': [],    # TODO: Implement overdue devices logic
            'total_active_resources': active_device_assignments.count() + active_license_assignments.count(),
            'pending_requests_count': pending_resource_requests.count() + pending_return_requests.count(),
            'alerts_count': 0,  # TODO: Implement alerts count
        }
        
        serializer = self.get_serializer(dashboard_data)
        return Response(serializer.data)


class ResourceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for resource requests.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ResourceRequestCreateSerializer
        return ResourceRequestSerializer
    
    def get_queryset(self):
        """Return resource requests for the current user's employee profile."""
        try:
            employee = self.request.user.employee_profile
            return ResourceRequest.objects.filter(employee=employee).select_related(
                'employee', 'approved_by', 'fulfilled_by', 'fulfilled_device', 'fulfilled_license'
            )
        except AttributeError:
            return ResourceRequest.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a resource request (admin only)."""
        # TODO: Add admin permission check
        resource_request = self.get_object()
        serializer = ResourceRequestApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            
            if action == 'approve':
                resource_request.approve(request.user, notes)
                return Response({'status': 'approved'})
            elif action == 'reject':
                rejection_reason = serializer.validated_data['rejection_reason']
                resource_request.reject(request.user, rejection_reason)
                return Response({'status': 'rejected'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def fulfill(self, request, pk=None):
        """Fulfill a resource request (admin only)."""
        # TODO: Add admin permission check
        resource_request = self.get_object()
        serializer = ResourceRequestFulfillmentSerializer(data=request.data)
        
        if serializer.is_valid():
            device_id = serializer.validated_data.get('device_id')
            license_id = serializer.validated_data.get('license_id')
            notes = serializer.validated_data.get('notes', '')
            
            device = None
            license_obj = None
            
            if device_id:
                from apps.devices.models import Device
                try:
                    device = Device.objects.get(id=device_id)
                except Device.DoesNotExist:
                    return Response(
                        {'error': '指定された端末が見つかりません。'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if license_id:
                from apps.licenses.models import License
                try:
                    license_obj = License.objects.get(id=license_id)
                except License.DoesNotExist:
                    return Response(
                        {'error': '指定されたライセンスが見つかりません。'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            resource_request.fulfill(request.user, device, license_obj, notes)
            return Response({'status': 'fulfilled'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for return requests.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReturnRequestCreateSerializer
        return ReturnRequestSerializer
    
    def get_queryset(self):
        """Return return requests for the current user's employee profile."""
        try:
            employee = self.request.user.employee_profile
            return ReturnRequest.objects.filter(employee=employee).select_related(
                'employee', 'processed_by', 'device_assignment__device', 'license_assignment__license'
            )
        except AttributeError:
            return ReturnRequest.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a return request (admin only)."""
        # TODO: Add admin permission check
        return_request = self.get_object()
        notes = request.data.get('notes', '')
        
        return_request.approve(request.user, notes)
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """Complete a return request (admin only)."""
        # TODO: Add admin permission check
        return_request = self.get_object()
        actual_return_date = request.data.get('actual_return_date')
        notes = request.data.get('notes', '')
        
        return_request.complete(request.user, actual_return_date, notes)
        return Response({'status': 'completed'})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notifications.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the current user's employee profile."""
        try:
            employee = self.request.user.employee_profile
            return Notification.objects.filter(employee=employee).select_related(
                'employee', 'related_license', 'related_device', 'related_request'
            )
        except AttributeError:
            return Notification.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'read'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def dismiss(self, request, pk=None):
        """Dismiss notification."""
        notification = self.get_object()
        notification.dismiss()
        return Response({'status': 'dismissed'})