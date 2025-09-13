"""
Tests for the reports app.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from apps.employees.models import Employee
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment
from .services import ReportService

User = get_user_model()


class ReportServiceTest(TestCase):
    """Test cases for ReportService."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test employee
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='Test Employee',
            email='test@example.com',
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
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=100),
            warranty_expiry=date.today() + timedelta(days=265),
            status='ASSIGNED'
        )
        
        # Create test license
        self.license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=8,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=100.00
        )
        
        # Create test assignments
        self.device_assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=30),
            purpose='Development work'
        )
        
        self.license_assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=30),
            start_date=date.today() - timedelta(days=30),
            purpose='Office productivity'
        )
    
    def test_get_usage_statistics(self):
        """Test usage statistics generation."""
        filters = {
            'start_date': date.today() - timedelta(days=60),
            'end_date': date.today()
        }
        
        result = ReportService.get_usage_statistics(filters)
        
        # Check structure
        self.assertIn('department_stats', result)
        self.assertIn('position_stats', result)
        self.assertIn('device_usage', result)
        self.assertIn('license_usage', result)
        self.assertIn('period_summary', result)
        
        # Check department stats
        self.assertIn('IT', result['department_stats'])
        dept_stats = result['department_stats']['IT']
        self.assertEqual(dept_stats['employee_count'], 1)
        self.assertEqual(dept_stats['device_assignments'], 1)
        self.assertEqual(dept_stats['license_assignments'], 1)
    
    def test_get_inventory_status(self):
        """Test inventory status generation."""
        result = ReportService.get_inventory_status()
        
        # Check structure
        self.assertIn('device_inventory', result)
        self.assertIn('license_inventory', result)
        self.assertIn('utilization_rates', result)
        self.assertIn('shortage_predictions', result)
        
        # Check device inventory
        device_inventory = result['device_inventory']
        self.assertIn('total_devices', device_inventory)
        self.assertIn('type_breakdown', device_inventory)
        
        # Check license inventory
        license_inventory = result['license_inventory']
        self.assertIn('license_details', license_inventory)
        self.assertIn('summary', license_inventory)
    
    def test_get_cost_analysis(self):
        """Test cost analysis generation."""
        filters = {
            'start_date': date.today() - timedelta(days=60),
            'end_date': date.today()
        }
        
        result = ReportService.get_cost_analysis(filters)
        
        # Check structure
        self.assertIn('department_costs', result)
        self.assertIn('software_costs', result)
        self.assertIn('cost_trends', result)
        self.assertIn('budget_comparison', result)
        
        # Check department costs
        self.assertIn('IT', result['department_costs'])
        dept_costs = result['department_costs']['IT']
        self.assertEqual(dept_costs['employee_count'], 1)
        self.assertIn('monthly_cost', dept_costs)
        self.assertIn('yearly_cost', dept_costs)
        
        # Check software costs
        software_costs = result['software_costs']
        self.assertIsInstance(software_costs, dict)
        
        # Check cost trends
        cost_trends = result['cost_trends']
        self.assertIsInstance(cost_trends, dict)


class ReportAPITest(APITestCase):
    """Test cases for Report API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
    
    def test_usage_statistics_endpoint_admin(self):
        """Test usage statistics endpoint with admin user."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('usage-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
    
    def test_usage_statistics_endpoint_regular_user(self):
        """Test usage statistics endpoint with regular user."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('usage-statistics')
        response = self.client.get(url)
        
        # Regular users should be able to read (GET request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_usage_statistics_endpoint_unauthenticated(self):
        """Test usage statistics endpoint without authentication."""
        url = reverse('usage-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_status_endpoint(self):
        """Test inventory status endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('inventory-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
    
    def test_department_usage_endpoint(self):
        """Test department usage endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('department-usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
    
    def test_position_usage_endpoint(self):
        """Test position usage endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('position-usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
    
    def test_cost_analysis_endpoint(self):
        """Test cost analysis endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('cost-analysis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
    
    def test_export_report_endpoint(self):
        """Test export report endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('export-report')
        data = {
            'format': 'csv',
            'report_type': 'usage_stats',
            'filters': {}
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
    
    def test_export_cost_analysis_report(self):
        """Test exporting cost analysis report."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('export-report')
        data = {
            'format': 'csv',
            'report_type': 'cost_analysis',
            'filters': {}
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
    
    def test_usage_statistics_with_filters(self):
        """Test usage statistics with query parameters."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('usage-statistics')
        params = {
            'department': 'IT',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
    
    def test_usage_statistics_invalid_date_range(self):
        """Test usage statistics with invalid date range."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('usage-statistics')
        params = {
            'start_date': '2024-12-31',
            'end_date': '2024-01-01'  # End date before start date
        }
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
