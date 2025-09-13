"""
Management command to generate cost analysis reports.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.reports.services import ReportService
import json


class Command(BaseCommand):
    help = 'Generate cost analysis report'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--department',
            type=str,
            help='Filter by department'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Generating cost analysis report...')
        
        # Prepare filters
        filters = {}
        if options['department']:
            filters['department'] = options['department']
        if options['start_date']:
            filters['start_date'] = options['start_date']
        if options['end_date']:
            filters['end_date'] = options['end_date']
        
        try:
            # Generate report
            report_data = ReportService.get_cost_analysis(filters)
            
            # Output results
            if options['output']:
                with open(options['output'], 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
                self.stdout.write(
                    self.style.SUCCESS(f'Report saved to {options["output"]}')
                )
            else:
                # Print summary to console
                self._print_summary(report_data)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to generate report: {e}')
            )
    
    def _print_summary(self, report_data):
        """Print report summary to console."""
        self.stdout.write('\n=== Cost Analysis Report ===')
        
        # Department costs summary
        if report_data['department_costs']:
            self.stdout.write('\nDepartment Costs:')
            total_monthly = 0
            total_yearly = 0
            
            for dept, costs in report_data['department_costs'].items():
                self.stdout.write(
                    f'  {dept}: ¥{costs["monthly_cost"]:,.0f}/month, '
                    f'¥{costs["yearly_cost"]:,.0f}/year '
                    f'({costs["employee_count"]} employees)'
                )
                total_monthly += costs['monthly_cost']
                total_yearly += costs['yearly_cost']
            
            self.stdout.write(f'\nTotal: ¥{total_monthly:,.0f}/month, ¥{total_yearly:,.0f}/year')
        
        # Software costs summary
        if report_data['software_costs']:
            self.stdout.write('\nTop 5 Software Costs:')
            sorted_software = sorted(
                report_data['software_costs'].items(),
                key=lambda x: x[1]['yearly_cost'],
                reverse=True
            )[:5]
            
            for software, costs in sorted_software:
                self.stdout.write(
                    f'  {software}: ¥{costs["yearly_cost"]:,.0f}/year '
                    f'({costs["used_licenses"]}/{costs["total_licenses"]} licenses)'
                )
        
        # Budget comparison
        if report_data['budget_comparison']:
            self.stdout.write('\nBudget Comparison:')
            for dept, comparison in report_data['budget_comparison'].items():
                status_color = self.style.ERROR if comparison['status'] == 'OVER_BUDGET' else self.style.SUCCESS
                self.stdout.write(
                    f'  {dept}: {status_color(comparison["status"])} '
                    f'({comparison["variance_percentage"]:+.1f}%)'
                )
        
        self.stdout.write(f'\nGenerated at: {report_data["generated_at"]}')