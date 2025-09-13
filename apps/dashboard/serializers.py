"""
Serializers for dashboard API.
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import ResourceRequest, ReturnRequest, Notification
from apps.employees.serializers import EmployeeListSerializer
from apps.devices.serializers import DeviceListSerializer, DeviceAssignmentSerializer
from apps.licenses.serializers import LicenseListSerializer, LicenseAssignmentSerializer
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment


class ResourceRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for resource requests.
    """
    
    employee = EmployeeListSerializer(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    fulfilled_by_name = serializers.CharField(source='fulfilled_by.get_full_name', read_only=True)
    fulfilled_device = DeviceListSerializer(read_only=True)
    fulfilled_license = LicenseListSerializer(read_only=True)
    
    # Display fields
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = ResourceRequest
        fields = [
            'id', 'request_type', 'request_type_display', 'employee',
            'device_type', 'software_name', 'specifications',
            'purpose', 'business_justification', 'expected_usage_period',
            'expected_start_date', 'expected_end_date', 'priority', 'priority_display',
            'status', 'status_display', 'approved_by_name', 'approved_at',
            'rejection_reason', 'fulfilled_device', 'fulfilled_license',
            'fulfilled_at', 'fulfilled_by_name', 'notes', 'admin_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee', 'status', 'approved_by_name', 'approved_at',
            'fulfilled_device', 'fulfilled_license', 'fulfilled_at', 
            'fulfilled_by_name', 'admin_notes', 'created_at', 'updated_at'
        ]


class ResourceRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating resource requests.
    """
    
    class Meta:
        model = ResourceRequest
        fields = [
            'request_type', 'device_type', 'software_name', 'specifications',
            'purpose', 'business_justification', 'expected_usage_period',
            'expected_start_date', 'expected_end_date', 'priority', 'notes'
        ]
    
    def validate(self, data):
        """Validate request data."""
        request_type = data.get('request_type')
        
        if request_type == 'DEVICE' and not data.get('device_type'):
            raise serializers.ValidationError({
                'device_type': '端末申請の場合、端末種別は必須です。'
            })
        
        if request_type == 'LICENSE' and not data.get('software_name'):
            raise serializers.ValidationError({
                'software_name': 'ライセンス申請の場合、ソフトウェア名は必須です。'
            })
        
        # Validate date range
        expected_start_date = data.get('expected_start_date')
        expected_end_date = data.get('expected_end_date')
        
        if expected_end_date and expected_start_date and expected_start_date > expected_end_date:
            raise serializers.ValidationError({
                'expected_end_date': '利用終了予定日は利用開始希望日より後である必要があります。'
            })
        
        # Validate start date is not in the past
        if expected_start_date and expected_start_date < timezone.now().date():
            raise serializers.ValidationError({
                'expected_start_date': '利用開始希望日は現在の日付以降である必要があります。'
            })
        
        return data
    
    def create(self, validated_data):
        """Create resource request with current user's employee profile."""
        request = self.context['request']
        
        try:
            employee = request.user.employee_profile
        except AttributeError:
            raise serializers.ValidationError(
                'ユーザーに社員プロファイルが関連付けられていません。'
            )
        
        validated_data['employee'] = employee
        return super().create(validated_data)


class ReturnRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for return requests.
    """
    
    employee = EmployeeListSerializer(read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    device_assignment = DeviceAssignmentSerializer(read_only=True)
    license_assignment = LicenseAssignmentSerializer(read_only=True)
    
    # Display fields
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'request_type', 'request_type_display', 'employee',
            'device_assignment', 'license_assignment', 'expected_return_date',
            'return_reason', 'condition_notes', 'status', 'status_display',
            'processed_by_name', 'processed_at', 'actual_return_date',
            'notes', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee', 'status', 'processed_by_name', 'processed_at',
            'actual_return_date', 'admin_notes', 'created_at', 'updated_at'
        ]


class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating return requests.
    """
    
    device_assignment_id = serializers.UUIDField(required=False, allow_null=True)
    license_assignment_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = ReturnRequest
        fields = [
            'request_type', 'device_assignment_id', 'license_assignment_id',
            'expected_return_date', 'return_reason', 'condition_notes', 'notes'
        ]
    
    def validate(self, data):
        """Validate return request data."""
        request_type = data.get('request_type')
        device_assignment_id = data.get('device_assignment_id')
        license_assignment_id = data.get('license_assignment_id')
        
        if request_type == 'DEVICE' and not device_assignment_id:
            raise serializers.ValidationError({
                'device_assignment_id': '端末返却申請の場合、端末割当IDは必須です。'
            })
        
        if request_type == 'LICENSE' and not license_assignment_id:
            raise serializers.ValidationError({
                'license_assignment_id': 'ライセンス返却申請の場合、ライセンス割当IDは必須です。'
            })
        
        # Validate expected return date is not in the past
        expected_return_date = data.get('expected_return_date')
        if expected_return_date and expected_return_date < timezone.now().date():
            raise serializers.ValidationError({
                'expected_return_date': '返却予定日は現在の日付以降である必要があります。'
            })
        
        return data
    
    def create(self, validated_data):
        """Create return request with current user's employee profile."""
        request = self.context['request']
        
        try:
            employee = request.user.employee_profile
        except AttributeError:
            raise serializers.ValidationError(
                'ユーザーに社員プロファイルが関連付けられていません。'
            )
        
        # Get assignment objects
        device_assignment_id = validated_data.pop('device_assignment_id', None)
        license_assignment_id = validated_data.pop('license_assignment_id', None)
        
        if device_assignment_id:
            try:
                device_assignment = DeviceAssignment.objects.get(
                    id=device_assignment_id,
                    employee=employee,
                    status='ACTIVE'
                )
                validated_data['device_assignment'] = device_assignment
            except DeviceAssignment.DoesNotExist:
                raise serializers.ValidationError({
                    'device_assignment_id': '指定された端末割当が見つからないか、あなたに割り当てられていません。'
                })
        
        if license_assignment_id:
            try:
                license_assignment = LicenseAssignment.objects.get(
                    id=license_assignment_id,
                    employee=employee,
                    status='ACTIVE'
                )
                validated_data['license_assignment'] = license_assignment
            except LicenseAssignment.DoesNotExist:
                raise serializers.ValidationError({
                    'license_assignment_id': '指定されたライセンス割当が見つからないか、あなたに割り当てられていません。'
                })
        
        validated_data['employee'] = employee
        return super().create(validated_data)


class EmployeeResourceSummarySerializer(serializers.Serializer):
    """
    Serializer for employee resource summary (dashboard overview).
    """
    
    # Device assignments
    active_device_assignments = DeviceAssignmentSerializer(many=True, read_only=True)
    device_count = serializers.IntegerField(read_only=True)
    
    # License assignments
    active_license_assignments = LicenseAssignmentSerializer(many=True, read_only=True)
    license_count = serializers.IntegerField(read_only=True)
    
    # Pending requests
    pending_resource_requests = ResourceRequestSerializer(many=True, read_only=True)
    pending_return_requests = ReturnRequestSerializer(many=True, read_only=True)
    
    # Alerts
    expiring_licenses = serializers.ListField(read_only=True)
    overdue_devices = serializers.ListField(read_only=True)
    
    # Summary counts
    total_active_resources = serializers.IntegerField(read_only=True)
    pending_requests_count = serializers.IntegerField(read_only=True)
    alerts_count = serializers.IntegerField(read_only=True)


class ResourceRequestApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving/rejecting resource requests.
    """
    
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate approval data."""
        action = data.get('action')
        
        if action == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': '却下の場合、却下理由は必須です。'
            })
        
        return data


class ResourceRequestFulfillmentSerializer(serializers.Serializer):
    """
    Serializer for fulfilling resource requests.
    """
    
    device_id = serializers.UUIDField(required=False, allow_null=True)
    license_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate fulfillment data."""
        device_id = data.get('device_id')
        license_id = data.get('license_id')
        
        if not device_id and not license_id:
            raise serializers.ValidationError(
                '端末IDまたはライセンスIDのいずれかは必須です。'
            )
        
        if device_id and license_id:
            raise serializers.ValidationError(
                '端末IDとライセンスIDは同時に指定できません。'
            )
        
        return data


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications.
    """
    
    employee = EmployeeListSerializer(read_only=True)
    related_license = LicenseListSerializer(read_only=True)
    related_device = DeviceListSerializer(read_only=True)
    related_request = ResourceRequestSerializer(read_only=True)
    
    # Display fields
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'employee', 'notification_type', 'notification_type_display',
            'title', 'message', 'priority', 'priority_display',
            'status', 'status_display', 'related_license', 'related_device',
            'related_request', 'scheduled_at', 'sent_at', 'read_at',
            'dismissed_at', 'data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee', 'sent_at', 'read_at', 'dismissed_at',
            'created_at', 'updated_at'
        ]