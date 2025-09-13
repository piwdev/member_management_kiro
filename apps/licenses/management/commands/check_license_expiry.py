"""
Management command to check for expiring licenses and send notifications.
This command should be run daily via cron job or scheduled task.
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.licenses.models import License, LicenseAssignment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for expiring licenses and update assignment statuses'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days ahead to check for expiring licenses (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes to the database'
        )
    
    def handle(self, *args, **options):
        days_ahead = options['days']
        dry_run = options['dry_run']
        
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days_ahead)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Checking for licenses expiring within {days_ahead} days...'
            )
        )
        
        # Check for expiring licenses
        expiring_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).order_by('expiry_date')
        
        if expiring_licenses.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {expiring_licenses.count()} licenses expiring soon:'
                )
            )
            
            for license_obj in expiring_licenses:
                days_until_expiry = (license_obj.expiry_date - today).days
                self.stdout.write(
                    f'  - {license_obj.software_name} ({license_obj.license_type}): '
                    f'expires in {days_until_expiry} days ({license_obj.expiry_date})'
                )
                
                # Log the expiring license
                logger.warning(
                    f'License expiring soon: {license_obj.software_name} '
                    f'({license_obj.license_type}) expires on {license_obj.expiry_date}'
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('No licenses expiring within the specified period.')
            )
        
        # Check for expired licenses
        expired_licenses = License.objects.filter(expiry_date__lt=today)
        
        if expired_licenses.exists():
            self.stdout.write(
                self.style.ERROR(
                    f'Found {expired_licenses.count()} expired licenses:'
                )
            )
            
            for license_obj in expired_licenses:
                days_expired = (today - license_obj.expiry_date).days
                self.stdout.write(
                    f'  - {license_obj.software_name} ({license_obj.license_type}): '
                    f'expired {days_expired} days ago ({license_obj.expiry_date})'
                )
        
        # Update expired assignments
        expired_assignments = LicenseAssignment.objects.filter(
            Q(license__expiry_date__lt=today) | Q(end_date__lt=today),
            status='ACTIVE'
        )
        
        if expired_assignments.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {expired_assignments.count()} assignments to expire:'
                )
            )
            
            if not dry_run:
                expired_count = 0
                for assignment in expired_assignments:
                    try:
                        assignment.expire()
                        expired_count += 1
                        self.stdout.write(
                            f'  - Expired assignment: {assignment.license.software_name} '
                            f'for {assignment.employee.name}'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  - Failed to expire assignment {assignment.id}: {e}'
                            )
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully expired {expired_count} assignments.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Dry run mode: No assignments were actually expired.')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('No assignments need to be expired.')
            )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'  - Licenses expiring within {days_ahead} days: {expiring_licenses.count()}\n'
                f'  - Expired licenses: {expired_licenses.count()}\n'
                f'  - Assignments to expire: {expired_assignments.count()}'
            )
        )