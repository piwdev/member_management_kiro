"""
Report models for the asset management system.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class ReportCache(models.Model):
    """
    Model to cache report data for performance optimization.
    """
    
    REPORT_TYPE_CHOICES = [
        ('USAGE_STATS', '利用状況統計'),
        ('INVENTORY_STATUS', '在庫状況'),
        ('COST_ANALYSIS', 'コスト分析'),
        ('DEPARTMENT_USAGE', '部署別利用状況'),
        ('POSITION_USAGE', '役職別利用状況'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        help_text="レポート種別"
    )
    
    report_key = models.CharField(
        max_length=200,
        help_text="レポートキー（パラメータのハッシュ）"
    )
    
    data = models.JSONField(
        help_text="キャッシュされたレポートデータ"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="キャッシュ有効期限"
    )
    
    class Meta:
        db_table = 'report_cache'
        verbose_name = 'レポートキャッシュ'
        verbose_name_plural = 'レポートキャッシュ'
        indexes = [
            models.Index(fields=['report_type', 'report_key']),
            models.Index(fields=['expires_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['report_type', 'report_key'],
                name='unique_report_cache'
            )
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_key}"
    
    @property
    def is_expired(self):
        """Check if cache has expired."""
        return timezone.now() > self.expires_at
    
    @classmethod
    def get_cached_data(cls, report_type, report_key):
        """Get cached data if available and not expired."""
        try:
            cache = cls.objects.get(
                report_type=report_type,
                report_key=report_key
            )
            if not cache.is_expired:
                return cache.data
            else:
                cache.delete()
                return None
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def set_cached_data(cls, report_type, report_key, data, expires_in_hours=1):
        """Set cached data with expiration."""
        expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)
        
        cache, created = cls.objects.update_or_create(
            report_type=report_type,
            report_key=report_key,
            defaults={
                'data': data,
                'expires_at': expires_at
            }
        )
        return cache
