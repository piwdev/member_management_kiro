"""
Dashboard views for the asset management system.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'checks': {}
    }
    
    overall_status = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 30)
        cached_value = cache.get(cache_key)
        if cached_value == 'test':
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            raise Exception("Cache test failed")
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # Set overall status
    if not overall_status:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes deployments.
    """
    # Check if all required services are ready
    readiness_status = {
        'status': 'ready',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    overall_ready = True
    
    # Database migrations check
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            readiness_status['checks']['migrations'] = {
                'status': 'not_ready',
                'pending_migrations': len(plan)
            }
            overall_ready = False
        else:
            readiness_status['checks']['migrations'] = {'status': 'ready'}
    except Exception as e:
        readiness_status['checks']['migrations'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_ready = False
    
    # Static files check
    try:
        import os
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            readiness_status['checks']['static_files'] = {'status': 'ready'}
        else:
            readiness_status['checks']['static_files'] = {
                'status': 'not_ready',
                'error': 'Static files not collected'
            }
            overall_ready = False
    except Exception as e:
        readiness_status['checks']['static_files'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_ready = False
    
    # Set overall status
    if not overall_ready:
        readiness_status['status'] = 'not_ready'
        return Response(readiness_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(readiness_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check endpoint for Kubernetes deployments.
    """
    # Simple liveness check - just return OK if the application is running
    return Response({
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)