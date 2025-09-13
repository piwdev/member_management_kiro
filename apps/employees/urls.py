"""
URL configuration for employee management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, EmployeeHistoryViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'employee-history', EmployeeHistoryViewSet, basename='employee-history')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Add app name for namespacing
app_name = 'employees'
