"""
URL configuration for permissions app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PermissionPolicyViewSet, PermissionOverrideViewSet, 
    PermissionAuditLogViewSet, PermissionCheckViewSet
)

router = DefaultRouter()
router.register(r'policies', PermissionPolicyViewSet)
router.register(r'overrides', PermissionOverrideViewSet)
router.register(r'audit-logs', PermissionAuditLogViewSet)
router.register(r'check', PermissionCheckViewSet, basename='permission-check')

urlpatterns = [
    path('', include(router.urls)),
]