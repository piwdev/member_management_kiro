from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    
    # Usage statistics endpoints
    path('usage-statistics/', views.usage_statistics, name='usage-statistics'),
    path('inventory-status/', views.inventory_status, name='inventory-status'),
    path('cost-analysis/', views.cost_analysis, name='cost-analysis'),
    path('department-usage/', views.department_usage, name='department-usage'),
    path('position-usage/', views.position_usage, name='position-usage'),
    
    # Export endpoint
    path('export/', views.export_report, name='export-report'),
]
