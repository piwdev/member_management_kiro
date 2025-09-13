"""
Employee serializers for the asset management system.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Employee, EmployeeHistory

User = get_user_model()


class EmployeeHistorySerializer(serializers.ModelSerializer):
    """Serializer for employee history records."""
    
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    
    class Meta:
        model = EmployeeHistory
        fields = [
            'id', 'change_type', 'change_type_display', 'field_name',
            'old_value', 'new_value', 'changed_by', 'changed_by_name',
            'changed_at', 'notes'
        ]
        read_only_fields = ['id', 'changed_at']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for employee list view with minimal fields."""
    
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'department', 'position',
            'location', 'location_display', 'status', 'status_display',
            'hire_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed employee information."""
    
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    full_name_with_kana = serializers.CharField(read_only=True)
    
    # User account information (read-only)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    
    # Creator and updater information
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    # History records
    history_records = EmployeeHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'name_kana', 'email',
            'department', 'position', 'location', 'location_display',
            'hire_date', 'termination_date', 'status', 'status_display',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'notes', 'is_active', 'full_name_with_kana',
            'username', 'user_email', 'last_login',
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'history_records'
        ]
        read_only_fields = [
            'id', 'is_active', 'full_name_with_kana', 'username', 'user_email',
            'last_login', 'created_at', 'updated_at', 'created_by_name',
            'updated_by_name', 'history_records'
        ]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new employees."""
    
    # User account fields
    username = serializers.CharField(write_only=True, help_text="ユーザー名")
    password = serializers.CharField(write_only=True, help_text="パスワード")
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'name', 'name_kana', 'email', 'department',
            'position', 'location', 'hire_date', 'phone_number',
            'emergency_contact_name', 'emergency_contact_phone', 'notes',
            'username', 'password'
        ]
    
    def validate_employee_id(self, value):
        """Validate employee ID format and uniqueness."""
        if not value:
            raise serializers.ValidationError("社員IDは必須です。")
        
        # Check if employee ID already exists
        if Employee.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("この社員IDは既に使用されています。")
        
        return value.upper()  # Convert to uppercase
    
    def validate_email(self, value):
        """Validate email uniqueness across employees and users."""
        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("このメールアドレスは既に使用されています。")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("このメールアドレスは既にユーザーアカウントで使用されています。")
        
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("このユーザー名は既に使用されています。")
        
        return value
    
    def validate_hire_date(self, value):
        """Validate hire date is not in the future."""
        if value > timezone.now().date():
            raise serializers.ValidationError("入社日は未来の日付にできません。")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Ensure email matches between employee and user fields
        if 'email' in attrs and attrs['email']:
            # Email will be used for both employee and user account
            pass
        
        return attrs
    
    def create(self, validated_data):
        """Create employee with associated user account."""
        # Extract user-related fields
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Create user account first
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=password,
            first_name=validated_data['name'].split()[0] if validated_data['name'] else '',
            last_name=' '.join(validated_data['name'].split()[1:]) if len(validated_data['name'].split()) > 1 else '',
            employee_id=validated_data['employee_id'],
            department=validated_data['department'],
            position=validated_data['position'],
            location=validated_data['location'],
            hire_date=validated_data['hire_date'],
            phone_number=validated_data.get('phone_number', ''),
        )
        
        # Create employee record
        validated_data['user'] = user
        validated_data['created_by'] = self.context['request'].user
        employee = Employee.objects.create(**validated_data)
        
        # Create history record
        EmployeeHistory.objects.create(
            employee=employee,
            change_type='CREATE',
            changed_by=self.context['request'].user,
            notes=f"社員レコード作成 - ユーザーアカウント: {username}"
        )
        
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing employees."""
    
    class Meta:
        model = Employee
        fields = [
            'name', 'name_kana', 'email', 'department', 'position',
            'location', 'phone_number', 'emergency_contact_name',
            'emergency_contact_phone', 'notes'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness excluding current employee."""
        employee = self.instance
        if Employee.objects.filter(email=value).exclude(id=employee.id).exists():
            raise serializers.ValidationError("このメールアドレスは既に使用されています。")
        
        if User.objects.filter(email=value).exclude(id=employee.user.id).exists():
            raise serializers.ValidationError("このメールアドレスは既にユーザーアカウントで使用されています。")
        
        return value
    
    def update(self, instance, validated_data):
        """Update employee and track changes."""
        request_user = self.context['request'].user
        
        # Track changes for history
        changes = []
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value:
                changes.append({
                    'field_name': field,
                    'old_value': str(old_value) if old_value is not None else '',
                    'new_value': str(new_value) if new_value is not None else '',
                })
        
        # Update employee
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.updated_by = request_user
        instance.save()
        
        # Update related user account
        user = instance.user
        if 'email' in validated_data:
            user.email = validated_data['email']
        if 'department' in validated_data:
            user.department = validated_data['department']
        if 'position' in validated_data:
            user.position = validated_data['position']
        if 'location' in validated_data:
            user.location = validated_data['location']
        
        user.save()
        
        # Create history records for changes
        for change in changes:
            change_type = 'UPDATE'
            if change['field_name'] == 'department':
                change_type = 'DEPARTMENT_CHANGE'
            elif change['field_name'] == 'position':
                change_type = 'POSITION_CHANGE'
            elif change['field_name'] == 'location':
                change_type = 'LOCATION_CHANGE'
            
            EmployeeHistory.objects.create(
                employee=instance,
                change_type=change_type,
                field_name=change['field_name'],
                old_value=change['old_value'],
                new_value=change['new_value'],
                changed_by=request_user
            )
        
        return instance


class EmployeeTerminationSerializer(serializers.Serializer):
    """Serializer for employee termination."""
    
    termination_date = serializers.DateField(
        required=False,
        help_text="退職日（指定しない場合は今日の日付）"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="退職理由・備考"
    )
    
    def validate_termination_date(self, value):
        """Validate termination date."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("退職日は未来の日付にできません。")
        
        return value
    
    def save(self, employee):
        """Terminate the employee."""
        termination_date = self.validated_data.get('termination_date')
        notes = self.validated_data.get('notes', '')
        request_user = self.context['request'].user
        
        # Terminate employment
        employee.terminate_employment(
            termination_date=termination_date,
            terminated_by=request_user
        )
        
        # Add notes to the termination history record if provided
        if notes:
            history_record = employee.history_records.filter(
                change_type='TERMINATION'
            ).first()
            if history_record:
                history_record.notes = f"{history_record.notes}\n備考: {notes}"
                history_record.save()
        
        return employee
