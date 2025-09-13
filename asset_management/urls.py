"""
URL configuration for asset_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/employees/', include('apps.employees.urls')),
    path('api/devices/', include('apps.devices.urls')),
    path('api/licenses/', include('apps.licenses.urls')),
    path('api/permissions/', include('apps.permissions.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/', include('apps.dashboard.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs in development
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
