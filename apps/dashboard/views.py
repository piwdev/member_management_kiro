"""
Dashboard views for employee resource management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from datetime import timedelta

from .models import ResourceRequest, ReturnRequest, Notification
from .serializers import (
    ResourceRequestSerializer, ResourceRequestCreateSerializer,
    ReturnRequestSerializer, ReturnRequestCreateSerializer,
    EmployeeResourceSummarySerializer, ResourceRequestApprovalSerializer,
    ResourceRequestFulfillmentSerializer, NotificationSerializer
)
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment
from apps.employees.models import Employee
from common.permissions import IsAdminOrReadOnly


class EmployeeDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for employee dashboard functionality.
    
    Provides endpoints for employees to:
    - View their assigned resources
    - Request new resources
    - Request resource returns
    - View their request history
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_employee(self):
        """Get current user's employee profile."""
        try:
            return self.request.user.employee_profile
        except AttributeError:
            return None
    
    @action(detail=False, methods=['get'])
    def my_resources(self, request):
        """
        Get current employee's assigned resources summary.
        
        Returns:
        - Active device assignments
        - Active license assignments
        - Pending requests
        - Alerts (expiring licenses, overdue devices)
        """
        employee = self.get_employee()
        if not employee:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get active device assignments
        active_device_assignments = DeviceAssignment.objects.filter(
            employee=employee,
            status='ACTIVE'
        ).select_related('device')
        
        # Get active license assignments
        active_license_assignments = LicenseAssignment.objects.filter(
            employee=employee,
            status='ACTIVE'
        ).select_related('license')
        
        # Get pending requests
        pending_resource_requests = ResourceRequest.objects.filter(
            employee=employee,
            status__in=['PENDING', 'APPROVED']
        ).order_by('-created_at')
        
        pending_return_requests = ReturnRequest.objects.filter(
            employee=employee,
            status__in=['PENDING', 'APPROVED']
        ).order_by('-created_at')
        
        # Check for alerts
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=30)
        
        # Expiring licenses (license itself expiring)
        expiring_licenses = []
        for assignment in active_license_assignments:
            if assignment.license.is_expiring_soon(days=30):
                expiring_licenses.append({
                    'assignment_id': assignment.id,
                    'software_name': assignment.license.software_name,
                    'license_expiry_date': assignment.license.expiry_date,
                    'days_until_license_expiry': (assignment.license.expiry_date - today).days,
                    'alert_type': 'license_expiry'
                })
        
        # Expiring assignments (assignment end date approaching)
        for assignment in active_license_assignments:
            if assignment.end_date and assignment.end_date <= expiry_threshold and assignment.end_date >= today:
                expiring_licenses.append({
                    'assignment_id': assignment.id,
                    'software_name': assignment.license.software_name,
                    'assignment_end_date': assignment.end_date,
                    'days_until_assignment_end': (assignment.end_date - today).days,
                    'alert_type': 'assignment_expiry'
                })
        
        # Overdue devices
        overdue_devices = []
        for assignment in active_device_assignments:
            if assignment.is_overdue:
                overdue_devices.append({
                    'assignment_id': assignment.id,
                    'device_name': str(assignment.device),
                    'expected_return_date': assignment.expected_return_date,
                    'days_overdue': (today - assignment.expected_return_date).days
                })
        
        # Prepare summary data
        summary_data = {
            'active_device_assignments': active_device_assignments,
            'device_count': active_device_assignments.count(),
            'active_license_assignments': active_license_assignments,
            'license_count': active_license_assignments.count(),
            'pending_resource_requests': pending_resource_requests,
            'pending_return_requests': pending_return_requests,
            'expiring_licenses': expiring_licenses,
            'overdue_devices': overdue_devices,
            'total_active_resources': active_device_assignments.count() + active_license_assignments.count(),
            'pending_requests_count': pending_resource_requests.count() + pending_return_requests.count(),
            'alerts_count': len(expiring_licenses) + len(overdue_devices)
        }
        
        serializer = EmployeeResourceSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_device_assignments(self, request):
        """Get current employee's device assignments."""
        employee = self.get_employee()
        if not employee:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filter by status if provided
        status_filter = request.query_params.get('status', 'ACTIVE')
        
        assignments = DeviceAssignment.objects.filter(
            employee=employee
        ).select_related('device')
        
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        
        assignments = assignments.order_by('-assigned_date')
        
        from apps.devices.serializers import DeviceAssignmentSerializer
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_license_assignments(self, request):
        """Get current employee's license assignments."""
        employee = self.get_employee()
        if not employee:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filter by status if provided
        status_filter = request.query_params.get('status', 'ACTIVE')
        
        assignments = LicenseAssignment.objects.filter(
            employee=employee
        ).select_related('license')
        
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        
        assignments = assignments.order_by('-assigned_date')
        
        from apps.licenses.serializers import LicenseAssignmentSerializer
        serializer = LicenseAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_resources(self, request):
        """
        Get available resources that the employee can request.
        
        Query parameters:
        - type: 'device' or 'license'
        """
        resource_type = request.query_params.get('type')
        
        if resource_type == 'device':
            # Get available devices
            devices = Device.objects.filter(status='AVAILABLE').order_by('type', 'manufacturer', 'model')
            from apps.devices.serializers import DeviceListSerializer
            serializer = DeviceListSerializer(devices, many=True)
            return Response(serializer.data)
        
        elif resource_type == 'license':
            # Get licenses with available count > 0 and not expired
            today = timezone.now().date()
            licenses = License.objects.filter(
                available_count__gt=0,
                expiry_date__gte=today
            ).order_by('software_name', 'license_type')
            from apps.licenses.serializers import LicenseListSerializer
            serializer = LicenseListSerializer(licenses, many=True)
            return Response(serializer.data)
        
        else:
            return Response(
                {'error': 'type パラメータは "device" または "license" である必要があります。'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def license_alerts(self, request):
        """
        Get license expiry alerts for the current employee.
        
        Query parameters:
        - days: Number of days ahead to check (default: 30)
        """
        employee = self.get_employee()
        if not employee:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        days_ahead = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days_ahead)
        
        # Get active license assignments for this employee
        active_assignments = LicenseAssignment.objects.filter(
            employee=employee,
            status='ACTIVE'
        ).select_related('license')
        
        alerts = []
        
        # Check for license expiry alerts
        for assignment in active_assignments:
            license_obj = assignment.license
            
            # License itself expiring
            if license_obj.expiry_date <= expiry_threshold and license_obj.expiry_date >= today:
                alerts.append({
                    'alert_type': 'license_expiry',
                    'assignment_id': assignment.id,
                    'software_name': license_obj.software_name,
                    'license_type': license_obj.license_type,
                    'expiry_date': license_obj.expiry_date,
                    'days_until_expiry': (license_obj.expiry_date - today).days,
                    'severity': 'high' if (license_obj.expiry_date - today).days <= 7 else 'medium',
                    'message': f'{license_obj.software_name}のライセンスが{(license_obj.expiry_date - today).days}日後に期限切れになります。'
                })
            
            # Assignment end date approaching
            if (assignment.end_date and 
                assignment.end_date <= expiry_threshold and 
                assignment.end_date >= today):
                alerts.append({
                    'alert_type': 'assignment_expiry',
                    'assignment_id': assignment.id,
                    'software_name': license_obj.software_name,
                    'license_type': license_obj.license_type,
                    'end_date': assignment.end_date,
                    'days_until_end': (assignment.end_date - today).days,
                    'severity': 'medium' if (assignment.end_date - today).days <= 7 else 'low',
                    'message': f'{license_obj.software_name}の利用期間が{(assignment.end_date - today).days}日後に終了します。'
                })
        
        # Sort alerts by urgency (days until expiry)
        alerts.sort(key=lambda x: x.get('days_until_expiry', x.get('days_until_end', 999)))
        
        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'days_ahead': days_ahead,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def admin_license_alerts(self, request):
        """
        Get system-wide license expiry alerts (admin only).
        
        Query parameters:
        - days: Number of days ahead to check (default: 30)
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'この機能には管理者権限が必要です。'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days_ahead = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days_ahead)
        
        alerts = []
        
        # Check for licenses expiring
        expiring_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).order_by('expiry_date')
        
        for license_obj in expiring_licenses:
            active_assignments_count = license_obj.assignments.filter(status='ACTIVE').count()
            days_until_expiry = (license_obj.expiry_date - today).days
            
            alerts.append({
                'alert_type': 'license_expiry',
                'license_id': license_obj.id,
                'software_name': license_obj.software_name,
                'license_type': license_obj.license_type,
                'expiry_date': license_obj.expiry_date,
                'days_until_expiry': days_until_expiry,
                'active_assignments': active_assignments_count,
                'total_licenses': license_obj.total_count,
                'severity': 'critical' if days_until_expiry <= 7 else 'high' if days_until_expiry <= 14 else 'medium',
                'message': f'{license_obj.software_name} ({license_obj.license_type}) が{days_until_expiry}日後に期限切れ - {active_assignments_count}件の割当に影響'
            })
        
        # Check for assignments expiring
        expiring_assignments = LicenseAssignment.objects.filter(
            status='ACTIVE',
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=expiry_threshold
        ).select_related('license', 'employee').order_by('end_date')
        
        for assignment in expiring_assignments:
            days_until_end = (assignment.end_date - today).days
            
            alerts.append({
                'alert_type': 'assignment_expiry',
                'assignment_id': assignment.id,
                'employee_name': assignment.employee.name,
                'employee_id': assignment.employee.employee_id,
                'department': assignment.employee.department,
                'software_name': assignment.license.software_name,
                'license_type': assignment.license.license_type,
                'end_date': assignment.end_date,
                'days_until_end': days_until_end,
                'severity': 'medium' if days_until_end <= 7 else 'low',
                'message': f'{assignment.employee.name}の{assignment.license.software_name}利用が{days_until_end}日後に終了'
            })
        
        # Sort alerts by severity and urgency
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        alerts.sort(key=lambda x: (
            severity_order.get(x['severity'], 4),
            x.get('days_until_expiry', x.get('days_until_end', 999))
        ))
        
        # Group alerts by severity
        alerts_by_severity = {
            'critical': [a for a in alerts if a['severity'] == 'critical'],
            'high': [a for a in alerts if a['severity'] == 'high'],
            'medium': [a for a in alerts if a['severity'] == 'medium'],
            'low': [a for a in alerts if a['severity'] == 'low']
        }
        
        return Response({
            'alerts': alerts,
            'alerts_by_severity': alerts_by_severity,
            'summary': {
                'total_alerts': len(alerts),
                'critical': len(alerts_by_severity['critical']),
                'high': len(alerts_by_severity['high']),
                'medium': len(alerts_by_severity['medium']),
                'low': len(alerts_by_severity['low'])
            },
            'days_ahead': days_ahead,
            'generated_at': timezone.now()
        })


class ResourceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing resource requests.
    
    Employees can create and view their own requests.
    Admins can view all requests and approve/reject them.
    """
    
    queryset = ResourceRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ResourceRequestCreateSerializer
        return ResourceRequestSerializer
    
    def get_queryset(self):
        """Filter requests based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own requests
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.employee_profile
                queryset = queryset.filter(employee=employee)
            except AttributeError:
                # User has no employee profile, return empty queryset
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by request type if provided
        request_type = self.request.query_params.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create resource request for current user."""
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override create to return full serializer data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Return full object data using the detail serializer
        response_serializer = ResourceRequestSerializer(instance, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_reject(self, request, pk=None):
        """
        Approve or reject a resource request (admin only).
        
        Expected payload:
        {
            "action": "approve" | "reject",
            "notes": "optional notes",
            "rejection_reason": "required for reject"
        }
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'この操作には管理者権限が必要です。'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resource_request = self.get_object()
        serializer = ResourceRequestApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            
            try:
                if action == 'approve':
                    resource_request.approve(
                        approved_by=request.user,
                        notes=notes
                    )
                    message = 'リソース申請を承認しました。'
                else:  # reject
                    rejection_reason = serializer.validated_data['rejection_reason']
                    resource_request.reject(
                        rejected_by=request.user,
                        reason=rejection_reason
                    )
                    message = 'リソース申請を却下しました。'
                
                response_serializer = ResourceRequestSerializer(resource_request)
                return Response({
                    'message': message,
                    'request': response_serializer.data
                })
                
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def fulfill(self, request, pk=None):
        """
        Fulfill an approved resource request (admin only).
        
        Expected payload:
        {
            "device_id": "uuid" (for device requests),
            "license_id": "uuid" (for license requests),
            "notes": "optional notes"
        }
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'この操作には管理者権限が必要です。'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resource_request = self.get_object()
        
        if resource_request.status != 'APPROVED':
            return Response(
                {'error': '承認済みのリクエストのみ完了できます。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ResourceRequestFulfillmentSerializer(data=request.data)
        
        if serializer.is_valid():
            device_id = serializer.validated_data.get('device_id')
            license_id = serializer.validated_data.get('license_id')
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    device = None
                    license_obj = None
                    
                    if device_id:
                        device = get_object_or_404(Device, id=device_id)
                        if not device.is_available:
                            return Response(
                                {'error': '指定された端末は利用できません。'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Assign device to employee
                        device.assign_to_employee(
                            employee=resource_request.employee,
                            assigned_date=timezone.now().date(),
                            return_date=resource_request.expected_end_date,
                            purpose=resource_request.purpose,
                            assigned_by=request.user
                        )
                    
                    if license_id:
                        license_obj = get_object_or_404(License, id=license_id)
                        if not license_obj.can_assign():
                            return Response(
                                {'error': '指定されたライセンスは利用できません。'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Create license assignment
                        LicenseAssignment.objects.create(
                            license=license_obj,
                            employee=resource_request.employee,
                            start_date=resource_request.expected_start_date,
                            end_date=resource_request.expected_end_date,
                            purpose=resource_request.purpose,
                            assigned_by=request.user
                        )
                    
                    # Mark request as fulfilled
                    resource_request.fulfill(
                        fulfilled_by=request.user,
                        device=device,
                        license_obj=license_obj,
                        notes=notes
                    )
                    
                    response_serializer = ResourceRequestSerializer(resource_request)
                    return Response({
                        'message': 'リソース申請を完了しました。',
                        'request': response_serializer.data
                    })
                    
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a resource request (employee can cancel their own pending requests)."""
        resource_request = self.get_object()
        
        # Check permissions
        if not request.user.is_staff:
            try:
                employee = request.user.employee_profile
                if resource_request.employee != employee:
                    return Response(
                        {'error': '他の社員のリクエストはキャンセルできません。'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            reason = request.data.get('reason', '')
            resource_request.cancel(cancelled_by=request.user, reason=reason)
            
            response_serializer = ResourceRequestSerializer(resource_request)
            return Response({
                'message': 'リソース申請をキャンセルしました。',
                'request': response_serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing return requests.
    
    Employees can create return requests for their assigned resources.
    Admins can process and complete return requests.
    """
    
    queryset = ReturnRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ReturnRequestCreateSerializer
        return ReturnRequestSerializer
    
    def get_queryset(self):
        """Filter return requests based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own requests
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.employee_profile
                queryset = queryset.filter(employee=employee)
            except AttributeError:
                # User has no employee profile, return empty queryset
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by request type if provided
        request_type = self.request.query_params.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Override create to return full serializer data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Return full object data using the detail serializer
        response_serializer = ReturnRequestSerializer(instance, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """
        Complete a return request (admin only).
        
        Expected payload:
        {
            "actual_return_date": "YYYY-MM-DD" (optional, defaults to today),
            "notes": "optional completion notes"
        }
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'この操作には管理者権限が必要です。'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return_request = self.get_object()
        
        try:
            actual_return_date = request.data.get('actual_return_date')
            if actual_return_date:
                from datetime import datetime
                actual_return_date = datetime.strptime(actual_return_date, '%Y-%m-%d').date()
            
            notes = request.data.get('notes', '')
            
            return_request.complete(
                completed_by=request.user,
                actual_return_date=actual_return_date,
                notes=notes
            )
            
            response_serializer = ReturnRequestSerializer(return_request)
            return Response({
                'message': '返却申請を完了しました。',
                'request': response_serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a return request (employee can cancel their own pending requests)."""
        return_request = self.get_object()
        
        # Check permissions
        if not request.user.is_staff:
            try:
                employee = request.user.employee_profile
                if return_request.employee != employee:
                    return Response(
                        {'error': '他の社員のリクエストはキャンセルできません。'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            reason = request.data.get('reason', '')
            return_request.cancel(cancelled_by=request.user, reason=reason)
            
            response_serializer = ReturnRequestSerializer(return_request)
            return Response({
                'message': '返却申請をキャンセルしました。',
                'request': response_serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    
    Employees can view their own notifications and mark them as read/dismissed.
    Admins can view all notifications.
    """
    
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own notifications
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.employee_profile
                queryset = queryset.filter(employee=employee)
            except AttributeError:
                # User has no employee profile, return empty queryset
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by priority if provided
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter unread notifications
        unread_only = self.request.query_params.get('unread_only')
        if unread_only and unread_only.lower() == 'true':
            queryset = queryset.filter(status='SENT')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        
        # Check permissions
        if not request.user.is_staff:
            try:
                employee = request.user.employee_profile
                if notification.employee != employee:
                    return Response(
                        {'error': '他の社員の通知は操作できません。'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss notification."""
        notification = self.get_object()
        
        # Check permissions
        if not request.user.is_staff:
            try:
                employee = request.user.employee_profile
                if notification.employee != employee:
                    return Response(
                        {'error': '他の社員の通知は操作できません。'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        notification.dismiss()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all unread notifications as read for the current user."""
        try:
            employee = request.user.employee_profile
        except AttributeError:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        unread_notifications = Notification.objects.filter(
            employee=employee,
            status='SENT'
        )
        
        count = 0
        for notification in unread_notifications:
            notification.mark_as_read()
            count += 1
        
        return Response({
            'message': f'{count}件の通知を既読にしました。',
            'marked_count': count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for the current user."""
        try:
            employee = request.user.employee_profile
        except AttributeError:
            return Response(
                {'error': 'ユーザーに社員プロファイルが関連付けられていません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        unread_count = Notification.objects.filter(
            employee=employee,
            status='SENT'
        ).count()
        
        return Response({
            'unread_count': unread_count
        })