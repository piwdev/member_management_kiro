"""
カスタム認証バックエンド
LDAP認証とセキュリティログ機能を統合
"""
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django_auth_ldap.backend import LDAPBackend
from .models import LoginAttempt

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomLDAPBackend(LDAPBackend):
    """
    カスタムLDAP認証バックエンド
    セキュリティログ機能を追加
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """認証処理（セキュリティログ付き）"""
        if username is None or password is None:
            return None
        
        # アカウントロック状態をチェック
        try:
            user = User.objects.get(username=username)
            if user.is_account_locked:
                logger.warning(f"Login attempt for locked account: {username}")
                return None
        except User.DoesNotExist:
            pass
        
        # LDAP認証を実行
        user = super().authenticate(request, username, password, **kwargs)
        
        if user:
            logger.info(f"LDAP authentication successful for user: {username}")
            # LDAP認証成功時にユーザー情報を更新
            self._update_user_from_ldap(user)
        else:
            logger.warning(f"LDAP authentication failed for user: {username}")
        
        return user
    
    def _update_user_from_ldap(self, user):
        """LDAP情報からユーザー情報を更新"""
        try:
            # LDAPから取得した情報でユーザーを更新
            if hasattr(user, 'ldap_user') and user.ldap_user:
                # LDAP DNを保存
                user.ldap_dn = user.ldap_user.dn
                
                # 部署情報の更新
                if hasattr(user.ldap_user, 'attrs') and 'department' in user.ldap_user.attrs:
                    departments = user.ldap_user.attrs.get('department', [])
                    if departments:
                        user.department = departments[0]
                
                # 役職情報の更新
                if hasattr(user.ldap_user, 'attrs') and 'title' in user.ldap_user.attrs:
                    titles = user.ldap_user.attrs.get('title', [])
                    if titles:
                        user.position = titles[0]
                
                # 社員IDの更新
                if hasattr(user.ldap_user, 'attrs') and 'employeeNumber' in user.ldap_user.attrs:
                    employee_numbers = user.ldap_user.attrs.get('employeeNumber', [])
                    if employee_numbers:
                        user.employee_id = employee_numbers[0]
                
                user.save()
                logger.info(f"Updated user {user.username} from LDAP data")
        
        except Exception as e:
            logger.error(f"Error updating user {user.username} from LDAP: {str(e)}")


class CustomModelBackend(ModelBackend):
    """
    カスタムモデル認証バックエンド
    フォールバック用（LDAP認証が失敗した場合）
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """認証処理（セキュリティログ付き）"""
        if username is None or password is None:
            return None
        
        # アカウントロック状態をチェック
        try:
            user = User.objects.get(username=username)
            if user.is_account_locked:
                logger.warning(f"Login attempt for locked account: {username}")
                return None
        except User.DoesNotExist:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return None
        
        # モデル認証を実行
        user = super().authenticate(request, username, password, **kwargs)
        
        if user:
            logger.info(f"Model authentication successful for user: {username}")
        else:
            logger.warning(f"Model authentication failed for user: {username}")
        
        return user