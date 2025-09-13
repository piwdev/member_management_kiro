"""
License models for the asset management system.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

User = get_user_model()


class License(models.Model):
    """
    Software license model that tracks license information, pricing, and availability.
    """
    
    PRICING_CHOICES = [
        ('MONTHLY', '月額'),
        ('YEARLY', '年額'),
        ('PERPETUAL', '買い切り'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # License information
    software_name = models.CharField(
        max_length=200,
        help_text="ソフトウェア名"
    )
    
    license_type = models.CharField(
        max_length=100,
        help_text="ライセンス種別 (例: Standard, Professional, Enterprise)"
    )
    
    # License counts
    total_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="購入数"
    )
    
    available_count = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="利用可能数"
    )
    
    # License details
    expiry_date = models.DateField(
        help_text="有効期限"
    )
    
    license_key = models.TextField(
        blank=True,
        null=True,
        help_text="ライセンスキー"
    )
    
    usage_conditions = models.TextField(
        blank=True,
        help_text="利用条件"
    )
    
    # Pricing information
    pricing_model = models.CharField(
        max_length=20,
        choices=PRICING_CHOICES,
        help_text="課金体系"
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="単価"
    )
    
    # Vendor information
    vendor_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="ベンダー名"
    )
    
    purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text="購入日"
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        help_text="説明"
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
        related_name='created_licenses',
        help_text="作成者"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_licenses',
        help_text="更新者"
    )
    
    class Meta:
        db_table = 'licenses'
        verbose_name = 'ライセンス'
        verbose_name_plural = 'ライセンス'
        ordering = ['software_name', 'license_type']
        indexes = [
            models.Index(fields=['software_name']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['pricing_model']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(available_count__lte=models.F('total_count')),
                name='available_count_lte_total_count'
            ),
        ]
    
    def __str__(self):
        return f"{self.software_name} ({self.license_type}) - {self.available_count}/{self.total_count}"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate available_count <= total_count
        if self.available_count > self.total_count:
            raise ValidationError({
                'available_count': '利用可能数は購入数を超えることはできません。'
            })
        
        # Validate expiry_date is not in the past for new licenses
        if not self.pk and self.expiry_date and self.expiry_date < timezone.now().date():
            raise ValidationError({
                'expiry_date': '有効期限は現在の日付より後である必要があります。'
            })
    
    @property
    def used_count(self):
        """Calculate the number of licenses currently in use."""
        return self.total_count - self.available_count
    
    @property
    def usage_percentage(self):
        """Calculate the usage percentage."""
        if self.total_count == 0:
            return 0
        return (self.used_count / self.total_count) * 100
    
    @property
    def is_fully_utilized(self):
        """Check if all licenses are assigned."""
        return self.available_count == 0
    
    def is_expiring_soon(self, days=30):
        """Check if license expires within specified days."""
        if not self.expiry_date:
            return False
        return self.expiry_date <= timezone.now().date() + timezone.timedelta(days=days)
    
    @property
    def is_expired(self):
        """Check if license has expired."""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()
    
    def calculate_monthly_cost(self):
        """Calculate monthly cost based on pricing model and used licenses."""
        used_licenses = self.used_count
        
        if self.pricing_model == 'MONTHLY':
            return self.unit_price * used_licenses
        elif self.pricing_model == 'YEARLY':
            return (self.unit_price * used_licenses) / 12
        else:  # PERPETUAL
            return Decimal('0.00')
    
    def calculate_yearly_cost(self):
        """Calculate yearly cost based on pricing model and used licenses."""
        used_licenses = self.used_count
        
        if self.pricing_model == 'MONTHLY':
            return self.unit_price * used_licenses * 12
        elif self.pricing_model == 'YEARLY':
            return self.unit_price * used_licenses
        else:  # PERPETUAL
            return Decimal('0.00')
    
    def calculate_total_cost(self):
        """Calculate total cost for all purchased licenses."""
        if self.pricing_model == 'PERPETUAL':
            return self.unit_price * self.total_count
        else:
            # For subscription models, return yearly cost
            return self.calculate_yearly_cost()
    
    def can_assign(self, count=1):
        """Check if the specified number of licenses can be assigned."""
        return self.available_count >= count and not self.is_expired
    
    @transaction.atomic
    def assign_license(self, count=1):
        """
        Assign licenses by reducing available count.
        This method should be called within a transaction.
        """
        if not self.can_assign(count):
            if self.is_expired:
                raise ValidationError("期限切れのライセンスは割り当てできません。")
            else:
                raise ValidationError(f"利用可能なライセンス数が不足しています。要求: {count}, 利用可能: {self.available_count}")
        
        self.available_count -= count
        self.save(update_fields=['available_count', 'updated_at'])
    
    @transaction.atomic
    def release_license(self, count=1):
        """
        Release licenses by increasing available count.
        This method should be called within a transaction.
        """
        if self.available_count + count > self.total_count:
            raise ValidationError("解放するライセンス数が購入数を超えています。")
        
        self.available_count += count
        self.save(update_fields=['available_count', 'updated_at'])


class LicenseAssignment(models.Model):
    """
    License assignment model that tracks which licenses are assigned to which employees.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('EXPIRED', '期限切れ'),
        ('REVOKED', '取り消し'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="ライセンス"
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='license_assignments',
        help_text="社員"
    )
    
    # Assignment details
    assigned_date = models.DateField(
        default=timezone.now,
        help_text="割当日"
    )
    
    start_date = models.DateField(
        help_text="利用開始日"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="利用終了日"
    )
    
    purpose = models.TextField(
        help_text="利用目的"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="ステータス"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="備考"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_licenses',
        help_text="割当者"
    )
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_licenses',
        help_text="取り消し者"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="取り消し日時"
    )
    
    class Meta:
        db_table = 'license_assignments'
        verbose_name = 'ライセンス割当'
        verbose_name_plural = 'ライセンス割当'
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['license', 'status']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['assigned_date']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['license', 'employee'],
                condition=models.Q(status='ACTIVE'),
                name='unique_active_license_assignment'
            ),
        ]
    
    def __str__(self):
        return f"{self.license.software_name} → {self.employee.name} ({self.get_status_display()})"
    
    def clean(self):
        """Validate model data."""
        super().clean()
        
        # Validate start_date <= end_date if end_date is provided
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': '利用終了日は利用開始日より後である必要があります。'
            })
        
        # Validate employee is active
        if self.employee and not self.employee.is_active:
            raise ValidationError({
                'employee': '非アクティブな社員にはライセンスを割り当てできません。'
            })
    
    @property
    def is_active(self):
        """Check if assignment is currently active."""
        if self.status != 'ACTIVE':
            return False
        
        today = timezone.now().date()
        
        # Check if within the valid date range
        if self.start_date > today:
            return False
        
        if self.end_date and self.end_date < today:
            return False
        
        # Check if license itself is not expired
        return not self.license.is_expired
    
    def is_expiring_soon(self, days=30):
        """Check if assignment expires within specified days."""
        if not self.end_date:
            return False
        return self.end_date <= timezone.now().date() + timezone.timedelta(days=days)
    
    def calculate_usage_days(self):
        """Calculate the number of days this license has been/will be used."""
        start = self.start_date
        end = self.end_date or timezone.now().date()
        return (end - start).days + 1
    
    @transaction.atomic
    def revoke(self, revoked_by=None, notes=None):
        """
        Revoke the license assignment and release the license.
        """
        if self.status != 'ACTIVE':
            raise ValidationError("アクティブでない割当は取り消しできません。")
        
        # Update assignment status
        self.status = 'REVOKED'
        self.revoked_by = revoked_by
        self.revoked_at = timezone.now()
        self.end_date = timezone.now().date()
        
        if notes:
            self.notes = f"{self.notes}\n取り消し理由: {notes}" if self.notes else f"取り消し理由: {notes}"
        
        # Save will automatically handle license release due to status change
        self.save()
        
        return self
    
    @transaction.atomic
    def expire(self):
        """
        Mark the assignment as expired and release the license.
        This is typically called by a scheduled task.
        """
        if self.status != 'ACTIVE':
            return
        
        self.status = 'EXPIRED'
        # Save will automatically handle license release due to status change
        self.save(update_fields=['status', 'updated_at'])
        
        return self
    



# Signal handlers for license count management

@receiver(pre_save, sender=LicenseAssignment)
def store_old_license_assignment_status(sender, instance, **kwargs):
    """Store the old status before saving to track changes."""
    if instance.pk:
        try:
            old_instance = LicenseAssignment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except LicenseAssignment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=LicenseAssignment)
def handle_license_assignment_count(sender, instance, created, **kwargs):
    """Handle license count changes when assignments are created or updated."""
    if created and instance.status == 'ACTIVE':
        # New active assignment - assign license
        instance.license.assign_license(count=1)
    elif not created and hasattr(instance, '_old_status'):
        # Check for status changes
        old_status = instance._old_status
        if old_status == 'ACTIVE' and instance.status != 'ACTIVE':
            # Status changed from active to inactive - release license
            instance.license.release_license(count=1)
        elif old_status != 'ACTIVE' and instance.status == 'ACTIVE':
            # Status changed from inactive to active - assign license
            instance.license.assign_license(count=1)