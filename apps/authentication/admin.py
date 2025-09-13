from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, LoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """カスタムユーザー管理画面"""
    list_display = [
        'username', 'email', 'get_full_name', 'employee_id', 
        'department', 'position', 'location', 'is_active', 
        'is_staff', 'account_status', 'last_login'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'location', 
        'department', 'date_joined'
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 
        'employee_id', 'department'
    ]
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('社員情報', {
            'fields': ('employee_id', 'department', 'position', 'location')
        }),
        ('LDAP情報', {
            'fields': ('ldap_dn',)
        }),
        ('セキュリティ', {
            'fields': (
                'failed_login_attempts', 'account_locked_until', 
                'last_password_change'
            )
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def account_status(self, obj):
        """アカウント状態表示"""
        if obj.is_account_locked:
            return format_html(
                '<span style="color: red;">🔒 ロック中</span>'
            )
        elif obj.failed_login_attempts > 0:
            return format_html(
                '<span style="color: orange;">⚠️ 失敗 {}回</span>',
                obj.failed_login_attempts
            )
        return format_html('<span style="color: green;">✅ 正常</span>')
    
    account_status.short_description = 'アカウント状態'
    
    def get_full_name(self, obj):
        """フルネーム表示"""
        return obj.get_full_name() or '-'
    
    get_full_name.short_description = '氏名'
    
    actions = ['unlock_accounts', 'reset_failed_attempts']
    
    def unlock_accounts(self, request, queryset):
        """選択したアカウントのロックを解除"""
        count = 0
        for user in queryset:
            if user.is_account_locked:
                user.unlock_account()
                count += 1
        
        self.message_user(
            request, 
            f'{count}個のアカウントのロックを解除しました。'
        )
    
    unlock_accounts.short_description = 'アカウントロックを解除'
    
    def reset_failed_attempts(self, request, queryset):
        """失敗回数をリセット"""
        count = queryset.filter(failed_login_attempts__gt=0).update(
            failed_login_attempts=0
        )
        self.message_user(
            request, 
            f'{count}個のアカウントの失敗回数をリセットしました。'
        )
    
    reset_failed_attempts.short_description = 'ログイン失敗回数をリセット'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """ログイン試行履歴管理画面"""
    list_display = [
        'username', 'user_display', 'ip_address', 'success_status', 
        'failure_reason', 'timestamp'
    ]
    list_filter = [
        'success', 'failure_reason', 'timestamp'
    ]
    search_fields = [
        'username', 'user__first_name', 'user__last_name', 
        'ip_address', 'user_agent'
    ]
    ordering = ['-timestamp']
    readonly_fields = [
        'user', 'username', 'ip_address', 'user_agent', 
        'success', 'failure_reason', 'timestamp'
    ]
    
    def has_add_permission(self, request):
        """追加権限なし（システムが自動生成）"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """変更権限なし（ログは変更不可）"""
        return False
    
    def user_display(self, obj):
        """ユーザー表示名"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return '-'
    
    user_display.short_description = 'ユーザー'
    
    def success_status(self, obj):
        """成功状態表示"""
        if obj.success:
            return format_html('<span style="color: green;">✅ 成功</span>')
        return format_html('<span style="color: red;">❌ 失敗</span>')
    
    success_status.short_description = '結果'
