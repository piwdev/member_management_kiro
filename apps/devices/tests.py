"""
Tests for device models and functionality.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

from apps.employees.models import Employee
from .models import Device, DeviceAssignment

User = get_user_model()


class DeviceModelTest(TestCase):
    """Test cases for the Device model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=30)
        )
    
    def test_device_creation(self):
        """Test basic device creation."""
        device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365),
            created_by=self.user
        )
        
        self.assertEqual(device.type, 'LAPTOP')
        self.assertEqual(device.manufacturer, 'Dell')
        self.assertEqual(device.model, 'Latitude 5520')
        self.assertEqual(device.serial_number, 'DL123456')
        self.assertEqual(device.status, 'AVAILABLE')
        self.assertTrue(device.is_available)
        self.assertFalse(device.is_assigned)
    
    def test_device_str_representation(self):
        """Test device string representation."""
        device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        
        expected = "ラップトップ - Dell Latitude 5520 (DL123456)"
        self.assertEqual(str(device), expected)
    
    def test_warranty_status_property(self):
        """Test warranty status calculation."""
        # Valid warranty
        device_valid = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        self.assertEqual(device_valid.warranty_status, 'VALID')
        
        # Expiring soon (within 30 days)
        device_expiring = Device.objects.create(
            type='TABLET',
            manufacturer='Apple',
            model='iPad Pro',
            serial_number='AP123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=15)
        )
        self.assertEqual(device_expiring.warranty_status, 'EXPIRING_SOON')
        
        # Expired
        device_expired = Device.objects.create(
            type='SMARTPHONE',
            manufacturer='Samsung',
            model='Galaxy S21',
            serial_number='SM123456',
            purchase_date=date.today() - timedelta(days=730),
            warranty_expiry=date.today() - timedelta(days=30)
        )
        self.assertEqual(device_expired.warranty_status, 'EXPIRED')
    
    def test_device_validation(self):
        """Test device model validation."""
        # Test warranty expiry before purchase date
        with self.assertRaises(ValidationError):
            device = Device(
                type='LAPTOP',
                manufacturer='Dell',
                model='Latitude 5520',
                serial_number='DL123456',
                purchase_date=date.today(),
                warranty_expiry=date.today() - timedelta(days=1)
            )
            device.full_clean()
    
    def test_device_assignment_methods(self):
        """Test device assignment and return methods."""
        device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        
        # Test assignment
        assignment = device.assign_to_employee(
            employee=self.employee,
            purpose='Development work',
            assigned_by=self.user
        )
        
        self.assertEqual(device.status, 'ASSIGNED')
        self.assertTrue(device.is_assigned)
        self.assertFalse(device.is_available)
        self.assertEqual(device.current_assignment, assignment)
        
        # Test return
        returned_assignment = device.return_from_employee(
            returned_by=self.user,
            notes='Device returned in good condition'
        )
        
        self.assertEqual(device.status, 'AVAILABLE')
        self.assertTrue(device.is_available)
        self.assertFalse(device.is_assigned)
        self.assertIsNone(device.current_assignment)
        self.assertEqual(returned_assignment.status, 'RETURNED')


class DeviceAssignmentModelTest(TestCase):
    """Test cases for the DeviceAssignment model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=30)
        )
        
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365)
        )
    
    def test_assignment_creation(self):
        """Test basic assignment creation."""
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            purpose='Development work',
            assigned_by=self.user
        )
        
        self.assertEqual(assignment.device, self.device)
        self.assertEqual(assignment.employee, self.employee)
        self.assertEqual(assignment.status, 'ACTIVE')
        self.assertTrue(assignment.is_active)
        self.assertFalse(assignment.is_overdue)
    
    def test_assignment_str_representation(self):
        """Test assignment string representation."""
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            purpose='Development work'
        )
        
        expected = f"{self.device} → {self.employee.name} ({date.today()})"
        self.assertEqual(str(assignment), expected)
    
    def test_assignment_validation(self):
        """Test assignment model validation."""
        # Test return date before assignment date
        with self.assertRaises(ValidationError):
            assignment = DeviceAssignment(
                device=self.device,
                employee=self.employee,
                assigned_date=date.today(),
                actual_return_date=date.today() - timedelta(days=1),
                purpose='Test'
            )
            assignment.full_clean()
        
        # Test expected return date before assignment date
        with self.assertRaises(ValidationError):
            assignment = DeviceAssignment(
                device=self.device,
                employee=self.employee,
                assigned_date=date.today(),
                expected_return_date=date.today() - timedelta(days=1),
                purpose='Test'
            )
            assignment.full_clean()
    
    def test_overdue_detection(self):
        """Test overdue assignment detection."""
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            purpose='Development work'
        )
        
        self.assertTrue(assignment.is_overdue)
    
    def test_days_assigned_calculation(self):
        """Test days assigned calculation."""
        assignment_date = date.today() - timedelta(days=5)
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=assignment_date,
            purpose='Development work'
        )
        
        self.assertEqual(assignment.days_assigned, 5)
        
        # Test with return date
        return_date = assignment_date + timedelta(days=3)
        assignment.actual_return_date = return_date
        assignment.save()
        
        self.assertEqual(assignment.days_assigned, 3)
    
    def test_unique_active_assignment_constraint(self):
        """Test that only one active assignment per device is allowed."""
        # Create first assignment
        DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            purpose='First assignment',
            status='ACTIVE'
        )
        
        # Create second employee
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        employee2 = Employee.objects.create(
            user=user2,
            employee_id='EMP002',
            name='Test Employee 2',
            email='employee2@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=30)
        )
        
        # Try to create second active assignment for same device
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DeviceAssignment.objects.create(
                device=self.device,
                employee=employee2,
                assigned_date=date.today(),
                purpose='Second assignment',
                status='ACTIVE'
            )
    
    def test_status_auto_update_on_save(self):
        """Test that status is automatically updated based on dates."""
        assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            purpose='Development work'
        )
        
        # Should be marked as overdue
        self.assertEqual(assignment.status, 'OVERDUE')
        
        # Set return date
        assignment.actual_return_date = date.today()
        assignment.save()
        
        # Should be marked as returned
        self.assertEqual(assignment.status, 'RETURNED')


class DeviceAPITest(TestCase):
    """Test cases for the Device API."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=30)
        )
        
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365),
            created_by=self.user
        )
        
        # Set up API client
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_device_list_api(self):
        """Test device list API."""
        response = self.client.get('/api/devices/devices/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['serial_number'], 'DL123456')
    
    def test_device_create_api(self):
        """Test device creation API."""
        data = {
            'type': 'TABLET',
            'manufacturer': 'Apple',
            'model': 'iPad Pro',
            'serial_number': 'AP123456',
            'purchase_date': date.today() - timedelta(days=100),
            'warranty_expiry': date.today() + timedelta(days=265),
            'specifications': {'storage': '256GB', 'ram': '8GB'}
        }
        
        response = self.client.post('/api/devices/devices/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['serial_number'], 'AP123456')
        self.assertEqual(response.data['type'], 'TABLET')
    
    def test_device_assign_api(self):
        """Test device assignment API."""
        data = {
            'employee_id': str(self.employee.id),
            'assigned_date': date.today(),
            'expected_return_date': date.today() + timedelta(days=30),
            'purpose': 'Development work',
            'assignment_notes': 'Test assignment'
        }
        
        response = self.client.post(f'/api/devices/devices/{self.device.id}/assign/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['purpose'], 'Development work')
        
        # Verify device status changed
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'ASSIGNED')
    
    def test_device_return_api(self):
        """Test device return API."""
        # First assign the device
        assignment = self.device.assign_to_employee(
            employee=self.employee,
            purpose='Test assignment',
            assigned_by=self.user
        )
        
        data = {
            'return_date': date.today(),
            'return_notes': 'Device returned in good condition'
        }
        
        response = self.client.post(f'/api/devices/devices/{self.device.id}/return_device/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['return_notes'], 'Device returned in good condition')
        
        # Verify device status changed
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'AVAILABLE')
    
    def test_device_statistics_api(self):
        """Test device statistics API."""
        response = self.client.get('/api/devices/devices/statistics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_devices', response.data)
        self.assertIn('status_breakdown', response.data)
        self.assertIn('type_breakdown', response.data)
        self.assertEqual(response.data['total_devices'], 1)


class DeviceAssignmentAPITest(TestCase):
    """Test cases for the DeviceAssignment API."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=30)
        )
        
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL123456',
            purchase_date=date.today() - timedelta(days=365),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        
        self.assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today() - timedelta(days=5),
            expected_return_date=date.today() + timedelta(days=25),
            purpose='Development work',
            assigned_by=self.user
        )
        
        # Set up API client
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_assignment_list_api(self):
        """Test assignment list API."""
        response = self.client.get('/api/devices/device-assignments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['purpose'], 'Development work')
    
    def test_assignment_filter_by_employee(self):
        """Test assignment filtering by employee."""
        response = self.client.get(f'/api/devices/device-assignments/?employee_id={self.employee.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_assignment_filter_by_device(self):
        """Test assignment filtering by device."""
        response = self.client.get(f'/api/devices/device-assignments/?device_id={self.device.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_assignment_by_employee_endpoint(self):
        """Test assignments by employee endpoint."""
        response = self.client.get(f'/api/devices/device-assignments/by_employee/?employee_id={self.employee.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)