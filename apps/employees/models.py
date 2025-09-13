"""
Employee models for the asset management system.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone

User = get_user_model()


class Employee(models.Model):
    """
    Employee model that extends User information with business-specific data.
    This model maintains the relationship between system users and employee records.
    """
    
    LOCATION_CHOICES = [
        ('TOKYO', '東京'),
        ('OKINAWA', '沖縄'),
        ('REMOTE', 'リモート'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('INACTIVE', '非アクティブ'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to User model (one-to-one relationship)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        help_text="関連するユーザーアカウント"
    )
    
    # Employee identification
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]{3,20}$',
                message='社員IDは3-20文字の英数字（大文字）で入力してください'
            )
        ],
        help_text="社員ID (例: EMP001, TOKYO001)"
    )
    
    # Personal information
    name = models.CharField(
        max_length=100,
        help_text="氏名"
    )
    
    name_kana = models.CharField(
        max_length=100,
        blank=True,
        help_text="氏名（カナ）"
    )
    
    email = models.EmailField(
        unique=True,
        help_text="メールアドレス"
    )
    
    # Organization information
    department = models.CharField(
        max_length=100,
        help_text="部署"
    )
    
    position = models.CharField(
        max_length=100,
        help_text="役職"
    )
    
    location = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
        help_text="勤務地"
    )
    
    # Employment information
    hire_date = models.DateField(
        help_text="入社日"
    )
    
    termination_date = models.DateField(
        null=True,
        blank=True,
        help_text="退職日"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="ステータス"
    )
    
    # Contact information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\-\+\(\)\s]+$',
                message='有効な電話番号を入力してください'
            )
        ],
        help_text="電話番号"
    )
    
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="緊急連絡先（氏名）"
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\-\+\(\)\s]+$',
                message='有効な電話番号を入力してください'
            )
        ],
        help_text="緊急連絡先（電話番号）"
    )
    
    # Additional information
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
        related_name='created_employees',
        help_text="作成者"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_employees',
        help_text="更新者"
    )
    
    class Meta:
        db_table = 'employees'
        verbose_name = '社員'
        verbose_name_plural = '社員'
        ordering = ['employee_id']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.name}"
    
    @property
    def is_active(self):
        """Check if employee is currently active."""
        return self.status == 'ACTIVE' and (
            self.termination_date is None or 
            self.termination_date > timezone.now().date()
        )
    
    @property
    def full_name_with_kana(self):
        """Return full name with kana if available."""
        if self.name_kana:
            return f"{self.name} ({self.name_kana})"
        return self.name
    
    def terminate_employment(self, termination_date=None, terminated_by=None):
        """
        Terminate employee and mark for resource recovery.
        This method handles the business logic for employee termination.
        """
        if termination_date is None:
            termination_date = timezone.now().date()
        
        self.termination_date = termination_date
        self.status = 'INACTIVE'
        self.updated_by = terminated_by
        self.save(update_fields=['termination_date', 'status', 'updated_by', 'updated_at'])
        
        # Create history record for termination
        EmployeeHistory.objects.create(
            employee=self,
            change_type='TERMINATION',
            field_name='status',
            old_value='ACTIVE',
            new_value='INACTIVE',
            changed_by=terminated_by,
            notes=f"退職処理 - 退職日: {termination_date}"
        )
        
        return self
    
    def reactivate_employment(self, reactivated_by=None):
        """Reactivate terminated employee."""
        self.termination_date = None
        self.status = 'ACTIVE'
        self.updated_by = reactivated_by
        self.save(update_fields=['termination_date', 'status', 'updated_by', 'updated_at'])
        
        # Create history record for reactivation
        EmployeeHistory.objects.create(
            employee=self,
            change_type='REACTIVATION',
            field_name='status',
            old_value='INACTIVE',
            new_value='ACTIVE',
            changed_by=reactivated_by,
            notes="雇用再開"
        )
        
        return self


class EmployeeHistory(models.Model):
    """
    Model to track changes to employee records for audit purposes.
    """
    
    CHANGE_TYPE_CHOICES = [
        ('CREATE', '作成'),
        ('UPDATE', '更新'),
        ('TERMINATION', '退職'),
        ('REACTIVATION', '復職'),
        ('DEPARTMENT_CHANGE', '部署変更'),
        ('POSITION_CHANGE', '役職変更'),
        ('LOCATION_CHANGE', '勤務地変更'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='history_records',
        help_text="対象社員"
    )
    
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        help_text="変更種別"
    )
    
    field_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="変更フィールド名"
    )
    
    old_value = models.TextField(
        blank=True,
        help_text="変更前の値"
    )
    
    new_value = models.TextField(
        blank=True,
        help_text="変更後の値"
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="変更者"
    )
    
    changed_at = models.DateTimeField(auto_now_add=True)
    
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    class Meta:
        db_table = 'employee_history'
        verbose_name = '社員履歴'
        verbose_name_plural = '社員履歴'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['employee', '-changed_at']),
            models.Index(fields=['change_type']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_change_type_display()} ({self.changed_at})"
