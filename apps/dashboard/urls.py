"""
URL configuration for dashboard app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeDashboardViewSet, ResourceRequestViewSet, ReturnRequestViewSet, NotificationViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'dashboard', EmployeeDashboardViewSet, basename='employee-dashboard')
router.register(r'resource-requests', ResourceRequestViewSet, basename='resource-request')
router.register(r'return-requests', ReturnRequestViewSet, basename='return-request')
router.register(r'notifications', NotificationViewSet, basename='notification')

app_name = 'dashboard'

urlpatterns = [
    path('', include(router.urls)),
]