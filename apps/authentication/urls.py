from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, logout_view, me_view, change_password_view,
    UserViewSet, LoginAttemptViewSet
)

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'login-attempts', LoginAttemptViewSet)

urlpatterns = [
    # JWT Authentication endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
    
    # User management endpoints
    path('me/', me_view, name='me'),
    path('change-password/', change_password_view, name='change_password'),
    
    # Admin endpoints
    path('', include(router.urls)),
]
