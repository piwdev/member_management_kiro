"""
Tests for license models and functionality.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, IntegrityError
from apps.employees.models import Employee
from .models import License, LicenseAssignment

User = get_user_model()


class LicenseModelTest(TestCase):
    """Test cases for License model."""
    
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
            hire_date=timezone.now().date()
        )
    
    def test_license_creation(self):
        """Test basic license creation."""
        license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=10,
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=Decimal('50000.00'),
            created_by=self.user
        )
        
        self.assertEqual(license.software_name, 'Microsoft Office')
        self.assertEqual(license.total_count, 10)
        self.assertEqual(license.available_count, 10)
        self.assertEqual(license.used_count, 0)
        self.assertEqual(license.usage_percentage, 0)
        self.assertFalse(license.is_fully_utilized)
        self.assertFalse(license.is_expired)
    
    def test_license_validation(self):
        """Test license validation rules."""
        # Test available_count > total_count validation
        with self.assertRaises(ValidationError):
            license = License(
                software_name='Test Software',
                license_type='Standard',
                total_count=5,
                available_count=10,  # Invalid: more than total
                expiry_date=timezone.now().date() + timezone.timedelta(days=365),
                pricing_model='YEARLY',
                unit_price=Decimal('10000.00')
            )
            license.full_clean()
    
    def test_license_cost_calculations(self):
        """Test license cost calculation methods."""
        # Monthly pricing
        monthly_license = License.objects.create(
            software_name='Monthly Software',
            license_type='Pro',
            total_count=5,
            available_count=3,  # 2 used
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1000.00'),
            created_by=self.user
        )
        
        self.assertEqual(monthly_license.calculate_monthly_cost(), Decimal('2000.00'))
        self.assertEqual(monthly_license.calculate_yearly_cost(), Decimal('24000.00'))
        
        # Yearly pricing
        yearly_license = License.objects.create(
            software_name='Yearly Software',
            license_type='Enterprise',
            total_count=3,
            available_count=1,  # 2 used
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=Decimal('12000.00'),
            created_by=self.user
        )
        
        self.assertEqual(yearly_license.calculate_monthly_cost(), Decimal('2000.00'))
        self.assertEqual(yearly_license.calculate_yearly_cost(), Decimal('24000.00'))
        
        # Perpetual pricing
        perpetual_license = License.objects.create(
            software_name='Perpetual Software',
            license_type='Standard',
            total_count=2,
            available_count=0,  # 2 used
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='PERPETUAL',
            unit_price=Decimal('50000.00'),
            created_by=self.user
        )
        
        self.assertEqual(perpetual_license.calculate_monthly_cost(), Decimal('0.00'))
        self.assertEqual(perpetual_license.calculate_yearly_cost(), Decimal('0.00'))
        self.assertEqual(perpetual_license.calculate_total_cost(), Decimal('100000.00'))
    
    def test_license_assignment_management(self):
        """Test license assignment and release functionality."""
        license = License.objects.create(
            software_name='Test Software',
            license_type='Standard',
            total_count=3,
            available_count=3,
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Test can_assign
        self.assertTrue(license.can_assign(1))
        self.assertTrue(license.can_assign(3))
        self.assertFalse(license.can_assign(4))
        
        # Test assign_license
        license.assign_license(2)
        license.refresh_from_db()
        self.assertEqual(license.available_count, 1)
        self.assertEqual(license.used_count, 2)
        
        # Test release_license
        license.release_license(1)
        license.refresh_from_db()
        self.assertEqual(license.available_count, 2)
        self.assertEqual(license.used_count, 1)
        
        # Test over-assignment validation
        with self.assertRaises(ValidationError):
            license.assign_license(3)  # Only 2 available
    
    def test_license_expiry_checks(self):
        """Test license expiry detection."""
        # Expired license
        expired_license = License.objects.create(
            software_name='Expired Software',
            license_type='Standard',
            total_count=5,
            available_count=5,
            expiry_date=timezone.now().date() - timezone.timedelta(days=1),
            pricing_model='YEARLY',
            unit_price=Decimal('10000.00'),
            created_by=self.user
        )
        
        self.assertTrue(expired_license.is_expired)
        self.assertFalse(expired_license.can_assign(1))
        
        # Expiring soon license
        expiring_license = License.objects.create(
            software_name='Expiring Software',
            license_type='Standard',
            total_count=5,
            available_count=5,
            expiry_date=timezone.now().date() + timezone.timedelta(days=15),
            pricing_model='YEARLY',
            unit_price=Decimal('10000.00'),
            created_by=self.user
        )
        
        self.assertTrue(expiring_license.is_expiring_soon())
        self.assertFalse(expiring_license.is_expired)


class LicenseAssignmentModelTest(TestCase):
    """Test cases for LicenseAssignment model."""
    
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
            hire_date=timezone.now().date()
        )
        
        self.license = License.objects.create(
            software_name='Test Software',
            license_type='Standard',
            total_count=5,
            available_count=5,
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_license_assignment_creation(self):
        """Test basic license assignment creation."""
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=timezone.now().date(),
            purpose='Development work',
            assigned_by=self.user
        )
        
        self.assertEqual(assignment.license, self.license)
        self.assertEqual(assignment.employee, self.employee)
        self.assertEqual(assignment.status, 'ACTIVE')
        self.assertTrue(assignment.is_active)
        
        # Check that license count was updated
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 4)
    
    def test_assignment_validation(self):
        """Test assignment validation rules."""
        # Test end_date before start_date
        with self.assertRaises(ValidationError):
            assignment = LicenseAssignment(
                license=self.license,
                employee=self.employee,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() - timezone.timedelta(days=1),
                purpose='Test'
            )
            assignment.full_clean()
    
    def test_unique_active_assignment_constraint(self):
        """Test that only one active assignment per license-employee pair is allowed."""
        # Create first assignment
        LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=timezone.now().date(),
            purpose='First assignment',
            assigned_by=self.user
        )
        
        # Try to create second active assignment for same license-employee
        with self.assertRaises(IntegrityError):
            LicenseAssignment.objects.create(
                license=self.license,
                employee=self.employee,
                start_date=timezone.now().date(),
                purpose='Second assignment',
                assigned_by=self.user
            )
    
    def test_assignment_revocation(self):
        """Test license assignment revocation."""
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=timezone.now().date(),
            purpose='Test assignment',
            assigned_by=self.user
        )
        
        # Check initial state
        self.assertEqual(assignment.status, 'ACTIVE')
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 4)
        
        # Revoke assignment
        assignment.revoke(revoked_by=self.user, notes='Test revocation')
        
        # Check final state
        self.assertEqual(assignment.status, 'REVOKED')
        self.assertIsNotNone(assignment.revoked_at)
        self.assertEqual(assignment.revoked_by, self.user)
        self.assertFalse(assignment.is_active)
        
        # Check that license was released
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 5)
    
    def test_assignment_expiration(self):
        """Test license assignment expiration."""
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            purpose='Test assignment',
            assigned_by=self.user
        )
        
        # Test expiring soon detection
        assignment.end_date = timezone.now().date() + timezone.timedelta(days=15)
        assignment.save()
        self.assertTrue(assignment.is_expiring_soon())
        
        # Test expiration
        assignment.expire()
        self.assertEqual(assignment.status, 'EXPIRED')
        self.assertFalse(assignment.is_active)
        
        # Check that license was released
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 5)
    
    def test_usage_days_calculation(self):
        """Test usage days calculation."""
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=30)
        
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=start_date,
            end_date=end_date,
            purpose='Test assignment',
            assigned_by=self.user
        )
        
        self.assertEqual(assignment.calculate_usage_days(), 31)  # 30 days + 1 (inclusive)
    
    def test_inactive_employee_assignment(self):
        """Test that inactive employees cannot be assigned licenses."""
        # Make employee inactive
        self.employee.status = 'INACTIVE'
        self.employee.save()
        
        with self.assertRaises(ValidationError):
            assignment = LicenseAssignment(
                license=self.license,
                employee=self.employee,
                start_date=timezone.now().date(),
                purpose='Test assignment'
            )
            assignment.full_clean()

# API Tests

import uuid
from datetime import date, timedelta
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class LicenseAPITest(APITestCase):
    """Test cases for License API endpoints."""
    
    def setUp(self):
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
        
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=365),
            created_by=self.admin_user
        )
        
        self.license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=8,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=Decimal('100.00'),
            created_by=self.admin_user
        )
    
    def test_license_list_authenticated(self):
        """Test license list endpoint with authentication."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('license-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['software_name'], 'Microsoft Office')
    
    def test_license_list_unauthenticated(self):
        """Test license list endpoint without authentication."""
        url = reverse('license-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_license_create_admin(self):
        """Test license creation by admin user."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-list')
        
        data = {
            'software_name': 'Adobe Photoshop',
            'license_type': 'Professional',
            'total_count': 5,
            'available_count': 5,
            'expiry_date': (date.today() + timedelta(days=365)).isoformat(),
            'pricing_model': 'MONTHLY',
            'unit_price': '50.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['software_name'], 'Adobe Photoshop')
        self.assertEqual(response.data['created_by'], self.admin_user.id)
    
    def test_license_create_regular_user(self):
        """Test license creation by regular user (should fail)."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('license-list')
        
        data = {
            'software_name': 'Adobe Photoshop',
            'license_type': 'Professional',
            'total_count': 5,
            'available_count': 5,
            'expiry_date': (date.today() + timedelta(days=365)).isoformat(),
            'pricing_model': 'MONTHLY',
            'unit_price': '50.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_license_assign(self):
        """Test license assignment endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-assign', kwargs={'pk': self.license.pk})
        
        data = {
            'employee_id': str(self.employee.id),
            'start_date': date.today().isoformat(),
            'purpose': 'Development work'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['license_info']['id'], str(self.license.id))
        self.assertEqual(response.data['employee_info']['id'], str(self.employee.id))
        
        # Check that license count was updated
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 7)
    
    def test_license_revoke(self):
        """Test license revocation endpoint."""
        # First create an assignment
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today(),
            purpose='Development work',
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-revoke', kwargs={'pk': self.license.pk})
        
        data = {
            'employee_id': str(self.employee.id),
            'notes': 'No longer needed'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that assignment was revoked
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'REVOKED')
        
        # Check that license count was updated
        self.license.refresh_from_db()
        self.assertEqual(self.license.available_count, 8)
    
    def test_license_usage_stats(self):
        """Test license usage statistics endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-usage-stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_licenses', response.data)
        self.assertIn('total_monthly_cost', response.data)
        self.assertIn('expiring_licenses', response.data)
        self.assertEqual(response.data['total_licenses'], 1)
    
    def test_license_cost_analysis(self):
        """Test license cost analysis endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-cost-analysis')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['software_name'], 'Microsoft Office')
        self.assertIn('monthly_cost', response.data[0])
        self.assertIn('yearly_cost', response.data[0])
    
    def test_license_expiring_alerts(self):
        """Test license expiring alerts endpoint."""
        # Create an expiring license
        expiring_license = License.objects.create(
            software_name='Expiring Software',
            license_type='Standard',
            total_count=5,
            available_count=5,
            expiry_date=date.today() + timedelta(days=15),
            pricing_model='YEARLY',
            unit_price=Decimal('100.00'),
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-expiring-alerts')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['licenses']), 1)
        self.assertEqual(response.data['licenses'][0]['software_name'], 'Expiring Software')


class LicenseAssignmentAPITest(APITestCase):
    """Test cases for LicenseAssignment API endpoints."""
    
    def setUp(self):
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
        
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=365),
            created_by=self.admin_user
        )
        
        self.license = License.objects.create(
            software_name='Microsoft Office',
            license_type='Standard',
            total_count=10,
            available_count=10,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='YEARLY',
            unit_price=Decimal('100.00'),
            created_by=self.admin_user
        )
    
    def test_assignment_create(self):
        """Test license assignment creation."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-assignment-list')
        
        data = {
            'license': str(self.license.id),
            'employee': str(self.employee.id),
            'start_date': date.today().isoformat(),
            'purpose': 'Development work'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['license'], str(self.license.id))
        self.assertEqual(response.data['employee'], str(self.employee.id))
    
    def test_assignment_list_filtering(self):
        """Test license assignment list with filtering."""
        # Create assignment
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today(),
            purpose='Development work',
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test filter by license
        url = reverse('license-assignment-list')
        response = self.client.get(url, {'license': str(self.license.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filter by employee
        response = self.client.get(url, {'employee': str(self.employee.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filter by status
        response = self.client.get(url, {'status': 'ACTIVE'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_assignment_revoke(self):
        """Test license assignment revocation."""
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today(),
            purpose='Development work',
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('license-assignment-revoke', kwargs={'pk': assignment.pk})
        
        data = {'notes': 'No longer needed'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that assignment was revoked
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'REVOKED')
    
    def test_my_assignments(self):
        """Test my assignments endpoint for regular user."""
        # Create assignment
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            start_date=date.today(),
            purpose='Development work',
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('license-assignment-my-assignments')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(assignment.id))