"""
Comprehensive tests for reports models, services, and API endpoints.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock
import json

from .models import Report, ReportSchedule
from .services import ReportService
from .serializers import ReportSerializer, ReportScheduleSerializer
from apps.employees.models import Employee
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment

User = get_user_model()


class ReportModelTest(TestCase):
    """Test cases for Report model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_report_creation(self):
        """Test basic report creation."""
        report = Report.objects.create(
            name='Test Report',
            report_type='USAGE',
            parameters={'department': 'IT', 'period': '30'},
            generated_by=self.user,
            file_path='/reports/test_report.pdf',
            file_size=1024
        )
        
        self.assertEqual(report.name, 'Test Report')
        self.assertEqual(report.report_type, 'USAGE')
        self.assertEqual(report.status, 'COMPLETED')
        self.assertEqual(report.generated_by, self.user)
        self.assertIsNotNone(report.generated_at)
    
    def test_report_str_representation(self):
        """Test report string representation."""
        report = Report.objects.create(
            name='Test Report',
            report_type='COST',
            generated_by=self.user
        )
        
        expected = f"Test Report (COST) - {report.generated_at}"
        self.assertEqual(str(report), expected)
    
    def test_report_file_size_validation(self):
        """Test report file size validation."""
        # Valid file size
        report = Report.objects.create(
            name='Valid Report',
            report_type='INVENTORY',
            generated_by=self.user,
            file_size=1024
        )
        self.assertEqual(report.file_size, 1024)
        
        # File size should be positive
        report.file_size = -1
        with self.assertRaises(Exception):
            report.full_clean()


class ReportScheduleModelTest(TestCase):
    """Test cases for ReportSchedule model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_schedule_creation(self):
        """Test basic schedule creation."""
        schedule = ReportSchedule.objects.create(
            name='Weekly Usage Report',
            report_type='USAGE',
            frequency='WEEKLY',
            parameters={'department': 'all'},
            created_by=self.user,
            next_run=timezone.now() + timedelta(days=7)
        )
        
        self.assertEqual(schedule.name, 'Weekly Usage Report')
        self.assertEqual(schedule.frequency, 'WEEKLY')
        self.assertTrue(schedule.is_active)
        self.assertIsNotNone(schedule.next_run)
    
    def test_schedule_validation(self):
        """Test schedule validation rules."""
        # Next run should be in the future for active schedules
        with self.assertRaises(Exception):
            schedule = ReportSchedule(
                name='Invalid Schedule',
                report_type='USAGE',
                frequency='DAILY',
                created_by=self.user,
                next_run=timezone.now() - timedelta(days=1),  # Past date
                is_active=True
            )
            schedule.full_clean()


class ReportServiceTest(TestCase):
    """Test cases for ReportService."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Create test employee
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=365)
        )
        
        # Create test device
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL001',
            purchase_date=date.today() - timedelta(days=180),
            warranty_expiry=date.today() + timedelta(days=185)
        )
        
        # Create test license
        self.license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=8,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1500.00')
        )
        
        # Create assignments
        self.device_assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=30),
            purpose='Development work',
            status='ACTIVE'
        )
        
        self.license_assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today() - timedelta(days=60),
            purpose='Office work',
            status='ACTIVE'
        )
    
    def test_generate_usage_report(self):
        """Test usage report generation."""
        parameters = {
            'start_date': (date.today() - timedelta(days=90)).isoformat(),
            'end_date': date.today().isoformat(),
            'department': 'IT'
        }
        
        report_data = ReportService.generate_usage_report(parameters)
        
        self.assertIn('summary', report_data)
        self.assertIn('device_usage', report_data)
        self.assertIn('license_usage', report_data)
        self.assertIn('department_breakdown', report_data)
        
        # Check summary data
        summary = report_data['summary']
        self.assertIn('total_devices', summary)
        self.assertIn('total_licenses', summary)
        self.assertIn('active_assignments', summary)
        
        # Should include our test data
        self.assertEqual(summary['total_devices'], 1)
        self.assertEqual(summary['total_licenses'], 1)
    
    def test_generate_cost_analysis_report(self):
        """Test cost analysis report generation."""
        parameters = {
            'start_date': (date.today() - timedelta(days=90)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        report_data = ReportService.generate_cost_analysis_report(parameters)
        
        self.assertIn('summary', report_data)
        self.assertIn('license_costs', report_data)
        self.assertIn('department_costs', report_data)
        self.assertIn('cost_trends', report_data)
        
        # Check cost calculations
        summary = report_data['summary']
        self.assertIn('total_monthly_cost', summary)
        self.assertIn('total_yearly_cost', summary)
        
        # Should include our license cost
        license_costs = report_data['license_costs']
        self.assertTrue(len(license_costs) > 0)
        office_cost = next((lc for lc in license_costs if lc['software_name'] == 'Microsoft Office'), None)
        self.assertIsNotNone(office_cost)
    
    def test_generate_inventory_report(self):
        """Test inventory report generation."""
        parameters = {
            'include_devices': True,
            'include_licenses': True,
            'location': 'TOKYO'
        }
        
        report_data = ReportService.generate_inventory_report(parameters)
        
        self.assertIn('devices', report_data)
        self.assertIn('licenses', report_data)
        self.assertIn('summary', report_data)
        
        # Check device inventory
        devices = report_data['devices']
        self.assertTrue(len(devices) > 0)
        
        # Check license inventory
        licenses = report_data['licenses']
        self.assertTrue(len(licenses) > 0)
        
        # Check summary
        summary = report_data['summary']
        self.assertIn('total_devices', summary)
        self.assertIn('available_devices', summary)
        self.assertIn('total_licenses', summary)
        self.assertIn('available_licenses', summary)
    
    def test_export_report_csv(self):
        """Test CSV report export."""
        data = {
            'summary': {'total_devices': 1, 'total_licenses': 1},
            'devices': [{'serial_number': 'DL001', 'type': 'LAPTOP', 'status': 'ASSIGNED'}],
            'licenses': [{'software_name': 'Microsoft Office', 'total_count': 10, 'used_count': 2}]
        }
        
        csv_content = ReportService.export_to_csv(data, 'inventory')
        
        self.assertIsInstance(csv_content, str)
        self.assertIn('serial_number', csv_content)
        self.assertIn('DL001', csv_content)
        self.assertIn('Microsoft Office', csv_content)
    
    def test_export_report_pdf(self):
        """Test PDF report export."""
        data = {
            'summary': {'total_devices': 1, 'total_licenses': 1},
            'generated_at': timezone.now().isoformat()
        }
        
        # Mock PDF generation
        with patch('apps.reports.services.generate_pdf') as mock_pdf:
            mock_pdf.return_value = b'PDF content'
            
            pdf_content = ReportService.export_to_pdf(data, 'usage', 'Test Report')
            
            self.assertEqual(pdf_content, b'PDF content')
            mock_pdf.assert_called_once()
    
    def test_schedule_report_generation(self):
        """Test scheduled report generation."""
        schedule = ReportSchedule.objects.create(
            name='Test Schedule',
            report_type='USAGE',
            frequency='DAILY',
            parameters={'department': 'IT'},
            created_by=self.admin_user,
            next_run=timezone.now() + timedelta(hours=1)
        )
        
        # Mock the actual report generation
        with patch.object(ReportService, 'generate_usage_report') as mock_generate:
            mock_generate.return_value = {'summary': {'total_devices': 1}}
            
            report = ReportService.execute_scheduled_report(schedule)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.name, 'Test Schedule')
            self.assertEqual(report.report_type, 'USAGE')
            mock_generate.assert_called_once_with(schedule.parameters)
    
    def test_report_caching(self):
        """Test report data caching."""
        parameters = {'department': 'IT'}
        
        # First call should generate report
        with patch.object(ReportService, '_calculate_usage_data') as mock_calc:
            mock_calc.return_value = {'devices': [], 'licenses': []}
            
            report1 = ReportService.generate_usage_report(parameters)
            report2 = ReportService.generate_usage_report(parameters)
            
            # Should only calculate once due to caching
            self.assertEqual(mock_calc.call_count, 1)
    
    def test_report_filtering(self):
        """Test report data filtering."""
        # Create additional test data
        other_employee = Employee.objects.create(
            user=User.objects.create_user(username='other', email='other@example.com', password='pass'),
            employee_id='EMP002',
            name='Other Employee',
            email='other@example.com',
            department='Sales',
            position='Sales Rep',
            location='OKINAWA',
            hire_date=date.today() - timedelta(days=200)
        )
        
        # Test department filtering
        parameters = {'department': 'IT'}
        report_data = ReportService.generate_usage_report(parameters)
        
        # Should only include IT department data
        for assignment in report_data.get('device_usage', []):
            self.assertEqual(assignment['employee_department'], 'IT')
    
    def test_report_date_range_filtering(self):
        """Test report date range filtering."""
        # Create assignment outside date range
        old_assignment = DeviceAssignment.objects.create(
            device=Device.objects.create(
                type='TABLET',
                manufacturer='Apple',
                model='iPad',
                serial_number='IPAD001',
                purchase_date=date.today() - timedelta(days=400),
                warranty_expiry=date.today() + timedelta(days=100)
            ),
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=200),
            actual_return_date=date.today() - timedelta(days=150),
            purpose='Old assignment',
            status='RETURNED'
        )
        
        # Test with date range that excludes old assignment
        parameters = {
            'start_date': (date.today() - timedelta(days=60)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        report_data = ReportService.generate_usage_report(parameters)
        
        # Should not include the old assignment
        device_usage = report_data.get('device_usage', [])
        old_assignment_found = any(
            usage['device_serial'] == 'IPAD001' 
            for usage in device_usage
        )
        self.assertFalse(old_assignment_found)


class ReportAPITest(APITestCase):
    """Test cases for Report API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Create test report
        self.report = Report.objects.create(
            name='Test Report',
            report_type='USAGE',
            parameters={'department': 'IT'},
            generated_by=self.admin_user,
            file_path='/reports/test.pdf',
            file_size=1024
        )
    
    def test_report_list_admin(self):
        """Test report list endpoint as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Report')
    
    def test_report_list_regular_user(self):
        """Test report list endpoint as regular user."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('report-list')
        response = self.client.get(url)
        
        # Regular users should only see their own reports
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_generate_usage_report_api(self):
        """Test usage report generation API."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('report-generate-usage')
        data = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat(),
            'department': 'IT',
            'format': 'json'
        }
        
        with patch.object(ReportService, 'generate_usage_report') as mock_generate:
            mock_generate.return_value = {
                'summary': {'total_devices': 5, 'total_licenses': 10},
                'device_usage': [],
                'license_usage': []
            }
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('summary', response.data)
            mock_generate.assert_called_once()
    
    def test_generate_cost_analysis_api(self):
        """Test cost analysis report generation API."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('report-generate-cost')
        data = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat(),
            'format': 'csv'
        }
        
        with patch.object(ReportService, 'generate_cost_analysis_report') as mock_generate:
            mock_generate.return_value = {
                'summary': {'total_monthly_cost': 50000},
                'license_costs': []
            }
            
            with patch.object(ReportService, 'export_to_csv') as mock_csv:
                mock_csv.return_value = 'CSV content'
                
                response = self.client.post(url, data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_generate_inventory_report_api(self):
        """Test inventory report generation API."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('report-generate-inventory')
        data = {
            'include_devices': True,
            'include_licenses': True,
            'location': 'TOKYO',
            'format': 'pdf'
        }
        
        with patch.object(ReportService, 'generate_inventory_report') as mock_generate:
            mock_generate.return_value = {
                'devices': [],
                'licenses': [],
                'summary': {'total_devices': 10}
            }
            
            with patch.object(ReportService, 'export_to_pdf') as mock_pdf:
                mock_pdf.return_value = b'PDF content'
                
                response = self.client.post(url, data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_report_download(self):
        """Test report file download."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Mock file existence and content
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b'Report content'
                
                url = reverse('report-download', kwargs={'pk': self.report.pk})
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_report_schedule_crud(self):
        """Test report schedule CRUD operations."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create schedule
        url = reverse('reportschedule-list')
        data = {
            'name': 'Weekly Report',
            'report_type': 'USAGE',
            'frequency': 'WEEKLY',
            'parameters': {'department': 'IT'},
            'next_run': (timezone.now() + timedelta(days=7)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        schedule_id = response.data['id']
        
        # Read schedule
        url = reverse('reportschedule-detail', kwargs={'pk': schedule_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Weekly Report')
        
        # Update schedule
        data = {'name': 'Updated Weekly Report'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Weekly Report')
        
        # Delete schedule
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_report_permissions(self):
        """Test report access permissions."""
        # Regular user should not access admin reports
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('report-detail', kwargs={'pk': self.report.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Admin should access all reports
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_report_filtering_api(self):
        """Test report filtering via API."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create additional reports
        Report.objects.create(
            name='Cost Report',
            report_type='COST',
            generated_by=self.admin_user
        )
        
        # Filter by report type
        url = reverse('report-list')
        response = self.client.get(url, {'report_type': 'USAGE'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['report_type'], 'USAGE')
    
    def test_report_statistics_api(self):
        """Test report statistics endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('report-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reports', response.data)
        self.assertIn('reports_by_type', response.data)
        self.assertIn('recent_reports', response.data)


class ReportSerializerTest(TestCase):
    """Test cases for report serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report = Report.objects.create(
            name='Test Report',
            report_type='USAGE',
            parameters={'department': 'IT'},
            generated_by=self.user
        )
    
    def test_report_serializer(self):
        """Test ReportSerializer."""
        serializer = ReportSerializer(self.report)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Report')
        self.assertEqual(data['report_type'], 'USAGE')
        self.assertEqual(data['parameters'], {'department': 'IT'})
        self.assertIn('generated_at', data)
        self.assertIn('generated_by_name', data)
    
    def test_report_schedule_serializer(self):
        """Test ReportScheduleSerializer."""
        schedule = ReportSchedule.objects.create(
            name='Test Schedule',
            report_type='COST',
            frequency='WEEKLY',
            parameters={'location': 'TOKYO'},
            created_by=self.user,
            next_run=timezone.now() + timedelta(days=7)
        )
        
        serializer = ReportScheduleSerializer(schedule)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Schedule')
        self.assertEqual(data['frequency'], 'WEEKLY')
        self.assertTrue(data['is_active'])
        self.assertIn('next_run', data)


class ReportIntegrationTest(TransactionTestCase):
    """Integration tests for the reports system."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Create comprehensive test data
        self.create_test_data()
    
    def create_test_data(self):
        """Create comprehensive test data for integration tests."""
        # Create employees
        self.employees = []
        departments = ['IT', 'Sales', 'HR']
        
        for i, dept in enumerate(departments):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            
            employee = Employee.objects.create(
                user=user,
                employee_id=f'EMP{i:03d}',
                name=f'Employee {i}',
                email=f'emp{i}@example.com',
                department=dept,
                position='Staff',
                location='TOKYO',
                hire_date=date.today() - timedelta(days=365)
            )
            self.employees.append(employee)
        
        # Create devices and assignments
        for i, employee in enumerate(self.employees):
            device = Device.objects.create(
                type='LAPTOP',
                manufacturer='Dell',
                model=f'Model {i}',
                serial_number=f'SN{i:03d}',
                purchase_date=date.today() - timedelta(days=180),
                warranty_expiry=date.today() + timedelta(days=185)
            )
            
            DeviceAssignment.objects.create(
                device=device,
                employee=employee,
                assigned_date=date.today() - timedelta(days=30),
                purpose='Work assignment',
                status='ACTIVE'
            )
        
        # Create licenses and assignments
        license = License.objects.create(
            software_name='Office Suite',
            license_type='Standard',
            total_count=10,
            available_count=7,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1000.00')
        )
        
        for employee in self.employees:
            LicenseAssignment.objects.create(
                license=license,
                employee=employee,
                start_date=date.today() - timedelta(days=60),
                purpose='Office work',
                status='ACTIVE'
            )
    
    def test_end_to_end_report_generation(self):
        """Test complete report generation workflow."""
        # Generate usage report
        parameters = {
            'start_date': (date.today() - timedelta(days=90)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        report_data = ReportService.generate_usage_report(parameters)
        
        # Verify report contains expected data
        self.assertIn('summary', report_data)
        self.assertIn('device_usage', report_data)
        self.assertIn('license_usage', report_data)
        
        summary = report_data['summary']
        self.assertEqual(summary['total_devices'], 3)
        self.assertEqual(summary['total_licenses'], 1)
        self.assertEqual(summary['active_device_assignments'], 3)
        self.assertEqual(summary['active_license_assignments'], 3)
        
        # Verify department breakdown
        dept_breakdown = report_data['department_breakdown']
        self.assertEqual(len(dept_breakdown), 3)  # IT, Sales, HR
        
        for dept_data in dept_breakdown:
            self.assertIn('department', dept_data)
            self.assertIn('device_count', dept_data)
            self.assertIn('license_count', dept_data)
    
    def test_scheduled_report_execution(self):
        """Test scheduled report execution."""
        # Create a schedule
        schedule = ReportSchedule.objects.create(
            name='Daily Usage Report',
            report_type='USAGE',
            frequency='DAILY',
            parameters={'department': 'IT'},
            created_by=self.admin_user,
            next_run=timezone.now() - timedelta(minutes=1)  # Past time to trigger
        )
        
        # Execute the schedule
        report = ReportService.execute_scheduled_report(schedule)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.name, 'Daily Usage Report')
        self.assertEqual(report.report_type, 'USAGE')
        self.assertEqual(report.status, 'COMPLETED')
        
        # Schedule should be updated for next run
        schedule.refresh_from_db()
        self.assertGreater(schedule.next_run, timezone.now())
    
    def test_report_data_consistency(self):
        """Test data consistency across different report types."""
        parameters = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        # Generate different report types
        usage_report = ReportService.generate_usage_report(parameters)
        cost_report = ReportService.generate_cost_analysis_report(parameters)
        inventory_report = ReportService.generate_inventory_report({})
        
        # Verify consistency
        usage_devices = usage_report['summary']['total_devices']
        inventory_devices = inventory_report['summary']['total_devices']
        self.assertEqual(usage_devices, inventory_devices)
        
        usage_licenses = usage_report['summary']['total_licenses']
        inventory_licenses = inventory_report['summary']['total_licenses']
        self.assertEqual(usage_licenses, inventory_licenses)
    
    def test_large_dataset_performance(self):
        """Test report generation performance with large datasets."""
        import time
        
        # Create additional test data
        for i in range(100):
            user = User.objects.create_user(
                username=f'perfuser{i}',
                email=f'perfuser{i}@example.com',
                password='testpass123'
            )
            
            employee = Employee.objects.create(
                user=user,
                employee_id=f'PERF{i:03d}',
                name=f'Perf Employee {i}',
                email=f'perf{i}@example.com',
                department='Performance',
                position='Tester',
                location='TOKYO',
                hire_date=date.today() - timedelta(days=100)
            )
        
        # Measure report generation time
        start_time = time.time()
        
        parameters = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        report_data = ReportService.generate_usage_report(parameters)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(generation_time, 5.0, "Report generation taking too long")
        
        # Verify report was generated correctly
        self.assertIn('summary', report_data)
        self.assertGreaterEqual(report_data['summary']['total_employees'], 103)  # Original 3 + 100 new


class ReportErrorHandlingTest(TestCase):
    """Test cases for report error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_invalid_date_range(self):
        """Test handling of invalid date ranges."""
        parameters = {
            'start_date': date.today().isoformat(),
            'end_date': (date.today() - timedelta(days=30)).isoformat()  # End before start
        }
        
        with self.assertRaises(ValueError):
            ReportService.generate_usage_report(parameters)
    
    def test_missing_parameters(self):
        """Test handling of missing required parameters."""
        # Empty parameters
        with self.assertRaises(KeyError):
            ReportService.generate_usage_report({})
    
    def test_database_error_handling(self):
        """Test handling of database errors during report generation."""
        parameters = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        # Mock database error
        with patch('apps.employees.models.Employee.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            with self.assertRaises(Exception):
                ReportService.generate_usage_report(parameters)
    
    def test_file_system_error_handling(self):
        """Test handling of file system errors during export."""
        data = {'summary': {'total_devices': 1}}
        
        # Mock file system error
        with patch('builtins.open', side_effect=IOError("File system error")):
            with self.assertRaises(IOError):
                ReportService.export_to_csv(data, 'test')
    
    def test_memory_error_handling(self):
        """Test handling of memory errors with large datasets."""
        # This is a conceptual test - in practice, you'd need actual large data
        parameters = {
            'start_date': (date.today() - timedelta(days=365)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        # Mock memory error
        with patch('apps.reports.services.ReportService._calculate_usage_data') as mock_calc:
            mock_calc.side_effect = MemoryError("Out of memory")
            
            with self.assertRaises(MemoryError):
                ReportService.generate_usage_report(parameters)