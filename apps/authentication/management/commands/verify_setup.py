"""
Management command to verify the Django project setup.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify that the Django project setup is complete and working'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Verifying Django project setup...'))
        
        # Check Django settings
        self.stdout.write('✅ Django settings loaded successfully')
        self.stdout.write(f'   - Settings module: {settings.SETTINGS_MODULE}')
        self.stdout.write(f'   - Debug mode: {settings.DEBUG}')
        self.stdout.write(f'   - Database engine: {settings.DATABASES["default"]["ENGINE"]}')
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write('✅ Database connection successful')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database connection failed: {e}'))
            return
        
        # Check installed apps
        expected_apps = [
            'apps.authentication',
            'apps.employees', 
            'apps.devices',
            'apps.licenses',
            'apps.permissions',
            'apps.reports',
            'rest_framework',
            'corsheaders',
        ]
        
        for app in expected_apps:
            if app in settings.INSTALLED_APPS:
                self.stdout.write(f'✅ App installed: {app}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ App missing: {app}'))
        
        # Check custom user model
        if settings.AUTH_USER_MODEL == 'authentication.User':
            self.stdout.write('✅ Custom user model configured')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Custom user model not configured: {settings.AUTH_USER_MODEL}'))
        
        # Check migrations
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                self.stdout.write(self.style.WARNING(f'⚠️  Unapplied migrations found: {len(plan)}'))
            else:
                self.stdout.write('✅ All migrations applied')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration check failed: {e}'))
        
        # Check if superuser exists
        try:
            if User.objects.filter(is_superuser=True).exists():
                self.stdout.write('✅ Superuser exists')
            else:
                self.stdout.write(self.style.WARNING('⚠️  No superuser found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ User model check failed: {e}'))
        
        # Check REST Framework configuration
        if hasattr(settings, 'REST_FRAMEWORK'):
            self.stdout.write('✅ Django REST Framework configured')
        else:
            self.stdout.write(self.style.ERROR('❌ Django REST Framework not configured'))
        
        # Check JWT configuration
        if hasattr(settings, 'SIMPLE_JWT'):
            self.stdout.write('✅ JWT authentication configured')
        else:
            self.stdout.write(self.style.ERROR('❌ JWT authentication not configured'))
        
        # Check CORS configuration
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            self.stdout.write('✅ CORS configuration found')
        else:
            self.stdout.write(self.style.ERROR('❌ CORS configuration missing'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Django project setup verification complete!'))
        self.stdout.write('Ready to proceed with the next implementation tasks.')