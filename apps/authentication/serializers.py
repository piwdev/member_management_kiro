from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, LoginAttempt


class LoginSerializer(serializers.Serializer):
    """ログイン用シリアライザー"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # ユーザーの存在確認とアカウントロック状態チェック
            try:
                user = User.objects.get(username=username)
                if user.is_account_locked:
                    raise serializers.ValidationError(
                        'アカウントがロックされています。しばらく時間をおいてから再試行してください。'
                    )
            except User.DoesNotExist:
                pass  # ユーザーが存在しない場合も認証を試行

            # 認証実行
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                # 認証失敗時の処理
                self._handle_failed_login(username)
                raise serializers.ValidationError(
                    'ユーザー名またはパスワードが正しくありません。'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'このアカウントは無効化されています。'
                )

            # 認証成功時の処理
            self._handle_successful_login(user)
            attrs['user'] = user
            return attrs

        raise serializers.ValidationError(
            'ユーザー名とパスワードの両方を入力してください。'
        )

    def _handle_failed_login(self, username):
        """ログイン失敗時の処理"""
        request = self.context.get('request')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        # ログイン試行履歴を記録
        try:
            user = User.objects.get(username=username)
            user.increment_failed_login()
            LoginAttempt.objects.create(
                user=user,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='認証失敗'
            )
        except User.DoesNotExist:
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='ユーザー不存在'
            )

    def _handle_successful_login(self, user):
        """ログイン成功時の処理"""
        request = self.context.get('request')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        # ログイン成功時はアカウントロックを解除
        if user.failed_login_attempts > 0:
            user.unlock_account()

        # 最終ログイン時刻を更新
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # ログイン試行履歴を記録
        LoginAttempt.objects.create(
            user=user,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

    def _get_client_ip(self, request):
        """クライアントIPアドレスを取得"""
        if not request:
            return '127.0.0.1'
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


class UserSerializer(serializers.ModelSerializer):
    """ユーザー情報シリアライザー"""
    full_name = serializers.SerializerMethodField()
    is_account_locked = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'employee_id', 'department', 'position', 'location',
            'is_active', 'is_staff', 'is_superuser', 'is_account_locked',
            'last_login', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'last_login', 'date_joined', 
            'created_at', 'updated_at', 'is_account_locked'
        ]

    def get_full_name(self, obj):
        """フルネームを取得"""
        return obj.get_full_name() or obj.username


class ChangePasswordSerializer(serializers.Serializer):
    """パスワード変更用シリアライザー"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                'パスワードと確認用パスワードが一致しません。'
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                '現在のパスワードが正しくありません。'
            )
        return value


class LoginAttemptSerializer(serializers.ModelSerializer):
    """ログイン試行履歴シリアライザー"""
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = LoginAttempt
        fields = [
            'id', 'user', 'user_display', 'username', 'ip_address',
            'user_agent', 'success', 'failure_reason', 'timestamp'
        ]

    def get_user_display(self, obj):
        """ユーザー表示名を取得"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.username

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user information.
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Add custom claims to the JWT token.
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['employee_id'] = user.employee_id
        token['department'] = user.department
        token['position'] = user.position
        token['location'] = user.location
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        return token
    
    def validate(self, attrs):
        """
        Validate credentials and return token with user info.
        """
        # Use the LoginSerializer for validation
        login_serializer = LoginSerializer(
            data=attrs, 
            context=self.context
        )
        login_serializer.is_valid(raise_exception=True)
        
        # Get the authenticated user
        user = login_serializer.validated_data['user']
        
        # Generate tokens
        refresh = self.get_token(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }