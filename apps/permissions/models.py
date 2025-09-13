"""
Permission models for the asset management system.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from django.db import transaction

User = get_user_model()


class PermissionPolicy(models.Model):
    """
    Permission policy model that defines access rules for employees based on department and position.
    Supports both standard policies and individual restrictions.
    """
    
    POLICY_TYPE_CHOICES = [
        ('DEPARTMENT', '部署別'),
        ('POSITION', '役職別'),
        ('INDIVIDUAL', '個別'),
        ('GLOBAL', '全社共通'),
    ]
    
    PRIORITY_CHOICES = [
        (1, '最高'),
        (2, '高'),
        (3, '中'),
        (4, '低'),
        (5, '最低'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Policy identification
    name = models.CharField(
        max_length=200,
        help_text="ポリシー名"
    )
    
    description = models.TextField(
        blank=True,
        help_text="ポリシーの説明"
    )
    
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPE_CHOICES,
        help_text="ポリシー種別"
    )
    
    # Target criteria
    target_department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="対象部署（部署別ポリシーの場合）"
    )
    
    target_position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="対象役職（役職別ポリシーの場合）"
    )
    
    target_employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='individual_policies',
        help_text="対象社員（個別ポリシーの場合）"
    )
    
    # Policy priority (lower number = higher priority)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
        help_text="優先度（数値が小さいほど高優先度）"
    )
    
    # Device permissions
    allowed_device_types = models.JSONField(
        default=list,
        blank=True,
        help_text="許可端末種別のリスト"
    )
    
    max_devices_per_type = models.JSONField(
        default=dict,
        blank=True,
        help_text="端末種別ごとの最大保有数"
    )
    
    # Software permissions
    allowed_software = models.JSONField(
        default=list,
        blank=True,
        help_text="許可ソフトウェアのリスト"
    )
    
    restricted_software = models.JSONField(
        default=list,
        blank=True,
        help_text="禁止ソフトウェアのリスト"
    )
    
    max_licenses_per_software = models.JSONField(
        default=dict,
        blank=True,
        help_text="ソフトウェアごとの最大ライセンス数"
    )
    
    # Status and validity
    is_active = models.BooleanField(
        default=True,
        help_text="有効フラグ"
    )
    
    effective_from = models.DateField(
        default=date.today,
        help_text="有効開始日"
    )
    
    effective_until = models.DateField(
        null=True,
        blank=True,
        help_text="有効終了日"
    )
    
    # Additional settings
    auto_approve_requests = models.BooleanField(
        default=False,
        help_text="申請の自動承認"
    )
    
    require_manager_approval = models.BooleanField(
        default=True,
        help_text="管理者承認必須"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_policies',
        help_text="作成者"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_policies',
        help_text="更新者"
    )
    
    class Meta:
        db_table = 'permission_policies'
        verbose_name = '権限ポリシー'
        verbose_name_plural = '権限ポリシー'
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['policy_type']),
            models.Index(fields=['target_department']),
            models.Index(fields=['target_position']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            # Ensure department policies have target_department
            models.CheckConstraint(
                check=models.Q(
                    ~models.Q(policy_type='DEPARTMENT') | 
                    models.Q(target_department__isnull=False)
                ),
                name='department_policy_has_target_department'
            ),
            # Ensure position policies have target_position
            models.CheckConstraint(
                check=models.Q(
                    ~models.Q(policy_type='POSITION') | 
                    models.Q(target_position__isnull=False)
                ),
                name='position_policy_has_target_position'
            ),
            # Ensure individual policies have target_employee
            models.CheckConstraint(
                check=models.Q(
                    ~models.Q(policy_type='INDIVIDUAL') | 
                    models.Q(target_employee__isnull=False)
                ),
                name='individual_policy_has_target_employee'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_policy_type_display()})"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate policy type specific requirements
        if self.policy_type == 'DEPARTMENT' and not self.target_department:
            raise ValidationError({
                'target_department': '部署別ポリシーには対象部署の指定が必要です。'
            })
        
        if self.policy_type == 'POSITION' and not self.target_position:
            raise ValidationError({
                'target_position': '役職別ポリシーには対象役職の指定が必要です。'
            })
        
        if self.policy_type == 'INDIVIDUAL' and not self.target_employee:
            raise ValidationError({
                'target_employee': '個別ポリシーには対象社員の指定が必要です。'
            })
        
        # Validate effective dates
        if self.effective_until and self.effective_from > self.effective_until:
            raise ValidationError({
                'effective_until': '有効終了日は有効開始日より後である必要があります。'
            })
    
    @property
    def is_currently_effective(self):
        """Check if policy is currently effective."""
        if not self.is_active:
            return False
        
        today = timezone.now().date()
        
        if self.effective_from > today:
            return False
        
        if self.effective_until and self.effective_until < today:
            return False
        
        return True
    
    def applies_to_employee(self, employee):
        """Check if this policy applies to the given employee."""
        if not self.is_currently_effective:
            return False
        
        if self.policy_type == 'GLOBAL':
            return True
        elif self.policy_type == 'DEPARTMENT':
            return employee.department == self.target_department
        elif self.policy_type == 'POSITION':
            return employee.position == self.target_position
        elif self.policy_type == 'INDIVIDUAL':
            return employee == self.target_employee
        
        return False
    
    def can_access_device_type(self, device_type):
        """Check if this policy allows access to the specified device type."""
        if not self.allowed_device_types:
            return True  # No restrictions means allowed
        return device_type in self.allowed_device_types
    
    def can_access_software(self, software_name):
        """Check if this policy allows access to the specified software."""
        # Check if explicitly restricted
        if software_name in self.restricted_software:
            return False
        
        # If allowed list is empty, everything is allowed (except restricted)
        if not self.allowed_software:
            return True
        
        # Check if explicitly allowed
        return software_name in self.allowed_software
    
    def get_max_devices_for_type(self, device_type):
        """Get maximum number of devices allowed for the specified type."""
        return self.max_devices_per_type.get(device_type, None)
    
    def get_max_licenses_for_software(self, software_name):
        """Get maximum number of licenses allowed for the specified software."""
        return self.max_licenses_per_software.get(software_name, None)


class PermissionOverride(models.Model):
    """
    Model for temporary permission overrides that can grant or restrict access beyond standard policies.
    """
    
    OVERRIDE_TYPE_CHOICES = [
        ('GRANT', '許可'),
        ('RESTRICT', '制限'),
    ]
    
    RESOURCE_TYPE_CHOICES = [
        ('DEVICE', '端末'),
        ('SOFTWARE', 'ソフトウェア'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Target
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='permission_overrides',
        help_text="対象社員"
    )
    
    # Override details
    override_type = models.CharField(
        max_length=10,
        choices=OVERRIDE_TYPE_CHOICES,
        help_text="オーバーライド種別"
    )
    
    resource_type = models.CharField(
        max_length=10,
        choices=RESOURCE_TYPE_CHOICES,
        help_text="リソース種別"
    )
    
    resource_identifier = models.CharField(
        max_length=200,
        help_text="リソース識別子（端末種別またはソフトウェア名）"
    )
    
    # Validity
    effective_from = models.DateField(
        default=date.today,
        help_text="有効開始日"
    )
    
    effective_until = models.DateField(
        help_text="有効終了日"
    )
    
    # Additional information
    reason = models.TextField(
        help_text="理由"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="有効フラグ"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_overrides',
        help_text="作成者"
    )
    
    class Meta:
        db_table = 'permission_overrides'
        verbose_name = '権限オーバーライド'
        verbose_name_plural = '権限オーバーライド'
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['employee', 'resource_type']),
            models.Index(fields=['effective_from', 'effective_until']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_override_type_display()} {self.resource_identifier}"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate effective dates
        if self.effective_from > self.effective_until:
            raise ValidationError({
                'effective_until': '有効終了日は有効開始日より後である必要があります。'
            })
    
    @property
    def is_currently_effective(self):
        """Check if override is currently effective."""
        if not self.is_active:
            return False
        
        today = timezone.now().date()
        return self.effective_from <= today <= self.effective_until


class PermissionAuditLog(models.Model):
    """
    Audit log for permission-related actions and access attempts.
    """
    
    ACTION_CHOICES = [
        ('POLICY_CREATED', 'ポリシー作成'),
        ('POLICY_UPDATED', 'ポリシー更新'),
        ('POLICY_DELETED', 'ポリシー削除'),
        ('OVERRIDE_CREATED', 'オーバーライド作成'),
        ('OVERRIDE_UPDATED', 'オーバーライド更新'),
        ('OVERRIDE_DELETED', 'オーバーライド削除'),
        ('ACCESS_GRANTED', 'アクセス許可'),
        ('ACCESS_DENIED', 'アクセス拒否'),
        ('PERMISSION_CHECK', '権限チェック'),
        ('AUTO_UPDATE', '自動更新'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="アクション"
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audit_logs',
        help_text="対象社員"
    )
    
    resource_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="リソース種別"
    )
    
    resource_identifier = models.CharField(
        max_length=200,
        blank=True,
        help_text="リソース識別子"
    )
    
    # Result and details
    result = models.CharField(
        max_length=20,
        blank=True,
        help_text="結果"
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="詳細情報"
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="実行者"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IPアドレス"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="ユーザーエージェント"
    )
    
    class Meta:
        db_table = 'permission_audit_logs'
        verbose_name = '権限監査ログ'
        verbose_name_plural = '権限監査ログ'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['employee', '-timestamp']),
            models.Index(fields=['resource_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp}"
