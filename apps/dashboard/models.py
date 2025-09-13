"""
Dashboard models for employee resource requests.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class ResourceRequest(models.Model):
    """
    Model for tracking employee resource requests (devices and licenses).
    """
    
    REQUEST_TYPE_CHOICES = [
        ('DEVICE', '端末'),
        ('LICENSE', 'ライセンス'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '承認待ち'),
        ('APPROVED', '承認済み'),
        ('REJECTED', '却下'),
        ('FULFILLED', '完了'),
        ('CANCELLED', 'キャンセル'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', '低'),
        ('MEDIUM', '中'),
        ('HIGH', '高'),
        ('URGENT', '緊急'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Request details
    request_type = models.CharField(
        max_length=10,
        choices=REQUEST_TYPE_CHOICES,
        help_text="リクエスト種別"
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='resource_requests',
        help_text="申請者"
    )
    
    # Resource specification
    device_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="希望端末種別（端末申請の場合）"
    )
    
    software_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="希望ソフトウェア名（ライセンス申請の場合）"
    )
    
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="詳細仕様・要件"
    )
    
    # Request details
    purpose = models.TextField(
        help_text="利用目的・理由"
    )
    
    business_justification = models.TextField(
        help_text="業務上の必要性"
    )
    
    expected_usage_period = models.CharField(
        max_length=100,
        help_text="利用予定期間"
    )
    
    expected_start_date = models.DateField(
        help_text="利用開始希望日"
    )
    
    expected_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="利用終了予定日"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        help_text="優先度"
    )
    
    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="ステータス"
    )
    
    # Approval workflow
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_resource_requests',
        help_text="承認者"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="承認日時"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text="却下理由"
    )
    
    # Fulfillment
    fulfilled_device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_requests',
        help_text="割り当てられた端末"
    )
    
    fulfilled_license = models.ForeignKey(
        'licenses.License',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_requests',
        help_text="割り当てられたライセンス"
    )
    
    fulfilled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="完了日時"
    )
    
    fulfilled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_resource_requests',
        help_text="完了処理者"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text="管理者メモ"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resource_requests'
        verbose_name = 'リソース申請'
        verbose_name_plural = 'リソース申請'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['request_type', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['expected_start_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_request_type_display()} ({self.get_status_display()})"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate request type specific fields
        if self.request_type == 'DEVICE' and not self.device_type:
            raise ValidationError({
                'device_type': '端末申請の場合、端末種別は必須です。'
            })
        
        if self.request_type == 'LICENSE' and not self.software_name:
            raise ValidationError({
                'software_name': 'ライセンス申請の場合、ソフトウェア名は必須です。'
            })
        
        # Validate date range
        if self.expected_end_date and self.expected_start_date > self.expected_end_date:
            raise ValidationError({
                'expected_end_date': '利用終了予定日は利用開始希望日より後である必要があります。'
            })
    
    @property
    def is_pending(self):
        """Check if request is pending approval."""
        return self.status == 'PENDING'
    
    @property
    def is_approved(self):
        """Check if request is approved."""
        return self.status == 'APPROVED'
    
    @property
    def is_fulfilled(self):
        """Check if request is fulfilled."""
        return self.status == 'FULFILLED'
    
    def approve(self, approved_by, notes=None):
        """Approve the resource request."""
        if self.status != 'PENDING':
            raise ValidationError('承認待ち以外のリクエストは承認できません。')
        
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        
        if notes:
            self.admin_notes = f"{self.admin_notes}\n承認メモ: {notes}" if self.admin_notes else f"承認メモ: {notes}"
        
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'admin_notes', 'updated_at'])
        return self
    
    def reject(self, rejected_by, reason):
        """Reject the resource request."""
        if self.status != 'PENDING':
            raise ValidationError('承認待ち以外のリクエストは却下できません。')
        
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.approved_by = rejected_by  # Track who made the decision
        self.approved_at = timezone.now()
        
        self.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_at', 'updated_at'])
        return self
    
    def fulfill(self, fulfilled_by, device=None, license_obj=None, notes=None):
        """Mark the request as fulfilled with assigned resource."""
        if self.status != 'APPROVED':
            raise ValidationError('承認済み以外のリクエストは完了できません。')
        
        if self.request_type == 'DEVICE' and not device:
            raise ValidationError('端末申請の完了には端末の指定が必要です。')
        
        if self.request_type == 'LICENSE' and not license_obj:
            raise ValidationError('ライセンス申請の完了にはライセンスの指定が必要です。')
        
        self.status = 'FULFILLED'
        self.fulfilled_by = fulfilled_by
        self.fulfilled_at = timezone.now()
        
        if device:
            self.fulfilled_device = device
        if license_obj:
            self.fulfilled_license = license_obj
        
        if notes:
            self.admin_notes = f"{self.admin_notes}\n完了メモ: {notes}" if self.admin_notes else f"完了メモ: {notes}"
        
        self.save(update_fields=[
            'status', 'fulfilled_by', 'fulfilled_at', 'fulfilled_device', 
            'fulfilled_license', 'admin_notes', 'updated_at'
        ])
        return self
    
    def cancel(self, cancelled_by=None, reason=None):
        """Cancel the resource request."""
        if self.status in ['FULFILLED', 'CANCELLED']:
            raise ValidationError('完了済みまたはキャンセル済みのリクエストはキャンセルできません。')
        
        self.status = 'CANCELLED'
        
        if reason:
            self.notes = f"{self.notes}\nキャンセル理由: {reason}" if self.notes else f"キャンセル理由: {reason}"
        
        self.save(update_fields=['status', 'notes', 'updated_at'])
        return self


class ReturnRequest(models.Model):
    """
    Model for tracking employee resource return requests.
    """
    
    REQUEST_TYPE_CHOICES = [
        ('DEVICE', '端末'),
        ('LICENSE', 'ライセンス'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '処理待ち'),
        ('APPROVED', '承認済み'),
        ('COMPLETED', '完了'),
        ('CANCELLED', 'キャンセル'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Request details
    request_type = models.CharField(
        max_length=10,
        choices=REQUEST_TYPE_CHOICES,
        help_text="返却種別"
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='return_requests',
        help_text="申請者"
    )
    
    # Resource to return
    device_assignment = models.ForeignKey(
        'devices.DeviceAssignment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='return_requests',
        help_text="返却対象端末割当"
    )
    
    license_assignment = models.ForeignKey(
        'licenses.LicenseAssignment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='return_requests',
        help_text="返却対象ライセンス割当"
    )
    
    # Return details
    expected_return_date = models.DateField(
        help_text="返却予定日"
    )
    
    return_reason = models.TextField(
        help_text="返却理由"
    )
    
    condition_notes = models.TextField(
        blank=True,
        help_text="状態・コンディション（端末の場合）"
    )
    
    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="ステータス"
    )
    
    # Processing
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_return_requests',
        help_text="処理者"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="処理日時"
    )
    
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="実際の返却日"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text="管理者メモ"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'return_requests'
        verbose_name = '返却申請'
        verbose_name_plural = '返却申請'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['request_type', 'status']),
            models.Index(fields=['expected_return_date']),
        ]
    
    def __str__(self):
        resource_name = ""
        if self.device_assignment:
            resource_name = str(self.device_assignment.device)
        elif self.license_assignment:
            resource_name = str(self.license_assignment.license)
        
        return f"{self.employee.name} - {resource_name} 返却申請 ({self.get_status_display()})"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate request type specific fields
        if self.request_type == 'DEVICE' and not self.device_assignment:
            raise ValidationError({
                'device_assignment': '端末返却申請の場合、端末割当は必須です。'
            })
        
        if self.request_type == 'LICENSE' and not self.license_assignment:
            raise ValidationError({
                'license_assignment': 'ライセンス返却申請の場合、ライセンス割当は必須です。'
            })
        
        # Validate that the assignment belongs to the employee
        if self.device_assignment and self.device_assignment.employee != self.employee:
            raise ValidationError({
                'device_assignment': '他の社員の端末割当は返却申請できません。'
            })
        
        if self.license_assignment and self.license_assignment.employee != self.employee:
            raise ValidationError({
                'license_assignment': '他の社員のライセンス割当は返却申請できません。'
            })
    
    @property
    def is_pending(self):
        """Check if return request is pending."""
        return self.status == 'PENDING'
    
    @property
    def is_completed(self):
        """Check if return request is completed."""
        return self.status == 'COMPLETED'
    
    def approve(self, approved_by, notes=None):
        """Approve the return request."""
        if self.status != 'PENDING':
            raise ValidationError('処理待ち以外のリクエストは承認できません。')
        
        self.status = 'APPROVED'
        self.processed_by = approved_by
        self.processed_at = timezone.now()
        
        if notes:
            self.admin_notes = f"{self.admin_notes}\n承認メモ: {notes}" if self.admin_notes else f"承認メモ: {notes}"
        
        self.save(update_fields=['status', 'processed_by', 'processed_at', 'admin_notes', 'updated_at'])
        return self
    
    def complete(self, completed_by, actual_return_date=None, notes=None):
        """Complete the return request and process the actual return."""
        if self.status not in ['PENDING', 'APPROVED']:
            raise ValidationError('処理待ちまたは承認済み以外のリクエストは完了できません。')
        
        if actual_return_date is None:
            actual_return_date = timezone.now().date()
        
        self.status = 'COMPLETED'
        self.processed_by = completed_by
        self.processed_at = timezone.now()
        self.actual_return_date = actual_return_date
        
        if notes:
            self.admin_notes = f"{self.admin_notes}\n完了メモ: {notes}" if self.admin_notes else f"完了メモ: {notes}"
        
        # Process the actual return
        if self.device_assignment:
            self.device_assignment.device.return_from_employee(
                return_date=actual_return_date,
                returned_by=completed_by,
                notes=f"返却申請経由: {self.return_reason}"
            )
        
        if self.license_assignment:
            self.license_assignment.revoke(
                revoked_by=completed_by,
                notes=f"返却申請経由: {self.return_reason}"
            )
        
        self.save(update_fields=[
            'status', 'processed_by', 'processed_at', 'actual_return_date', 
            'admin_notes', 'updated_at'
        ])
        return self
    
    def cancel(self, cancelled_by=None, reason=None):
        """Cancel the return request."""
        if self.status == 'COMPLETED':
            raise ValidationError('完了済みのリクエストはキャンセルできません。')
        
        self.status = 'CANCELLED'
        
        if reason:
            self.notes = f"{self.notes}\nキャンセル理由: {reason}" if self.notes else f"キャンセル理由: {reason}"
        
        self.save(update_fields=['status', 'notes', 'updated_at'])
        return self


class Notification(models.Model):
    """
    Model for tracking notifications and alerts sent to users.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('LICENSE_EXPIRY', 'ライセンス期限切れ'),
        ('ASSIGNMENT_EXPIRY', 'ライセンス割当期限切れ'),
        ('DEVICE_OVERDUE', '端末返却期限超過'),
        ('REQUEST_APPROVED', 'リクエスト承認'),
        ('REQUEST_REJECTED', 'リクエスト却下'),
        ('SYSTEM_ALERT', 'システムアラート'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '未送信'),
        ('SENT', '送信済み'),
        ('READ', '既読'),
        ('DISMISSED', '無視'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', '低'),
        ('MEDIUM', '中'),
        ('HIGH', '高'),
        ('CRITICAL', '緊急'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="通知対象社員"
    )
    
    # Notification details
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="通知種別"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="通知タイトル"
    )
    
    message = models.TextField(
        help_text="通知メッセージ"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        help_text="優先度"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="ステータス"
    )
    
    # Related objects (optional)
    related_license = models.ForeignKey(
        'licenses.License',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="関連ライセンス"
    )
    
    related_device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="関連端末"
    )
    
    related_request = models.ForeignKey(
        ResourceRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="関連リソース申請"
    )
    
    # Timing
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        help_text="送信予定日時"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="送信日時"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="既読日時"
    )
    
    dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="無視日時"
    )
    
    # Additional data
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="追加データ"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['priority', 'scheduled_at']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.title} ({self.get_status_display()})"
    
    @property
    def is_pending(self):
        """Check if notification is pending."""
        return self.status == 'PENDING'
    
    @property
    def is_sent(self):
        """Check if notification has been sent."""
        return self.status in ['SENT', 'READ', 'DISMISSED']
    
    @property
    def is_read(self):
        """Check if notification has been read."""
        return self.status in ['READ', 'DISMISSED']
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        if self.status == 'PENDING':
            self.status = 'SENT'
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at', 'updated_at'])
        return self
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status == 'SENT':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])
        return self
    
    def dismiss(self):
        """Dismiss notification."""
        if self.status in ['SENT', 'READ']:
            self.status = 'DISMISSED'
            self.dismissed_at = timezone.now()
            self.save(update_fields=['status', 'dismissed_at', 'updated_at'])
        return self