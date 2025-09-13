"""
Serializers for device management API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Device, DeviceAssignment
from apps.employees.models import Employee

User = get_user_model()


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model."""
    
    warranty_status = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    is_assigned = serializers.ReadOnlyField()
    current_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'type',
            'manufacturer',
            'model',
            'serial_number',
            'purchase_date',
            'warranty_expiry',
            'status',
            'specifications',
            'notes',
            'warranty_status',
            'is_available',
            'is_assigned',
            'current_assignment',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_assignment(self, obj):
        """Get current assignment information."""
        assignment = obj.current_assignment
        if assignment:
            return {
                'id': assignment.id,
                'employee': {
                    'id': assignment.employee.id,
                    'name': assignment.employee.name,
                    'employee_id': assignment.employee.employee_id
                },
                'assigned_date': assignment.assigned_date,
                'expected_return_date': assignment.expected_return_date,
                'purpose': assignment.purpose
            }
        return None
    
    def validate_serial_number(self, value):
        """Validate serial number uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if Device.objects.exclude(id=self.instance.id).filter(serial_number=value).exists():
                raise serializers.ValidationError("このシリアル番号は既に使用されています。")
        else:
            # Create case
            if Device.objects.filter(serial_number=value).exists():
                raise serializers.ValidationError("このシリアル番号は既に使用されています。")
        return value
    
    def validate(self, data):
        """Validate device data."""
        # Validate warranty expiry is after purchase date
        purchase_date = data.get('purchase_date')
        warranty_expiry = data.get('warranty_expiry')
        
        if purchase_date and warranty_expiry and warranty_expiry < purchase_date:
            raise serializers.ValidationError({
                'warranty_expiry': '保証期限は購入日より後の日付である必要があります。'
            })
        
        return data


class DeviceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for device list views."""
    
    warranty_status = serializers.ReadOnlyField()
    current_assignment_employee = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'type',
            'manufacturer',
            'model',
            'serial_number',
            'status',
            'warranty_status',
            'current_assignment_employee',
            'created_at'
        ]
    
    def get_current_assignment_employee(self, obj):
        """Get current assignment employee name."""
        assignment = obj.current_assignment
        if assignment:
            return assignment.employee.name
        return None


class DeviceAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for DeviceAssignment model."""
    
    device_info = serializers.SerializerMethodField()
    employee_info = serializers.SerializerMethodField()
    days_assigned = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = DeviceAssignment
        fields = [
            'id',
            'device',
            'employee',
            'assigned_date',
            'expected_return_date',
            'actual_return_date',
            'purpose',
            'status',
            'assignment_notes',
            'return_notes',
            'device_info',
            'employee_info',
            'days_assigned',
            'is_overdue',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
    
    def get_device_info(self, obj):
        """Get device information."""
        return {
            'id': obj.device.id,
            'type': obj.device.get_type_display(),
            'manufacturer': obj.device.manufacturer,
            'model': obj.device.model,
            'serial_number': obj.device.serial_number
        }
    
    def get_employee_info(self, obj):
        """Get employee information."""
        return {
            'id': obj.employee.id,
            'name': obj.employee.name,
            'employee_id': obj.employee.employee_id,
            'department': obj.employee.department
        }
    
    def validate(self, data):
        """Validate assignment data."""
        assigned_date = data.get('assigned_date')
        expected_return_date = data.get('expected_return_date')
        actual_return_date = data.get('actual_return_date')
        
        # Validate return dates are after assignment date
        if assigned_date:
            if expected_return_date and expected_return_date < assigned_date:
                raise serializers.ValidationError({
                    'expected_return_date': '返却予定日は割当日より後の日付である必要があります。'
                })
            
            if actual_return_date and actual_return_date < assigned_date:
                raise serializers.ValidationError({
                    'actual_return_date': '返却日は割当日より後の日付である必要があります。'
                })
        
        return data


class DeviceAssignRequestSerializer(serializers.Serializer):
    """Serializer for device assignment requests."""
    
    employee_id = serializers.UUIDField()
    assigned_date = serializers.DateField(default=timezone.now().date)
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    purpose = serializers.CharField(max_length=200)
    assignment_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_employee_id(self, value):
        """Validate employee exists and is active."""
        try:
            employee = Employee.objects.get(id=value)
            if not employee.is_active:
                raise serializers.ValidationError("指定された社員は非アクティブです。")
            return value
        except Employee.DoesNotExist:
            raise serializers.ValidationError("指定された社員が見つかりません。")
    
    def validate(self, data):
        """Validate assignment request data."""
        assigned_date = data.get('assigned_date')
        expected_return_date = data.get('expected_return_date')
        
        if expected_return_date and assigned_date and expected_return_date < assigned_date:
            raise serializers.ValidationError({
                'expected_return_date': '返却予定日は割当日より後の日付である必要があります。'
            })
        
        return data


class DeviceReturnRequestSerializer(serializers.Serializer):
    """Serializer for device return requests."""
    
    return_date = serializers.DateField(default=timezone.now().date)
    return_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_return_date(self, value):
        """Validate return date is not in the future."""
        if value > timezone.now().date():
            raise serializers.ValidationError("返却日は未来の日付にできません。")
        return value


class DeviceAssignmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for device assignment history."""
    
    device_info = serializers.SerializerMethodField()
    employee_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceAssignment
        fields = [
            'id',
            'assigned_date',
            'expected_return_date',
            'actual_return_date',
            'purpose',
            'status',
            'device_info',
            'employee_info',
            'assignment_notes',
            'return_notes'
        ]
    
    def get_device_info(self, obj):
        """Get basic device information."""
        return {
            'type': obj.device.get_type_display(),
            'manufacturer': obj.device.manufacturer,
            'model': obj.device.model,
            'serial_number': obj.device.serial_number
        }
    
    def get_employee_info(self, obj):
        """Get basic employee information."""
        return {
            'name': obj.employee.name,
            'employee_id': obj.employee.employee_id,
            'department': obj.employee.department
        }
