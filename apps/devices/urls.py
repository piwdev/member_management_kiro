"""
URL configuration for device management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DeviceViewSet, DeviceAssignmentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'device-assignments', DeviceAssignmentViewSet)

app_name = 'devices'

urlpatterns = [
    path('', include(router.urls)),
]
