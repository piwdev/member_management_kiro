import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.db import transaction
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import User, LoginAttempt, RegistrationAttempt
from .serializers import (
    LoginSerializer, UserSerializer, ChangePasswordSerializer, 
    LoginAttemptSerializer, UserRegistrationSerializer
)

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """カスタムJWTトークン取得ビュー"""
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.warning(
                f"Login failed for user: {request.data.get('username', 'unknown')} "
                f"from IP: {_get_client_ip(request)}"
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        logger.info(
            f"Successful login for user: {user.username} "
            f"from IP: {_get_client_ip(request)}"
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """ログアウトビュー"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        logout(request)
        logger.info(f"User {request.user.username} logged out successfully")
        
        return Response(
            {'message': 'ログアウトしました。'}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Logout error for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'ログアウト処理中にエラーが発生しました。'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@ratelimit(key='header:user-agent', rate='10/h', method='POST', block=True)
def register_view(request):
    """ユーザー登録ビュー"""
    ip_address = _get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # 登録データの取得
    username = request.data.get('username', '')
    email = request.data.get('email', '')
    
    try:
        with transaction.atomic():
            # シリアライザーでバリデーション
            serializer = UserRegistrationSerializer(data=request.data)
            
            if serializer.is_valid():
                # ユーザー作成
                user = serializer.save()
                
                # 成功時の登録試行履歴を記録
                RegistrationAttempt.objects.create(
                    username=username,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True,
                    created_user=user
                )
                
                logger.info(
                    f"Successful registration for user: {user.username} "
                    f"from IP: {ip_address}"
                )
                
                # 成功レスポンス
                return Response({
                    'message': '登録が完了しました。ログインしてください。',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            
            else:
                # バリデーションエラー時の登録試行履歴を記録
                failure_reasons = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        failure_reasons.extend([str(error) for error in errors])
                    else:
                        failure_reasons.append(str(errors))
                
                failure_reason = '; '.join(failure_reasons[:100])  # 100文字制限
                
                RegistrationAttempt.objects.create(
                    username=username,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=failure_reason
                )
                
                logger.warning(
                    f"Registration validation failed for username: {username}, "
                    f"email: {email} from IP: {ip_address}. "
                    f"Errors: {failure_reason}"
                )
                
                return Response({
                    'error': '登録に失敗しました。',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        # 予期しないエラー時の登録試行履歴を記録
        RegistrationAttempt.objects.create(
            username=username,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason=f'システムエラー: {str(e)[:90]}'
        )
        
        logger.error(
            f"Registration system error for username: {username}, "
            f"email: {email} from IP: {ip_address}. "
            f"Error: {str(e)}"
        )
        
        return Response({
            'error': 'システムエラーが発生しました。しばらく時間をおいてから再試行してください。'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ensure_csrf_cookie
def csrf_token_view(request):
    """CSRFトークン取得ビュー"""
    return Response({
        'csrfToken': get_token(request)
    })


def _get_client_ip(request):
    """クライアントIPアドレスを取得"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    """現在のユーザー情報取得ビュー"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """パスワード変更ビュー"""
    serializer = ChangePasswordSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.last_password_change = timezone.now()
        user.save()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return Response(
            {'message': 'パスワードが正常に変更されました。'}, 
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    """ユーザー管理ビューセット（管理者用）"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 検索フィルター
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                first_name__icontains=search
            ) | queryset.filter(
                last_name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                employee_id__icontains=search
            )
        
        # 部署フィルター
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department=department)
        
        # アクティブ状態フィルター
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-date_joined')

    @action(detail=True, methods=['post'])
    def unlock_account(self, request, pk=None):
        """アカウントロック解除"""
        user = self.get_object()
        user.unlock_account()
        
        logger.info(f"Account unlocked for user: {user.username} by admin: {request.user.username}")
        
        return Response(
            {'message': f'ユーザー {user.username} のアカウントロックを解除しました。'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """パスワードリセット（管理者用）"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': '新しいパスワードを入力してください。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.save()
        
        logger.info(f"Password reset for user: {user.username} by admin: {request.user.username}")
        
        return Response(
            {'message': f'ユーザー {user.username} のパスワードをリセットしました。'},
            status=status.HTTP_200_OK
        )


class LoginAttemptViewSet(ModelViewSet):
    """ログイン試行履歴ビューセット（管理者用）"""
    queryset = LoginAttempt.objects.all()
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    http_method_names = ['get']  # 読み取り専用
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # ユーザーフィルター
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username__icontains=username)
        
        # 成功/失敗フィルター
        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=success.lower() == 'true')
        
        # IPアドレスフィルター
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # 日付範囲フィルター
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset.order_by('-timestamp')
