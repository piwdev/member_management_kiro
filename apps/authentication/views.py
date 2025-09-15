import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import User, LoginAttempt
from .serializers import (
    LoginSerializer, UserSerializer, ChangePasswordSerializer, 
    LoginAttemptSerializer
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
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
                f"from IP: {self._get_client_ip(request)}"
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        logger.info(
            f"Successful login for user: {user.username} "
            f"from IP: {self._get_client_ip(request)}"
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

    def _get_client_ip(self, request):
        """クライアントIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


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
