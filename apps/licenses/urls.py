"""
URL configuration for licenses app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LicenseViewSet, LicenseAssignmentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'licenses', LicenseViewSet, basename='license')
router.register(r'assignments', LicenseAssignmentViewSet, basename='license-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
