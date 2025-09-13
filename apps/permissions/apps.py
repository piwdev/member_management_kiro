from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.permissions'
    verbose_name = '権限管理'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        import apps.permissions.signals
