"""
Authentication models for the asset management system.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Integrates with LDAP and includes additional fields for asset management.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="社員ID (Employee ID)"
    )
    department = models.CharField(
        max_length=100, 
        blank=True,
        help_text="部署 (Department)"
    )
    position = models.CharField(
        max_length=100, 
        blank=True,
        help_text="役職 (Position)"
    )
    
    LOCATION_CHOICES = [
        ('TOKYO', '東京'),
        ('OKINAWA', '沖縄'),
        ('REMOTE', 'リモート'),
    ]
    
    location = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
        blank=True,
        help_text="勤務地 (Work Location)"
    )
    
    hire_date = models.DateField(
        null=True, 
        blank=True,
        help_text="入社日 (Hire Date)"
    )
    
    phone_number = models.CharField(
        max_length=20, 
        blank=True,
        help_text="電話番号 (Phone Number)"
    )
    
    # LDAP integration fields
    ldap_dn = models.CharField(
        max_length=255, 
        blank=True,
        help_text="LDAP Distinguished Name"
    )
    
    # Authentication tracking
    last_login_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="最終ログインIP (Last Login IP)"
    )
    
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="ログイン失敗回数 (Failed Login Attempts)"
    )
    
    account_locked_until = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="アカウントロック期限 (Account Locked Until)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        ordering = ['username']
    
    def __str__(self):
        if self.get_full_name():
            return f"{self.username} ({self.get_full_name()})"
        return self.username
    
    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock the account for specified duration."""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock the account and reset failed attempts."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
        
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])


class LoginAttempt(models.Model):
    """
    Model to track login attempts for security monitoring.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='login_attempts'
    )
    username = models.CharField(max_length=150)  # Store even if user doesn't exist
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_login_attempts'
        verbose_name = 'ログイン試行'
        verbose_name_plural = 'ログイン試行'
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "成功" if self.success else "失敗"
        return f"{self.username} - {status} ({self.timestamp})"


class RegistrationAttempt(models.Model):
    """
    Model to track registration attempts for security monitoring.
    """
    
    username = models.CharField(max_length=150)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_user = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='registration_attempts'
    )
    
    class Meta:
        db_table = 'auth_registration_attempts'
        verbose_name = '登録試行'
        verbose_name_plural = '登録試行'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['email', 'timestamp']),
        ]
    
    def __str__(self):
        status = "成功" if self.success else "失敗"
        return f"{self.username} ({self.email}) - {status} ({self.timestamp})"