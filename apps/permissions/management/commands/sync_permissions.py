"""
Management command to synchronize permissions for all employees.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.employees.models import Employee
from apps.permissions.services import PermissionService
from apps.permissions.models import PermissionAuditLog


class Command(BaseCommand):
    help = 'Synchronize permissions for all employees based on current policies'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--department',
            type=str,
            help='Only sync permissions for employees in specified department',
        )
        parser.add_argument(
            '--employee-id',
            type=str,
            help='Only sync permissions for specific employee',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        department = options['department']
        employee_id = options['employee_id']
        
        # Build queryset
        queryset = Employee.objects.filter(status='ACTIVE')
        
        if department:
            queryset = queryset.filter(department=department)
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        employees = list(queryset)
        
        if not employees:
            self.stdout.write(
                self.style.WARNING('No employees found matching criteria')
            )
            return
        
        self.stdout.write(
            f'Found {len(employees)} employees to process'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        processed = 0
        errors = 0
        
        for employee in employees:
            try:
                if dry_run:
                    # Just get permission summary without making changes
                    summary = PermissionService.get_employee_permission_summary(employee)
                    self.stdout.write(
                        f'  {employee.employee_id} ({employee.name}): '
                        f'{len(summary["applicable_policies"])} policies, '
                        f'{len(summary["active_overrides"])} overrides'
                    )
                else:
                    # Update permissions
                    with transaction.atomic():
                        PermissionService.update_employee_permissions(
                            employee=employee,
                            old_department=employee.department,
                            old_position=employee.position,
                            updated_by=None
                        )
                        
                        # Log the sync
                        PermissionAuditLog.objects.create(
                            action='AUTO_UPDATE',
                            employee=employee,
                            details={
                                'action': 'sync_permissions',
                                'command': 'sync_permissions'
                            }
                        )
                    
                    self.stdout.write(
                        f'  ✓ {employee.employee_id} ({employee.name})'
                    )
                
                processed += 1
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ {employee.employee_id} ({employee.name}): {str(e)}'
                    )
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would process {processed} employees'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'SYNC COMPLETE: Processed {processed} employees'
                )
            )
        
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )