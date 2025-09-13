"""
Management command to check for license expiry alerts and send notifications.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

from apps.licenses.models import License, LicenseAssignment
from apps.employees.models import Employee
from apps.dashboard.models import ResourceRequest, Notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to check license expiry and send alerts.
    
    This command should be run daily via cron job to:
    1. Check for licenses expiring within 30 days
    2. Check for license assignments expiring within 30 days
    3. Log alerts for admin notification
    4. Mark expired assignments
    """
    
    help = 'Check for license expiry alerts and process notifications'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days ahead to check for expiry (default: 30)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes (for testing)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        days_ahead = options['days']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days_ahead)
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Checking for license expiry alerts (looking {days_ahead} days ahead)'
                )
            )
        
        # Check for expiring licenses
        expiring_licenses = self.check_expiring_licenses(today, expiry_threshold, verbose, dry_run)
        
        # Check for expiring license assignments
        expiring_assignments = self.check_expiring_assignments(today, expiry_threshold, verbose, dry_run)
        
        # Process expired assignments
        expired_assignments = self.process_expired_assignments(today, dry_run, verbose)
        
        # Generate summary
        total_alerts = len(expiring_licenses) + len(expiring_assignments)
        
        if verbose or total_alerts > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary:'
                    f'\n- Expiring licenses: {len(expiring_licenses)}'
                    f'\n- Expiring assignments: {len(expiring_assignments)}'
                    f'\n- Expired assignments processed: {expired_assignments}'
                    f'\n- Total alerts: {total_alerts}'
                )
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes were made')
            )
        
        # Log summary for admin monitoring
        logger.info(
            f'License expiry check completed: '
            f'{len(expiring_licenses)} expiring licenses, '
            f'{len(expiring_assignments)} expiring assignments, '
            f'{expired_assignments} expired assignments processed'
        )
    
    def check_expiring_licenses(self, today, expiry_threshold, verbose, dry_run=False):
        """Check for licenses expiring within the threshold."""
        expiring_licenses = License.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        ).order_by('expiry_date')
        
        alerts = []
        
        for license_obj in expiring_licenses:
            days_until_expiry = (license_obj.expiry_date - today).days
            
            alert_info = {
                'license': license_obj,
                'days_until_expiry': days_until_expiry,
                'active_assignments': license_obj.assignments.filter(status='ACTIVE').count()
            }
            alerts.append(alert_info)
            
            if verbose:
                self.stdout.write(
                    f'License expiring: {license_obj.software_name} '
                    f'({license_obj.license_type}) - '
                    f'{days_until_expiry} days remaining '
                    f'({license_obj.expiry_date})'
                )
            
            # Log for admin notification
            logger.warning(
                f'License expiring in {days_until_expiry} days: '
                f'{license_obj.software_name} ({license_obj.license_type}) - '
                f'{alert_info["active_assignments"]} active assignments'
            )
            
            # Create notifications for affected employees (pass dry_run parameter)
            self.create_license_expiry_notifications(license_obj, days_until_expiry, dry_run)
        
        return alerts
    
    def check_expiring_assignments(self, today, expiry_threshold, verbose, dry_run=False):
        """Check for license assignments expiring within the threshold."""
        expiring_assignments = LicenseAssignment.objects.filter(
            status='ACTIVE',
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=expiry_threshold
        ).select_related('license', 'employee').order_by('end_date')
        
        alerts = []
        
        for assignment in expiring_assignments:
            days_until_expiry = (assignment.end_date - today).days
            
            alert_info = {
                'assignment': assignment,
                'days_until_expiry': days_until_expiry,
                'employee': assignment.employee,
                'license': assignment.license
            }
            alerts.append(alert_info)
            
            if verbose:
                self.stdout.write(
                    f'Assignment expiring: {assignment.employee.name} - '
                    f'{assignment.license.software_name} - '
                    f'{days_until_expiry} days remaining '
                    f'({assignment.end_date})'
                )
            
            # Log for employee and admin notification
            logger.info(
                f'License assignment expiring in {days_until_expiry} days: '
                f'{assignment.employee.name} - {assignment.license.software_name}'
            )
            
            # Create notification for employee (pass dry_run parameter)
            self.create_assignment_expiry_notification(assignment, days_until_expiry, dry_run)
        
        return alerts
    
    def process_expired_assignments(self, today, dry_run, verbose):
        """Process assignments that have already expired."""
        expired_assignments = LicenseAssignment.objects.filter(
            status='ACTIVE',
            end_date__isnull=False,
            end_date__lt=today
        ).select_related('license', 'employee')
        
        processed_count = 0
        
        for assignment in expired_assignments:
            days_overdue = (today - assignment.end_date).days
            
            if verbose:
                self.stdout.write(
                    f'Processing expired assignment: {assignment.employee.name} - '
                    f'{assignment.license.software_name} - '
                    f'{days_overdue} days overdue'
                )
            
            if not dry_run:
                try:
                    assignment.expire()
                    processed_count += 1
                    
                    logger.info(
                        f'Expired license assignment processed: '
                        f'{assignment.employee.name} - {assignment.license.software_name}'
                    )
                    
                except Exception as e:
                    logger.error(
                        f'Error processing expired assignment {assignment.id}: {str(e)}'
                    )
                    if verbose:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error processing assignment {assignment.id}: {str(e)}'
                            )
                        )
        
        return processed_count    

    def create_license_expiry_notifications(self, license_obj, days_until_expiry, dry_run=False):
        """Create notifications for employees affected by license expiry."""
        active_assignments = license_obj.assignments.filter(status='ACTIVE').select_related('employee')
        
        priority = 'CRITICAL' if days_until_expiry <= 7 else 'HIGH' if days_until_expiry <= 14 else 'MEDIUM'
        
        for assignment in active_assignments:
            # Check if notification already exists for this license and employee
            existing_notification = Notification.objects.filter(
                employee=assignment.employee,
                notification_type='LICENSE_EXPIRY',
                related_license=license_obj,
                status__in=['PENDING', 'SENT']
            ).first()
            
            if not existing_notification and not dry_run:
                Notification.objects.create(
                    employee=assignment.employee,
                    notification_type='LICENSE_EXPIRY',
                    title=f'{license_obj.software_name} ライセンス期限切れ警告',
                    message=f'{license_obj.software_name} ({license_obj.license_type}) のライセンスが{days_until_expiry}日後に期限切れになります。継続利用が必要な場合は管理者にお問い合わせください。',
                    priority=priority,
                    related_license=license_obj,
                    data={
                        'days_until_expiry': days_until_expiry,
                        'expiry_date': license_obj.expiry_date.isoformat(),
                        'assignment_id': str(assignment.id)
                    }
                )
    
    def create_assignment_expiry_notification(self, assignment, days_until_expiry, dry_run=False):
        """Create notification for assignment expiry."""
        # Check if notification already exists
        existing_notification = Notification.objects.filter(
            employee=assignment.employee,
            notification_type='ASSIGNMENT_EXPIRY',
            related_license=assignment.license,
            status__in=['PENDING', 'SENT'],
            data__assignment_id=str(assignment.id)
        ).first()
        
        if not existing_notification and not dry_run:
            priority = 'HIGH' if days_until_expiry <= 7 else 'MEDIUM'
            
            Notification.objects.create(
                employee=assignment.employee,
                notification_type='ASSIGNMENT_EXPIRY',
                title=f'{assignment.license.software_name} 利用期間終了警告',
                message=f'{assignment.license.software_name} の利用期間が{days_until_expiry}日後に終了します。継続利用が必要な場合は管理者にお問い合わせください。',
                priority=priority,
                related_license=assignment.license,
                data={
                    'days_until_end': days_until_expiry,
                    'end_date': assignment.end_date.isoformat(),
                    'assignment_id': str(assignment.id)
                }
            )