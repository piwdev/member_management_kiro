"""
Device models for the asset management system.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class Device(models.Model):
    """
    Device model for managing hardware assets like laptops, desktops, tablets, and smartphones.
    """
    
    TYPE_CHOICES = [
        ('LAPTOP', 'ラップトップ'),
        ('DESKTOP', 'デスクトップ'),
        ('TABLET', 'タブレット'),
        ('SMARTPHONE', 'スマートフォン'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', '利用可能'),
        ('ASSIGNED', '貸出中'),
        ('MAINTENANCE', '修理中'),
        ('DISPOSED', '廃棄'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Device identification
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="端末種別"
    )
    
    manufacturer = models.CharField(
        max_length=100,
        help_text="メーカー"
    )
    
    model = models.CharField(
        max_length=100,
        help_text="モデル"
    )
    
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9\-]+$',
                message='シリアル番号は英数字とハイフンのみ使用可能です'
            )
        ],
        help_text="シリアル番号"
    )
    
    # Purchase and warranty information
    purchase_date = models.DateField(
        help_text="購入日"
    )
    
    warranty_expiry = models.DateField(
        help_text="保証期限"
    )
    
    # Status and availability
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE',
        help_text="ステータス"
    )
    
    # Additional information
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="仕様情報 (CPU, メモリ, ストレージ等)"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_devices',
        help_text="作成者"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_devices',
        help_text="更新者"
    )
    
    class Meta:
        db_table = 'devices'
        verbose_name = '端末'
        verbose_name_plural = '端末'
        ordering = ['type', 'manufacturer', 'model']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['manufacturer']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.manufacturer} {self.model} ({self.serial_number})"
    
    @property
    def is_available(self):
        """Check if device is available for assignment."""
        return self.status == 'AVAILABLE'
    
    @property
    def is_assigned(self):
        """Check if device is currently assigned."""
        return self.status == 'ASSIGNED'
    
    @property
    def current_assignment(self):
        """Get current active assignment if any."""
        return self.assignments.filter(status='ACTIVE').first()
    
    @property
    def warranty_status(self):
        """Check warranty status."""
        today = timezone.now().date()
        if self.warranty_expiry < today:
            return 'EXPIRED'
        elif (self.warranty_expiry - today).days <= 30:
            return 'EXPIRING_SOON'
        return 'VALID'
    
    def clean(self):
        """Custom validation for the Device model."""
        super().clean()
        
        # Validate warranty expiry is after purchase date
        if self.warranty_expiry and self.purchase_date:
            if self.warranty_expiry < self.purchase_date:
                raise ValidationError({
                    'warranty_expiry': '保証期限は購入日より後の日付である必要があります'
                })
    
    def assign_to_employee(self, employee, assigned_date=None, return_date=None, purpose='', assigned_by=None):
        """
        Assign device to an employee.
        """
        from apps.employees.models import Employee
        
        if not self.is_available:
            raise ValidationError(f'端末は現在利用できません。ステータス: {self.get_status_display()}')
        
        if assigned_date is None:
            assigned_date = timezone.now().date()
        
        # Create assignment record
        assignment = DeviceAssignment.objects.create(
            device=self,
            employee=employee,
            assigned_date=assigned_date,
            expected_return_date=return_date,
            purpose=purpose,
            assigned_by=assigned_by,
            status='ACTIVE'
        )
        
        # Update device status
        self.status = 'ASSIGNED'
        self.updated_by = assigned_by
        self.save(update_fields=['status', 'updated_by', 'updated_at'])
        
        return assignment
    
    def return_from_employee(self, return_date=None, returned_by=None, notes=''):
        """
        Return device from current assignment.
        """
        current_assignment = self.current_assignment
        if not current_assignment:
            raise ValidationError('この端末は現在割り当てられていません')
        
        if return_date is None:
            return_date = timezone.now().date()
        
        # Update assignment record
        current_assignment.actual_return_date = return_date
        current_assignment.return_notes = notes
        current_assignment.returned_by = returned_by
        current_assignment.status = 'RETURNED'
        current_assignment.save(update_fields=[
            'actual_return_date', 'return_notes', 'returned_by', 'status', 'updated_at'
        ])
        
        # Update device status
        self.status = 'AVAILABLE'
        self.updated_by = returned_by
        self.save(update_fields=['status', 'updated_by', 'updated_at'])
        
        return current_assignment


class DeviceAssignment(models.Model):
    """
    Model to track device assignments to employees (lending history).
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('RETURNED', '返却済み'),
        ('OVERDUE', '期限超過'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="割り当て端末"
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='device_assignments',
        help_text="割り当て社員"
    )
    
    # Assignment details
    assigned_date = models.DateField(
        help_text="割当日"
    )
    
    expected_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="返却予定日"
    )
    
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="実際の返却日"
    )
    
    purpose = models.CharField(
        max_length=200,
        help_text="使用目的"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="ステータス"
    )
    
    # Notes and additional information
    assignment_notes = models.TextField(
        blank=True,
        help_text="割当時の備考"
    )
    
    return_notes = models.TextField(
        blank=True,
        help_text="返却時の備考"
    )
    
    # Metadata
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_devices',
        help_text="割当実行者"
    )
    
    returned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returned_devices',
        help_text="返却処理者"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_assignments'
        verbose_name = '端末割当'
        verbose_name_plural = '端末割当'
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['device', '-assigned_date']),
            models.Index(fields=['employee', '-assigned_date']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_date']),
        ]
        constraints = [
            # Ensure only one active assignment per device
            models.UniqueConstraint(
                fields=['device'],
                condition=models.Q(status='ACTIVE'),
                name='unique_active_device_assignment'
            )
        ]
    
    def __str__(self):
        return f"{self.device} → {self.employee.name} ({self.assigned_date})"
    
    @property
    def is_active(self):
        """Check if assignment is currently active."""
        return self.status == 'ACTIVE'
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue."""
        if not self.expected_return_date or self.actual_return_date:
            return False
        return timezone.now().date() > self.expected_return_date
    
    @property
    def days_assigned(self):
        """Calculate number of days the device has been assigned."""
        end_date = self.actual_return_date or timezone.now().date()
        return (end_date - self.assigned_date).days
    
    def clean(self):
        """Custom validation for the DeviceAssignment model."""
        super().clean()
        
        # Validate return date is after assignment date
        if self.actual_return_date and self.assigned_date:
            if self.actual_return_date < self.assigned_date:
                raise ValidationError({
                    'actual_return_date': '返却日は割当日より後の日付である必要があります'
                })
        
        # Validate expected return date is after assignment date
        if self.expected_return_date and self.assigned_date:
            if self.expected_return_date < self.assigned_date:
                raise ValidationError({
                    'expected_return_date': '返却予定日は割当日より後の日付である必要があります'
                })
    
    def save(self, *args, **kwargs):
        """Override save to update status based on dates."""
        # Auto-update status based on dates
        if self.actual_return_date:
            self.status = 'RETURNED'
        elif self.is_overdue:
            self.status = 'OVERDUE'
        elif not self.actual_return_date:
            self.status = 'ACTIVE'
        
        super().save(*args, **kwargs)
