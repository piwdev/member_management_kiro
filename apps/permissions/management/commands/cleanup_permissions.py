"""
Management command to clean up expired permissions and audit logs.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from apps.permissions.models import PermissionOverride, PermissionAuditLog


class Command(BaseCommand):
    help = 'Clean up expired permission overrides and old audit logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--audit-log-days',
            type=int,
            default=365,
            help='Keep audit logs for specified number of days (default: 365)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        audit_log_days = options['audit_log_days']
        force = options['force']
        
        today = timezone.now().date()
        audit_cutoff = timezone.now() - timedelta(days=audit_log_days)
        
        # Find expired overrides
        expired_overrides = PermissionOverride.objects.filter(
            is_active=True,
            effective_until__lt=today
        )
        
        # Find old audit logs
        old_audit_logs = PermissionAuditLog.objects.filter(
            timestamp__lt=audit_cutoff
        )
        
        expired_count = expired_overrides.count()
        audit_count = old_audit_logs.count()
        
        self.stdout.write(f'Found {expired_count} expired permission overrides')
        self.stdout.write(f'Found {audit_count} audit logs older than {audit_log_days} days')
        
        if expired_count == 0 and audit_count == 0:
            self.stdout.write(self.style.SUCCESS('Nothing to clean up'))
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            
            if expired_count > 0:
                self.stdout.write('Would deactivate expired overrides:')
                for override in expired_overrides[:10]:  # Show first 10
                    self.stdout.write(
                        f'  - {override.employee.name}: {override.resource_identifier} '
                        f'(expired: {override.effective_until})'
                    )
                if expired_count > 10:
                    self.stdout.write(f'  ... and {expired_count - 10} more')
            
            if audit_count > 0:
                self.stdout.write(f'Would delete {audit_count} old audit log entries')
            
            return
        
        # Confirm before proceeding
        if not force:
            if expired_count > 0:
                confirm = input(f'Deactivate {expired_count} expired overrides? [y/N]: ')
                if confirm.lower() != 'y':
                    self.stdout.write('Skipping expired overrides cleanup')
                    expired_count = 0
            
            if audit_count > 0:
                confirm = input(f'Delete {audit_count} old audit logs? [y/N]: ')
                if confirm.lower() != 'y':
                    self.stdout.write('Skipping audit logs cleanup')
                    audit_count = 0
        
        # Perform cleanup
        with transaction.atomic():
            cleaned_overrides = 0
            cleaned_logs = 0
            
            # Deactivate expired overrides
            if expired_count > 0:
                cleaned_overrides = expired_overrides.update(is_active=False)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deactivated {cleaned_overrides} expired permission overrides'
                    )
                )
            
            # Delete old audit logs
            if audit_count > 0:
                deleted_info = old_audit_logs.delete()
                cleaned_logs = deleted_info[0]
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {cleaned_logs} old audit log entries'
                    )
                )
            
            # Log the cleanup operation
            if cleaned_overrides > 0 or cleaned_logs > 0:
                PermissionAuditLog.objects.create(
                    action='AUTO_UPDATE',
                    details={
                        'action': 'cleanup_permissions',
                        'expired_overrides_cleaned': cleaned_overrides,
                        'audit_logs_cleaned': cleaned_logs,
                        'audit_log_cutoff_days': audit_log_days,
                        'command': 'cleanup_permissions'
                    }
                )
        
        self.stdout.write(
            self.style.SUCCESS('Cleanup completed successfully')
        )