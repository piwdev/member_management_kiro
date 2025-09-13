"""
Report services for generating usage statistics and analytics.
"""

import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q, F, Case, When, Value, IntegerField
from django.utils import timezone
from django.core.cache import cache
from apps.employees.models import Employee
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment
from .models import ReportCache


class ReportService:
    """Service class for generating various reports and analytics."""
    
    @staticmethod
    def _generate_cache_key(report_type, filters):
        """Generate a cache key based on report type and filters."""
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        return hashlib.md5(f"{report_type}_{filter_str}".encode()).hexdigest()
    
    @staticmethod
    def _get_date_range(filters):
        """Extract and validate date range from filters."""
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
            
        return start_date, end_date
    
    @classmethod
    def get_usage_statistics(cls, filters=None):
        """
        Generate usage statistics report with department, position, and period analysis.
        """
        if filters is None:
            filters = {}
        
        # Check cache first
        cache_key = cls._generate_cache_key('USAGE_STATS', filters)
        cached_data = ReportCache.get_cached_data('USAGE_STATS', cache_key)
        if cached_data:
            return cached_data
        
        start_date, end_date = cls._get_date_range(filters)
        department_filter = filters.get('department')
        position_filter = filters.get('position')
        
        # Base employee queryset
        employee_qs = Employee.objects.filter(status='ACTIVE')
        if department_filter:
            employee_qs = employee_qs.filter(department=department_filter)
        if position_filter:
            employee_qs = employee_qs.filter(position=position_filter)
        
        # Department statistics
        department_stats = cls._get_department_usage_stats(employee_qs, start_date, end_date)
        
        # Position statistics
        position_stats = cls._get_position_usage_stats(employee_qs, start_date, end_date)
        
        # Device usage statistics
        device_usage = cls._get_device_usage_stats(start_date, end_date, department_filter, position_filter)
        
        # License usage statistics
        license_usage = cls._get_license_usage_stats(start_date, end_date, department_filter, position_filter)
        
        # Period summary
        period_summary = cls._get_period_summary(start_date, end_date)
        
        report_data = {
            'department_stats': department_stats,
            'position_stats': position_stats,
            'device_usage': device_usage,
            'license_usage': license_usage,
            'period_summary': period_summary,
            'generated_at': timezone.now().isoformat(),
            'filters': filters
        }
        
        # Cache the result
        ReportCache.set_cached_data('USAGE_STATS', cache_key, report_data, expires_in_hours=1)
        
        return report_data
    
    @classmethod
    def _get_department_usage_stats(cls, employee_qs, start_date, end_date):
        """Get usage statistics by department."""
        department_stats = {}
        
        departments = employee_qs.values_list('department', flat=True).distinct()
        
        for dept in departments:
            dept_employees = employee_qs.filter(department=dept)
            
            # Device assignments in period
            device_assignments = DeviceAssignment.objects.filter(
                Q(actual_return_date__gte=start_date) | Q(actual_return_date__isnull=True),
                employee__in=dept_employees,
                assigned_date__lte=end_date
            )
            
            # License assignments in period
            license_assignments = LicenseAssignment.objects.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                employee__in=dept_employees,
                start_date__lte=end_date
            )
            
            department_stats[dept] = {
                'employee_count': dept_employees.count(),
                'device_assignments': device_assignments.count(),
                'license_assignments': license_assignments.count(),
                'unique_devices': device_assignments.values('device').distinct().count(),
                'unique_licenses': license_assignments.values('license').distinct().count(),
                'avg_devices_per_employee': round(
                    device_assignments.count() / max(dept_employees.count(), 1), 2
                ),
                'avg_licenses_per_employee': round(
                    license_assignments.count() / max(dept_employees.count(), 1), 2
                )
            }
        
        return department_stats
    
    @classmethod
    def _get_position_usage_stats(cls, employee_qs, start_date, end_date):
        """Get usage statistics by position."""
        position_stats = {}
        
        positions = employee_qs.values_list('position', flat=True).distinct()
        
        for pos in positions:
            pos_employees = employee_qs.filter(position=pos)
            
            # Device assignments in period
            device_assignments = DeviceAssignment.objects.filter(
                Q(actual_return_date__gte=start_date) | Q(actual_return_date__isnull=True),
                employee__in=pos_employees,
                assigned_date__lte=end_date
            )
            
            # License assignments in period
            license_assignments = LicenseAssignment.objects.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                employee__in=pos_employees,
                start_date__lte=end_date
            )
            
            position_stats[pos] = {
                'employee_count': pos_employees.count(),
                'device_assignments': device_assignments.count(),
                'license_assignments': license_assignments.count(),
                'unique_devices': device_assignments.values('device').distinct().count(),
                'unique_licenses': license_assignments.values('license').distinct().count(),
                'avg_devices_per_employee': round(
                    device_assignments.count() / max(pos_employees.count(), 1), 2
                ),
                'avg_licenses_per_employee': round(
                    license_assignments.count() / max(pos_employees.count(), 1), 2
                )
            }
        
        return position_stats
    
    @classmethod
    def _get_device_usage_stats(cls, start_date, end_date, department_filter=None, position_filter=None):
        """Get device usage statistics."""
        # Base queryset for device assignments
        assignments_qs = DeviceAssignment.objects.filter(
            Q(actual_return_date__gte=start_date) | Q(actual_return_date__isnull=True),
            assigned_date__lte=end_date
        )
        
        # Apply filters
        if department_filter:
            assignments_qs = assignments_qs.filter(employee__department=department_filter)
        if position_filter:
            assignments_qs = assignments_qs.filter(employee__position=position_filter)
        
        # Device type usage
        device_type_usage = assignments_qs.values('device__type').annotate(
            count=Count('id'),
            unique_devices=Count('device', distinct=True)
        ).order_by('-count')
        
        # Most used devices
        popular_devices = assignments_qs.values(
            'device__manufacturer', 'device__model', 'device__type'
        ).annotate(
            assignment_count=Count('id')
        ).order_by('-assignment_count')[:10]
        
        # Assignment duration analysis
        returned_assignments = assignments_qs.filter(actual_return_date__isnull=False)
        avg_assignment_duration = 0
        if returned_assignments.exists():
            durations = [
                (assignment.actual_return_date - assignment.assigned_date).days
                for assignment in returned_assignments
            ]
            avg_assignment_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'device_type_usage': list(device_type_usage),
            'popular_devices': list(popular_devices),
            'total_assignments': assignments_qs.count(),
            'active_assignments': assignments_qs.filter(status='ACTIVE').count(),
            'avg_assignment_duration_days': round(avg_assignment_duration, 1)
        }
    
    @classmethod
    def _get_license_usage_stats(cls, start_date, end_date, department_filter=None, position_filter=None):
        """Get license usage statistics."""
        # Base queryset for license assignments
        assignments_qs = LicenseAssignment.objects.filter(
            Q(end_date__gte=start_date) | Q(end_date__isnull=True),
            start_date__lte=end_date
        )
        
        # Apply filters
        if department_filter:
            assignments_qs = assignments_qs.filter(employee__department=department_filter)
        if position_filter:
            assignments_qs = assignments_qs.filter(employee__position=position_filter)
        
        # Software usage
        software_usage = assignments_qs.values('license__software_name').annotate(
            assignment_count=Count('id'),
            unique_employees=Count('employee', distinct=True)
        ).order_by('-assignment_count')
        
        # License type usage
        license_type_usage = assignments_qs.values('license__license_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'software_usage': list(software_usage),
            'license_type_usage': list(license_type_usage),
            'total_assignments': assignments_qs.count(),
            'active_assignments': assignments_qs.filter(status='ACTIVE').count()
        }
    
    @classmethod
    def _get_period_summary(cls, start_date, end_date):
        """Get summary statistics for the specified period."""
        # New assignments in period
        new_device_assignments = DeviceAssignment.objects.filter(
            assigned_date__range=[start_date, end_date]
        ).count()
        
        new_license_assignments = LicenseAssignment.objects.filter(
            assigned_date__range=[start_date, end_date]
        ).count()
        
        # Returns in period
        device_returns = DeviceAssignment.objects.filter(
            actual_return_date__range=[start_date, end_date]
        ).count()
        
        license_revocations = LicenseAssignment.objects.filter(
            end_date__range=[start_date, end_date],
            status__in=['EXPIRED', 'REVOKED']
        ).count()
        
        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'new_device_assignments': new_device_assignments,
            'new_license_assignments': new_license_assignments,
            'device_returns': device_returns,
            'license_revocations': license_revocations,
            'net_device_change': new_device_assignments - device_returns,
            'net_license_change': new_license_assignments - license_revocations
        }
    
    @classmethod
    def get_inventory_status(cls, filters=None):
        """
        Generate inventory status report with utilization rates and shortage predictions.
        """
        if filters is None:
            filters = {}
        
        # Check cache first
        cache_key = cls._generate_cache_key('INVENTORY_STATUS', filters)
        cached_data = ReportCache.get_cached_data('INVENTORY_STATUS', cache_key)
        if cached_data:
            return cached_data
        
        device_type_filter = filters.get('device_type')
        software_name_filter = filters.get('software_name')
        
        # Device inventory
        device_inventory = cls._get_device_inventory(device_type_filter)
        
        # License inventory
        license_inventory = cls._get_license_inventory(software_name_filter)
        
        # Utilization rates
        utilization_rates = cls._get_utilization_rates(device_type_filter, software_name_filter)
        
        # Shortage predictions
        shortage_predictions = cls._get_shortage_predictions()
        
        report_data = {
            'device_inventory': device_inventory,
            'license_inventory': license_inventory,
            'utilization_rates': utilization_rates,
            'shortage_predictions': shortage_predictions,
            'generated_at': timezone.now().isoformat(),
            'filters': filters
        }
        
        # Cache the result
        ReportCache.set_cached_data('INVENTORY_STATUS', cache_key, report_data, expires_in_hours=2)
        
        return report_data
    
    @classmethod
    def _get_device_inventory(cls, device_type_filter=None):
        """Get device inventory statistics."""
        devices_qs = Device.objects.all()
        if device_type_filter:
            devices_qs = devices_qs.filter(type=device_type_filter)
        
        # Status breakdown
        status_breakdown = devices_qs.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Type breakdown
        type_breakdown = devices_qs.values('type').annotate(
            total=Count('id'),
            available=Count(Case(When(status='AVAILABLE', then=1), output_field=IntegerField())),
            assigned=Count(Case(When(status='ASSIGNED', then=1), output_field=IntegerField())),
            maintenance=Count(Case(When(status='MAINTENANCE', then=1), output_field=IntegerField()))
        ).order_by('type')
        
        return {
            'total_devices': devices_qs.count(),
            'status_breakdown': list(status_breakdown),
            'type_breakdown': list(type_breakdown)
        }
    
    @classmethod
    def _get_license_inventory(cls, software_name_filter=None):
        """Get license inventory statistics."""
        licenses_qs = License.objects.all()
        if software_name_filter:
            licenses_qs = licenses_qs.filter(software_name__icontains=software_name_filter)
        
        # License utilization
        license_stats = []
        for license in licenses_qs:
            license_stats.append({
                'software_name': license.software_name,
                'license_type': license.license_type,
                'total_count': license.total_count,
                'used_count': license.used_count,
                'available_count': license.available_count,
                'utilization_percentage': license.usage_percentage,
                'is_fully_utilized': license.is_fully_utilized,
                'expires_soon': license.is_expiring_soon(),
                'is_expired': license.is_expired
            })
        
        # Summary statistics
        total_licenses = sum(stat['total_count'] for stat in license_stats)
        total_used = sum(stat['used_count'] for stat in license_stats)
        total_available = sum(stat['available_count'] for stat in license_stats)
        
        return {
            'license_details': license_stats,
            'summary': {
                'total_licenses': total_licenses,
                'total_used': total_used,
                'total_available': total_available,
                'overall_utilization': round((total_used / total_licenses * 100) if total_licenses > 0 else 0, 2)
            }
        }
    
    @classmethod
    def _get_utilization_rates(cls, device_type_filter=None, software_name_filter=None):
        """Calculate utilization rates for devices and licenses."""
        # Device utilization
        device_utilization = {}
        device_types = Device.objects.values_list('type', flat=True).distinct()
        
        for device_type in device_types:
            if device_type_filter and device_type != device_type_filter:
                continue
                
            total = Device.objects.filter(type=device_type).count()
            assigned = Device.objects.filter(type=device_type, status='ASSIGNED').count()
            utilization = (assigned / total * 100) if total > 0 else 0
            
            device_utilization[device_type] = {
                'total': total,
                'assigned': assigned,
                'utilization_percentage': round(utilization, 2)
            }
        
        # License utilization
        license_utilization = {}
        licenses_qs = License.objects.all()
        if software_name_filter:
            licenses_qs = licenses_qs.filter(software_name__icontains=software_name_filter)
        
        for license in licenses_qs:
            license_utilization[f"{license.software_name} ({license.license_type})"] = {
                'total': license.total_count,
                'used': license.used_count,
                'utilization_percentage': round(license.usage_percentage, 2)
            }
        
        return {
            'device_utilization': device_utilization,
            'license_utilization': license_utilization
        }
    
    @classmethod
    def _get_shortage_predictions(cls):
        """Predict potential shortages based on current trends."""
        # Simple prediction based on current utilization and growth trends
        predictions = []
        
        # Device shortage predictions
        device_types = Device.objects.values_list('type', flat=True).distinct()
        for device_type in device_types:
            total = Device.objects.filter(type=device_type).count()
            available = Device.objects.filter(type=device_type, status='AVAILABLE').count()
            
            if available <= total * 0.1:  # Less than 10% available
                predictions.append({
                    'resource_type': 'device',
                    'resource_name': device_type,
                    'current_available': available,
                    'total': total,
                    'severity': 'HIGH' if available == 0 else 'MEDIUM',
                    'recommendation': f'{device_type}の追加調達を検討してください'
                })
        
        # License shortage predictions
        for license in License.objects.all():
            if license.available_count <= license.total_count * 0.1:  # Less than 10% available
                predictions.append({
                    'resource_type': 'license',
                    'resource_name': f"{license.software_name} ({license.license_type})",
                    'current_available': license.available_count,
                    'total': license.total_count,
                    'severity': 'HIGH' if license.available_count == 0 else 'MEDIUM',
                    'recommendation': f'{license.software_name}のライセンス追加購入を検討してください'
                })
        
        return predictions
    
    @classmethod
    def get_cost_analysis(cls, filters=None):
        """
        Generate cost analysis report with department costs and software cost trends.
        """
        if filters is None:
            filters = {}
        
        # Check cache first
        cache_key = cls._generate_cache_key('COST_ANALYSIS', filters)
        cached_data = ReportCache.get_cached_data('COST_ANALYSIS', cache_key)
        if cached_data:
            return cached_data
        
        start_date, end_date = cls._get_date_range(filters)
        department_filter = filters.get('department')
        
        # Department costs
        department_costs = cls._get_department_costs(start_date, end_date, department_filter)
        
        # Software costs
        software_costs = cls._get_software_costs(start_date, end_date)
        
        # Cost trends
        cost_trends = cls._get_cost_trends(start_date, end_date)
        
        # Budget comparison (placeholder - would need budget data)
        budget_comparison = cls._get_budget_comparison(department_costs)
        
        report_data = {
            'department_costs': department_costs,
            'software_costs': software_costs,
            'cost_trends': cost_trends,
            'budget_comparison': budget_comparison,
            'generated_at': timezone.now().isoformat(),
            'filters': filters
        }
        
        # Cache the result
        ReportCache.set_cached_data('COST_ANALYSIS', cache_key, report_data, expires_in_hours=2)
        
        return report_data
    
    @classmethod
    def _get_department_costs(cls, start_date, end_date, department_filter=None):
        """Calculate costs by department."""
        department_costs = {}
        
        # Get all departments or filter by specific department
        if department_filter:
            departments = [department_filter]
        else:
            departments = Employee.objects.filter(
                status='ACTIVE'
            ).values_list('department', flat=True).distinct()
        
        for dept in departments:
            dept_employees = Employee.objects.filter(
                department=dept,
                status='ACTIVE'
            )
            
            # Get license assignments for department employees in the period
            license_assignments = LicenseAssignment.objects.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                employee__in=dept_employees,
                start_date__lte=end_date,
                status='ACTIVE'
            )
            
            # Calculate costs
            monthly_cost = Decimal('0.00')
            yearly_cost = Decimal('0.00')
            total_cost = Decimal('0.00')
            
            license_breakdown = {}
            
            for assignment in license_assignments:
                license = assignment.license
                
                # Calculate cost for this assignment
                if license.pricing_model == 'MONTHLY':
                    assignment_monthly = license.unit_price
                    assignment_yearly = license.unit_price * 12
                elif license.pricing_model == 'YEARLY':
                    assignment_monthly = license.unit_price / 12
                    assignment_yearly = license.unit_price
                else:  # PERPETUAL
                    assignment_monthly = Decimal('0.00')
                    assignment_yearly = Decimal('0.00')
                
                monthly_cost += assignment_monthly
                yearly_cost += assignment_yearly
                
                # Track by software
                software_key = f"{license.software_name} ({license.license_type})"
                if software_key not in license_breakdown:
                    license_breakdown[software_key] = {
                        'assignments': 0,
                        'monthly_cost': Decimal('0.00'),
                        'yearly_cost': Decimal('0.00'),
                        'pricing_model': license.pricing_model
                    }
                
                license_breakdown[software_key]['assignments'] += 1
                license_breakdown[software_key]['monthly_cost'] += assignment_monthly
                license_breakdown[software_key]['yearly_cost'] += assignment_yearly
            
            # Convert Decimal to float for JSON serialization
            department_costs[dept] = {
                'employee_count': dept_employees.count(),
                'license_assignments': license_assignments.count(),
                'monthly_cost': float(monthly_cost),
                'yearly_cost': float(yearly_cost),
                'avg_cost_per_employee': float(monthly_cost / max(dept_employees.count(), 1)),
                'license_breakdown': {
                    k: {
                        'assignments': v['assignments'],
                        'monthly_cost': float(v['monthly_cost']),
                        'yearly_cost': float(v['yearly_cost']),
                        'pricing_model': v['pricing_model']
                    }
                    for k, v in license_breakdown.items()
                }
            }
        
        return department_costs
    
    @classmethod
    def _get_software_costs(cls, start_date, end_date):
        """Calculate costs by software."""
        software_costs = {}
        
        # Get all active licenses
        licenses = License.objects.all()
        
        for license in licenses:
            # Get assignments in the period
            assignments = LicenseAssignment.objects.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                license=license,
                start_date__lte=end_date,
                status='ACTIVE'
            )
            
            assignment_count = assignments.count()
            
            # Calculate costs
            if license.pricing_model == 'MONTHLY':
                monthly_cost = license.unit_price * assignment_count
                yearly_cost = monthly_cost * 12
            elif license.pricing_model == 'YEARLY':
                yearly_cost = license.unit_price * assignment_count
                monthly_cost = yearly_cost / 12
            else:  # PERPETUAL
                monthly_cost = Decimal('0.00')
                yearly_cost = Decimal('0.00')
            
            software_key = f"{license.software_name} ({license.license_type})"
            software_costs[software_key] = {
                'license_id': str(license.id),
                'total_licenses': license.total_count,
                'used_licenses': assignment_count,
                'utilization_percentage': round((assignment_count / license.total_count * 100) if license.total_count > 0 else 0, 2),
                'pricing_model': license.pricing_model,
                'unit_price': float(license.unit_price),
                'monthly_cost': float(monthly_cost),
                'yearly_cost': float(yearly_cost),
                'cost_per_user': float(monthly_cost / max(assignment_count, 1)),
                'expiry_date': license.expiry_date.isoformat(),
                'is_expiring_soon': license.is_expiring_soon(),
                'departments_using': list(
                    assignments.values_list('employee__department', flat=True).distinct()
                )
            }
        
        return software_costs
    
    @classmethod
    def _get_cost_trends(cls, start_date, end_date):
        """Calculate cost trends over time."""
        # For simplicity, we'll calculate monthly trends
        trends = {}
        
        current_date = start_date
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Get active assignments for this month
            monthly_assignments = LicenseAssignment.objects.filter(
                Q(end_date__gte=month_start) | Q(end_date__isnull=True),
                start_date__lte=month_end,
                status='ACTIVE'
            )
            
            monthly_cost = Decimal('0.00')
            assignment_count = 0
            
            for assignment in monthly_assignments:
                license = assignment.license
                if license.pricing_model == 'MONTHLY':
                    monthly_cost += license.unit_price
                elif license.pricing_model == 'YEARLY':
                    monthly_cost += license.unit_price / 12
                assignment_count += 1
            
            month_key = current_date.strftime('%Y-%m')
            trends[month_key] = {
                'month': month_key,
                'total_cost': float(monthly_cost),
                'assignment_count': assignment_count,
                'avg_cost_per_assignment': float(monthly_cost / max(assignment_count, 1))
            }
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trends
    
    @classmethod
    def _get_budget_comparison(cls, department_costs):
        """Compare actual costs with budget (placeholder implementation)."""
        # In a real implementation, this would compare with actual budget data
        budget_comparison = {}
        
        for dept, costs in department_costs.items():
            # Placeholder budget calculation (e.g., 10% more than current cost)
            estimated_budget = costs['yearly_cost'] * 1.1
            variance = costs['yearly_cost'] - estimated_budget
            variance_percentage = (variance / estimated_budget * 100) if estimated_budget > 0 else 0
            
            budget_comparison[dept] = {
                'actual_cost': costs['yearly_cost'],
                'estimated_budget': estimated_budget,
                'variance': variance,
                'variance_percentage': round(variance_percentage, 2),
                'status': 'OVER_BUDGET' if variance > 0 else 'UNDER_BUDGET' if variance < 0 else 'ON_BUDGET'
            }
        
        return budget_comparison