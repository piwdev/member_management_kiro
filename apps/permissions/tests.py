"""
Tests for permission models and services.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from .models import PermissionPolicy, PermissionOverride, PermissionAuditLog
from .services import PermissionService
from apps.employees.models import Employee

User = get_user_model()


class PermissionPolicyModelTest(TestCase):
    """Test cases for PermissionPolicy model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today(),
            user=self.user
        )
    
    def test_create_department_policy(self):
        """Test creating a department-based policy."""
        policy = PermissionPolicy.objects.create(
            name='IT Department Policy',
            policy_type='DEPARTMENT',
            target_department='IT',
            allowed_device_types=['LAPTOP', 'DESKTOP'],
            allowed_software=['Microsoft Office', 'Visual Studio'],
            created_by=self.user
        )
        
        self.assertEqual(policy.name, 'IT Department Policy')
        self.assertEqual(policy.policy_type, 'DEPARTMENT')
        self.assertEqual(policy.target_department, 'IT')
        self.assertTrue(policy.is_currently_effective)
    
    def test_create_position_policy(self):
        """Test creating a position-based policy."""
        policy = PermissionPolicy.objects.create(
            name='Developer Policy',
            policy_type='POSITION',
            target_position='Developer',
            allowed_device_types=['LAPTOP'],
            max_devices_per_type={'LAPTOP': 2},
            created_by=self.user
        )
        
        self.assertEqual(policy.target_position, 'Developer')
        self.assertEqual(policy.max_devices_per_type['LAPTOP'], 2)
    
    def test_create_individual_policy(self):
        """Test creating an individual policy."""
        policy = PermissionPolicy.objects.create(
            name='Individual Policy for EMP001',
            policy_type='INDIVIDUAL',
            target_employee=self.employee,
            restricted_software=['Adobe Photoshop'],
            created_by=self.user
        )
        
        self.assertEqual(policy.target_employee, self.employee)
        self.assertIn('Adobe Photoshop', policy.restricted_software)
    
    def test_policy_validation(self):
        """Test policy validation rules."""
        # Department policy without target_department should fail
        with self.assertRaises(ValidationError):
            policy = PermissionPolicy(
                name='Invalid Department Policy',
                policy_type='DEPARTMENT',
                created_by=self.user
            )
            policy.full_clean()
        
        # Position policy without target_position should fail
        with self.assertRaises(ValidationError):
            policy = PermissionPolicy(
                name='Invalid Position Policy',
                policy_type='POSITION',
                created_by=self.user
            )
            policy.full_clean()
    
    def test_applies_to_employee(self):
        """Test policy applicability to employees."""
        # Department policy
        dept_policy = PermissionPolicy.objects.create(
            name='IT Policy',
            policy_type='DEPARTMENT',
            target_department='IT',
            created_by=self.user
        )
        
        # Position policy
        pos_policy = PermissionPolicy.objects.create(
            name='Developer Policy',
            policy_type='POSITION',
            target_position='Developer',
            created_by=self.user
        )
        
        # Individual policy
        ind_policy = PermissionPolicy.objects.create(
            name='Individual Policy',
            policy_type='INDIVIDUAL',
            target_employee=self.employee,
            created_by=self.user
        )
        
        # Global policy
        global_policy = PermissionPolicy.objects.create(
            name='Global Policy',
            policy_type='GLOBAL',
            created_by=self.user
        )
        
        self.assertTrue(dept_policy.applies_to_employee(self.employee))
        self.assertTrue(pos_policy.applies_to_employee(self.employee))
        self.assertTrue(ind_policy.applies_to_employee(self.employee))
        self.assertTrue(global_policy.applies_to_employee(self.employee))
    
    def test_can_access_device_type(self):
        """Test device type access checking."""
        policy = PermissionPolicy.objects.create(
            name='Test Policy',
            policy_type='DEPARTMENT',
            target_department='IT',
            allowed_device_types=['LAPTOP', 'DESKTOP'],
            created_by=self.user
        )
        
        self.assertTrue(policy.can_access_device_type('LAPTOP'))
        self.assertTrue(policy.can_access_device_type('DESKTOP'))
        self.assertFalse(policy.can_access_device_type('TABLET'))
    
    def test_can_access_software(self):
        """Test software access checking."""
        policy = PermissionPolicy.objects.create(
            name='Test Policy',
            policy_type='DEPARTMENT',
            target_department='IT',
            allowed_software=['Microsoft Office'],
            restricted_software=['Adobe Photoshop'],
            created_by=self.user
        )
        
        self.assertTrue(policy.can_access_software('Microsoft Office'))
        self.assertFalse(policy.can_access_software('Adobe Photoshop'))
        self.assertFalse(policy.can_access_software('Unknown Software'))


class PermissionOverrideModelTest(TestCase):
    """Test cases for PermissionOverride model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today(),
            user=self.user
        )
    
    def test_create_override(self):
        """Test creating a permission override."""
        override = PermissionOverride.objects.create(
            employee=self.employee,
            override_type='GRANT',
            resource_type='SOFTWARE',
            resource_identifier='Adobe Photoshop',
            effective_from=date.today(),
            effective_until=date.today() + timedelta(days=30),
            reason='Special project requirement',
            created_by=self.user
        )
        
        self.assertEqual(override.employee, self.employee)
        self.assertEqual(override.override_type, 'GRANT')
        self.assertEqual(override.resource_identifier, 'Adobe Photoshop')
        self.assertTrue(override.is_currently_effective)
    
    def test_override_validation(self):
        """Test override validation rules."""
        # Invalid date range should fail
        with self.assertRaises(ValidationError):
            override = PermissionOverride(
                employee=self.employee,
                override_type='GRANT',
                resource_type='SOFTWARE',
                resource_identifier='Test Software',
                effective_from=date.today() + timedelta(days=10),
                effective_until=date.today(),
                reason='Test reason',
                created_by=self.user
            )
            override.full_clean()


class PermissionServiceTest(TestCase):
    """Test cases for PermissionService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            name='Test Employee',
            email='employee@example.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today(),
            user=self.user
        )
        
        # Create test policies
        self.dept_policy = PermissionPolicy.objects.create(
            name='IT Department Policy',
            policy_type='DEPARTMENT',
            target_department='IT',
            priority=2,
            allowed_device_types=['LAPTOP', 'DESKTOP'],
            allowed_software=['Microsoft Office'],
            created_by=self.user
        )
        
        self.pos_policy = PermissionPolicy.objects.create(
            name='Developer Policy',
            policy_type='POSITION',
            target_position='Developer',
            priority=1,  # Higher priority
            allowed_device_types=['LAPTOP'],
            restricted_software=['Adobe Photoshop'],
            created_by=self.user
        )
    
    def test_get_applicable_policies(self):
        """Test getting applicable policies for an employee."""
        policies = PermissionService.get_applicable_policies(self.employee)
        
        # Should return both policies, ordered by priority
        self.assertEqual(len(policies), 2)
        self.assertEqual(policies[0], self.pos_policy)  # Higher priority first
        self.assertEqual(policies[1], self.dept_policy)
    
    def test_can_access_device_type(self):
        """Test device type access checking."""
        # Should be allowed by both policies
        can_access, reason = PermissionService.can_access_device_type(
            self.employee, 'LAPTOP', log_check=False
        )
        self.assertTrue(can_access)
        
        # Should be denied (not in higher priority policy)
        can_access, reason = PermissionService.can_access_device_type(
            self.employee, 'DESKTOP', log_check=False
        )
        self.assertFalse(can_access)
        
        # Should be denied (not in any policy)
        can_access, reason = PermissionService.can_access_device_type(
            self.employee, 'TABLET', log_check=False
        )
        self.assertFalse(can_access)
    
    def test_can_access_software(self):
        """Test software access checking."""
        # Should be allowed
        can_access, reason = PermissionService.can_access_software(
            self.employee, 'Microsoft Office', log_check=False
        )
        self.assertTrue(can_access)
        
        # Should be denied (restricted by higher priority policy)
        can_access, reason = PermissionService.can_access_software(
            self.employee, 'Adobe Photoshop', log_check=False
        )
        self.assertFalse(can_access)
    
    def test_override_behavior(self):
        """Test permission override behavior."""
        # Create an override that grants access to restricted software
        override = PermissionOverride.objects.create(
            employee=self.employee,
            override_type='GRANT',
            resource_type='SOFTWARE',
            resource_identifier='Adobe Photoshop',
            effective_from=date.today(),
            effective_until=date.today() + timedelta(days=30),
            reason='Special project',
            created_by=self.user
        )
        
        # Now should be allowed due to override
        can_access, reason = PermissionService.can_access_software(
            self.employee, 'Adobe Photoshop', log_check=False
        )
        self.assertTrue(can_access)
        self.assertIn('オーバーライド', reason)
    
    def test_get_employee_permission_summary(self):
        """Test getting employee permission summary."""
        summary = PermissionService.get_employee_permission_summary(self.employee)
        
        self.assertEqual(summary['employee_id'], 'EMP001')
        self.assertEqual(summary['employee_name'], 'Test Employee')
        self.assertEqual(len(summary['applicable_policies']), 2)
        self.assertIn('LAPTOP', summary['allowed_device_types'])
        self.assertIn('Adobe Photoshop', summary['restricted_software'])
    
    def test_audit_logging(self):
        """Test that permission checks create audit logs."""
        initial_count = PermissionAuditLog.objects.count()
        
        # Perform a permission check with logging
        PermissionService.can_access_device_type(
            self.employee, 'LAPTOP', log_check=True, performed_by=self.user
        )
        
        # Should have created an audit log
        self.assertEqual(PermissionAuditLog.objects.count(), initial_count + 1)
        
        log = PermissionAuditLog.objects.latest('timestamp')
        self.assertEqual(log.employee, self.employee)
        self.assertEqual(log.resource_type, 'DEVICE')
        self.assertEqual(log.resource_identifier, 'LAPTOP')
        self.assertEqual(log.performed_by, self.user)
