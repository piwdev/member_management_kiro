"""
License serializers for the asset management system.
"""

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import License, LicenseAssignment
from apps.employees.models import Employee


class LicenseSerializer(serializers.ModelSerializer):
    """
    Serializer for License model with computed fields for usage statistics and cost calculations.
    """
    
    # Read-only computed fields
    used_count = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    is_fully_utilized = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    monthly_cost = serializers.SerializerMethodField()
    yearly_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    is_expiring_soon = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = License
        fields = [
            'id', 'software_name', 'license_type', 'total_count', 'available_count',
            'expiry_date', 'license_key', 'usage_conditions', 'pricing_model',
            'unit_price', 'vendor_name', 'purchase_date', 'description', 'notes',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            # Computed fields
            'used_count', 'usage_percentage', 'is_fully_utilized', 'is_expired',
            'monthly_cost', 'yearly_cost', 'total_cost', 'is_expiring_soon',
            'days_until_expiry'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'used_count', 'usage_percentage', 'is_fully_utilized', 'is_expired',
            'monthly_cost', 'yearly_cost', 'total_cost', 'is_expiring_soon',
            'days_until_expiry'
        ]
    
    def get_monthly_cost(self, obj):
        """Calculate monthly cost for the license."""
        return float(obj.calculate_monthly_cost())
    
    def get_yearly_cost(self, obj):
        """Calculate yearly cost for the license."""
        return float(obj.calculate_yearly_cost())
    
    def get_total_cost(self, obj):
        """Calculate total cost for the license."""
        return float(obj.calculate_total_cost())
    
    def get_is_expiring_soon(self, obj):
        """Check if license is expiring within 30 days."""
        return obj.is_expiring_soon(days=30)
    
    def get_days_until_expiry(self, obj):
        """Calculate days until license expiry."""
        if not obj.expiry_date:
            return None
        
        today = timezone.now().date()
        if obj.expiry_date < today:
            return 0  # Already expired
        
        return (obj.expiry_date - today).days
    
    def validate(self, data):
        """Validate license data."""
        # Ensure available_count <= total_count
        total_count = data.get('total_count')
        available_count = data.get('available_count')
        
        if total_count is not None and available_count is not None:
            if available_count > total_count:
                raise serializers.ValidationError({
                    'available_count': '利用可能数は購入数を超えることはできません。'
                })
        
        # Validate expiry_date is not in the past for new licenses
        expiry_date = data.get('expiry_date')
        if expiry_date and not self.instance and expiry_date < timezone.now().date():
            raise serializers.ValidationError({
                'expiry_date': '有効期限は現在の日付より後である必要があります。'
            })
        
        return data
    
    def create(self, validated_data):
        """Create license with current user as creator."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update license with current user as updater."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class LicenseListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for license list views with essential information only.
    """
    
    used_count = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    is_expiring_soon = serializers.SerializerMethodField()
    monthly_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = License
        fields = [
            'id', 'software_name', 'license_type', 'total_count', 'available_count',
            'expiry_date', 'pricing_model', 'unit_price', 'used_count',
            'usage_percentage', 'is_expiring_soon', 'monthly_cost'
        ]
    
    def get_is_expiring_soon(self, obj):
        """Check if license is expiring within 30 days."""
        return obj.is_expiring_soon(days=30)
    
    def get_monthly_cost(self, obj):
        """Calculate monthly cost for the license."""
        return float(obj.calculate_monthly_cost())


class LicenseAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for LicenseAssignment model with nested license and employee information.
    """
    
    # Nested serializers for related objects
    license_info = serializers.SerializerMethodField()
    employee_info = serializers.SerializerMethodField()
    
    # Computed fields
    is_active = serializers.ReadOnlyField()
    is_expiring_soon = serializers.SerializerMethodField()
    usage_days = serializers.SerializerMethodField()
    
    class Meta:
        model = LicenseAssignment
        fields = [
            'id', 'license', 'employee', 'assigned_date', 'start_date', 'end_date',
            'purpose', 'status', 'notes', 'created_at', 'updated_at',
            'assigned_by', 'revoked_by', 'revoked_at',
            # Nested and computed fields
            'license_info', 'employee_info', 'is_active', 'is_expiring_soon',
            'usage_days'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'assigned_by', 'revoked_by',
            'revoked_at', 'license_info', 'employee_info', 'is_active',
            'is_expiring_soon', 'usage_days'
        ]
    
    def get_license_info(self, obj):
        """Get basic license information."""
        return {
            'id': str(obj.license.id),
            'software_name': obj.license.software_name,
            'license_type': obj.license.license_type,
            'expiry_date': obj.license.expiry_date,
            'is_expired': obj.license.is_expired
        }
    
    def get_employee_info(self, obj):
        """Get basic employee information."""
        return {
            'id': str(obj.employee.id),
            'employee_id': obj.employee.employee_id,
            'name': obj.employee.name,
            'department': obj.employee.department,
            'position': obj.employee.position
        }
    
    def get_is_expiring_soon(self, obj):
        """Check if assignment is expiring within 30 days."""
        return obj.is_expiring_soon(days=30)
    
    def get_usage_days(self, obj):
        """Calculate usage days for the assignment."""
        return obj.calculate_usage_days()
    
    def validate(self, data):
        """Validate assignment data."""
        license_obj = data.get('license')
        employee = data.get('employee')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate employee is active
        if employee and not employee.is_active:
            raise serializers.ValidationError({
                'employee': '非アクティブな社員にはライセンスを割り当てできません。'
            })
        
        # Validate license availability (only for new assignments)
        if not self.instance and license_obj:
            if not license_obj.can_assign():
                if license_obj.is_expired:
                    raise serializers.ValidationError({
                        'license': '期限切れのライセンスは割り当てできません。'
                    })
                else:
                    raise serializers.ValidationError({
                        'license': f'利用可能なライセンス数が不足しています。利用可能: {license_obj.available_count}'
                    })
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '利用終了日は利用開始日より後である必要があります。'
            })
        
        # Check for duplicate active assignments (only for new assignments)
        if not self.instance and license_obj and employee:
            existing = LicenseAssignment.objects.filter(
                license=license_obj,
                employee=employee,
                status='ACTIVE'
            ).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'employee': 'この社員には既に同じライセンスが割り当てられています。'
                })
        
        return data
    
    def create(self, validated_data):
        """Create assignment with current user as assigner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class LicenseAssignmentCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating license assignments.
    """
    
    class Meta:
        model = LicenseAssignment
        fields = [
            'license', 'employee', 'start_date', 'end_date', 'purpose', 'notes'
        ]
    
    def to_representation(self, instance):
        """Convert UUID fields to strings for consistent API responses."""
        data = super().to_representation(instance)
        data['license'] = str(data['license'])
        data['employee'] = str(data['employee'])
        return data
    
    def validate(self, data):
        """Validate assignment data."""
        license_obj = data.get('license')
        employee = data.get('employee')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate employee is active
        if employee and not employee.is_active:
            raise serializers.ValidationError({
                'employee': '非アクティブな社員にはライセンスを割り当てできません。'
            })
        
        # Validate license availability
        if license_obj and not license_obj.can_assign():
            if license_obj.is_expired:
                raise serializers.ValidationError({
                    'license': '期限切れのライセンスは割り当てできません。'
                })
            else:
                raise serializers.ValidationError({
                    'license': f'利用可能なライセンス数が不足しています。利用可能: {license_obj.available_count}'
                })
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '利用終了日は利用開始日より後である必要があります。'
            })
        
        # Check for duplicate active assignments
        if license_obj and employee:
            existing = LicenseAssignment.objects.filter(
                license=license_obj,
                employee=employee,
                status='ACTIVE'
            ).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'employee': 'この社員には既に同じライセンスが割り当てられています。'
                })
        
        return data
    
    def create(self, validated_data):
        """Create assignment with current user as assigner and default assigned_date."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        
        # Set assigned_date to today if not provided
        if 'assigned_date' not in validated_data:
            validated_data['assigned_date'] = timezone.now().date()
        
        return super().create(validated_data)


class LicenseUsageStatsSerializer(serializers.Serializer):
    """
    Serializer for license usage statistics and alerts.
    """
    
    total_licenses = serializers.IntegerField()
    active_licenses = serializers.IntegerField()
    expired_licenses = serializers.IntegerField()
    expiring_soon_licenses = serializers.IntegerField()
    fully_utilized_licenses = serializers.IntegerField()
    total_monthly_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_yearly_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # License alerts
    expiring_licenses = LicenseListSerializer(many=True)
    over_utilized_licenses = LicenseListSerializer(many=True)
    
    class Meta:
        fields = [
            'total_licenses', 'active_licenses', 'expired_licenses',
            'expiring_soon_licenses', 'fully_utilized_licenses',
            'total_monthly_cost', 'total_yearly_cost',
            'expiring_licenses', 'over_utilized_licenses'
        ]


class LicenseCostAnalysisSerializer(serializers.Serializer):
    """
    Serializer for license cost analysis by department, software, etc.
    """
    
    software_name = serializers.CharField()
    license_type = serializers.CharField()
    department = serializers.CharField(required=False)
    total_licenses = serializers.IntegerField()
    used_licenses = serializers.IntegerField()
    monthly_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    yearly_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    usage_percentage = serializers.FloatField()
    
    class Meta:
        fields = [
            'software_name', 'license_type', 'department', 'total_licenses',
            'used_licenses', 'monthly_cost', 'yearly_cost', 'usage_percentage'
        ]
