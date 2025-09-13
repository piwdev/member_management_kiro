"""
Tests for dashboard app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta

from .models import ResourceRequest, ReturnRequest, Notification
from apps.employees.models import Employee
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment

User = get_user_model()


class ResourceRequestModelTest(TestCase):
    """Test cases for ResourceRequest model."""
    
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
            email='test@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today()
        )
    
    def test_create_device_request(self):
        """Test creating a device resource request."""
        request = ResourceRequest.objects.create(
            request_type='DEVICE',
            employee=self.employee,
            device_type='LAPTOP',
            purpose='Development work',
            business_justification='Need laptop for project',
            expected_usage_period='6 months',
            expected_start_date=date.today() + timedelta(days=1)
        )
        
        self.assertEqual(request.request_type, 'DEVICE')
        self.assertEqual(request.employee, self.employee)
        self.assertEqual(request.status, 'PENDING')
        self.assertTrue(request.is_pending)
    
    def test_create_license_request(self):
        """Test creating a license resource request."""
        request = ResourceRequest.objects.create(
            request_type='LICENSE',
            employee=self.employee,
            software_name='Adobe Photoshop',
            purpose='Design work',
            business_justification='Need for UI design',
            expected_usage_period='1 year',
            expected_start_date=date.today() + timedelta(days=1)
        )
        
        self.assertEqual(request.request_type, 'LICENSE')
        self.assertEqual(request.software_name, 'Adobe Photoshop')
        self.assertTrue(request.is_pending)
    
    def test_approve_request(self):
        """Test approving a resource request."""
        request = ResourceRequest.objects.create(
            request_type='DEVICE',
            employee=self.employee,
            device_type='LAPTOP',
            purpose='Development work',
            business_justification='Need laptop for project',
            expected_usage_period='6 months',
            expected_start_date=date.today() + timedelta(days=1)
        )
        
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        request.approve(approved_by=admin_user, notes='Approved for project')
        
        self.assertEqual(request.status, 'APPROVED')
        self.assertEqual(request.approved_by, admin_user)
        self.assertIsNotNone(request.approved_at)
        self.assertTrue(request.is_approved)


class EmployeeDashboardAPITest(APITestCase):
    """Test cases for employee dashboard API."""
    
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
            email='test@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today()
        )
        
        # Create test device and license
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL001',
            purchase_date=date.today(),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        
        self.license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=5,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=100.00
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_get_my_resources(self):
        """Test getting employee's assigned resources."""
        # Create assignments
        device_assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            purpose='Development work'
        )
        
        license_assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today(),
            purpose='Office work'
        )
        
        url = '/api/dashboard/my_resources/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['device_count'], 1)
        self.assertEqual(data['license_count'], 1)
        self.assertEqual(data['total_active_resources'], 2)
    
    def test_create_resource_request(self):
        """Test creating a resource request."""
        url = '/api/resource-requests/'
        data = {
            'request_type': 'DEVICE',
            'device_type': 'LAPTOP',
            'purpose': 'Development work',
            'business_justification': 'Need laptop for new project',
            'expected_usage_period': '6 months',
            'expected_start_date': (date.today() + timedelta(days=1)).isoformat(),
            'priority': 'MEDIUM'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify request was created
        response_data = response.json()
        request = ResourceRequest.objects.get(id=response_data['id'])
        self.assertEqual(request.employee, self.employee)
        self.assertEqual(request.request_type, 'DEVICE')
        self.assertEqual(request.status, 'PENDING')
    
    def test_create_return_request(self):
        """Test creating a return request."""
        # Create an active assignment first
        device_assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            purpose='Development work'
        )
        
        url = '/api/return-requests/'
        data = {
            'request_type': 'DEVICE',
            'device_assignment_id': str(device_assignment.id),
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'return_reason': 'Project completed',
            'condition_notes': 'Good condition'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify return request was created
        response_data = response.json()
        return_request = ReturnRequest.objects.get(id=response_data['id'])
        self.assertEqual(return_request.employee, self.employee)
        self.assertEqual(return_request.device_assignment, device_assignment)
        self.assertEqual(return_request.status, 'PENDING')
    
    def test_get_available_devices(self):
        """Test getting available devices."""
        url = '/api/dashboard/available_resources/?type=device'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['serial_number'], 'DL001')
    
    def test_get_available_licenses(self):
        """Test getting available licenses."""
        url = '/api/dashboard/available_resources/?type=license'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['software_name'], 'Microsoft Office')
        self.assertEqual(data[0]['available_count'], 5)


class ReturnRequestModelTest(TestCase):
    """Test cases for ReturnRequest model."""
    
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
            email='test@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today()
        )
        
        self.device = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL001',
            purchase_date=date.today(),
            warranty_expiry=date.today() + timedelta(days=365)
        )
        
        self.device_assignment = DeviceAssignment.objects.create(
            device=self.device,
            employee=self.employee,
            assigned_date=date.today(),
            purpose='Development work'
        )
    
    def test_create_device_return_request(self):
        """Test creating a device return request."""
        return_request = ReturnRequest.objects.create(
            request_type='DEVICE',
            employee=self.employee,
            device_assignment=self.device_assignment,
            expected_return_date=date.today() + timedelta(days=7),
            return_reason='Project completed'
        )
        
        self.assertEqual(return_request.request_type, 'DEVICE')
        self.assertEqual(return_request.employee, self.employee)
        self.assertEqual(return_request.device_assignment, self.device_assignment)
        self.assertEqual(return_request.status, 'PENDING')
        self.assertTrue(return_request.is_pending)
    
    def test_complete_return_request(self):
        """Test completing a return request."""
        return_request = ReturnRequest.objects.create(
            request_type='DEVICE',
            employee=self.employee,
            device_assignment=self.device_assignment,
            expected_return_date=date.today() + timedelta(days=7),
            return_reason='Project completed'
        )
        
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        return_request.complete(
            completed_by=admin_user,
            actual_return_date=date.today(),
            notes='Return processed successfully'
        )
        
        self.assertEqual(return_request.status, 'COMPLETED')
        self.assertEqual(return_request.processed_by, admin_user)
        self.assertIsNotNone(return_request.processed_at)
        self.assertTrue(return_request.is_completed)
        
        # Verify device was returned
        self.device_assignment.refresh_from_db()
        self.assertEqual(self.device_assignment.status, 'RETURNED')
        
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'AVAILABLE')


class LicenseAlertTest(APITestCase):
    """Test cases for license alert functionality."""
    
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
            email='test@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today()
        )
        
        # Create expiring license
        self.expiring_license = License.objects.create(
            software_name='Adobe Photoshop',
            license_type='Standard',
            total_count=5,
            available_count=3,
            expiry_date=date.today() + timedelta(days=15),  # Expires in 15 days
            pricing_model='YEARLY',
            unit_price=500.00
        )
        
        # Create license assignment with end date
        self.assignment_with_end_date = LicenseAssignment.objects.create(
            license=self.expiring_license,
            employee=self.employee,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),  # Ends in 10 days
            purpose='Design work'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_get_license_alerts(self):
        """Test getting license alerts for employee."""
        url = '/api/dashboard/license_alerts/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertGreater(data['total_alerts'], 0)
        self.assertIn('alerts', data)
        
        # Should have both license expiry and assignment expiry alerts
        alert_types = [alert['alert_type'] for alert in data['alerts']]
        self.assertIn('license_expiry', alert_types)
        self.assertIn('assignment_expiry', alert_types)
    
    def test_admin_license_alerts(self):
        """Test admin license alerts endpoint."""
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=admin_user)
        
        url = '/api/dashboard/admin_license_alerts/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('alerts', data)
        self.assertIn('summary', data)
        self.assertIn('alerts_by_severity', data)
    
    def test_license_alert_management_command(self):
        """Test the license alert management command."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('check_license_alerts', '--dry-run', '--verbose', stdout=out)
        
        output = out.getvalue()
        self.assertIn('License expiring', output)
        self.assertIn('Assignment expiring', output)


class NotificationTest(APITestCase):
    """Test cases for notification functionality."""
    
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
            email='test@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today()
        )
        
        # Create test notification
        self.notification = Notification.objects.create(
            employee=self.employee,
            notification_type='LICENSE_EXPIRY',
            title='Test License Expiry',
            message='Your license is expiring soon.',
            priority='HIGH'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_get_notifications(self):
        """Test getting user notifications."""
        url = '/api/notifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'Test License Expiry')
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read."""
        # First mark notification as sent
        self.notification.mark_as_sent()
        
        url = f'/api/notifications/{self.notification.id}/mark_as_read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify notification was marked as read
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, 'READ')
        self.assertIsNotNone(self.notification.read_at)
    
    def test_dismiss_notification(self):
        """Test dismissing notification."""
        # First mark as sent
        self.notification.mark_as_sent()
        
        url = f'/api/notifications/{self.notification.id}/dismiss/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify notification was dismissed
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, 'DISMISSED')
        self.assertIsNotNone(self.notification.dismissed_at)
    
    def test_unread_count(self):
        """Test getting unread notification count."""
        # Mark notification as sent (unread)
        self.notification.mark_as_sent()
        
        url = '/api/notifications/unread_count/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['unread_count'], 1)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        # Create another notification and mark both as sent
        notification2 = Notification.objects.create(
            employee=self.employee,
            notification_type='SYSTEM_ALERT',
            title='System Maintenance',
            message='System will be down for maintenance.',
            priority='MEDIUM'
        )
        
        self.notification.mark_as_sent()
        notification2.mark_as_sent()
        
        url = '/api/notifications/mark_all_as_read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['marked_count'], 2)
        
        # Verify both notifications are marked as read
        self.notification.refresh_from_db()
        notification2.refresh_from_db()
        
        self.assertEqual(self.notification.status, 'READ')
        self.assertEqual(notification2.status, 'READ')