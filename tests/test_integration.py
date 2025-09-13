"""
Integration tests for the entire asset management system.
Tests the interaction between different apps and components.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
import json

from apps.employees.models import Employee, EmployeeHistory
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment
from apps.permissions.models import PermissionPolicy, PermissionOverride
from apps.permissions.services import PermissionService
from apps.reports.services import ReportService
from apps.dashboard.models import Notification

User = get_user_model()


class SystemIntegrationTest(TransactionTestCase):
    """Test complete system workflows and integration between apps."""
    
    def setUp(self):
        """Set up comprehensive test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular users
        self.dev_user = User.objects.create_user(
            username='developer',
            email='dev@company.com',
            password='devpass123'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@company.com',
            password='managerpass123'
        )
        
        # Create employees
        self.dev_employee = Employee.objects.create(
            user=self.dev_user,
            employee_id='DEV001',
            name='開発太郎',
            email='dev@company.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=365),
            created_by=self.admin_user
        )
        
        self.manager_employee = Employee.objects.create(
            user=self.manager_user,
            employee_id='MGR001',
            name='管理花子',
            email='manager@company.com',
            department='開発部',
            position='マネージャー',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=1000),
            created_by=self.admin_user
        )
        
        # Create devices
        self.laptop = Device.objects.create(
            type='LAPTOP',
            manufacturer='Dell',
            model='Latitude 5520',
            serial_number='DL001',
            purchase_date=date.today() - timedelta(days=180),
            warranty_expiry=date.today() + timedelta(days=185),
            created_by=self.admin_user
        )
        
        self.desktop = Device.objects.create(
            type='DESKTOP',
            manufacturer='HP',
            model='EliteDesk 800',
            serial_number='HP001',
            purchase_date=date.today() - timedelta(days=200),
            warranty_expiry=date.today() + timedelta(days=165),
            created_by=self.admin_user
        )
        
        # Create licenses
        self.office_license = License.objects.create(
            software_name='Microsoft Office 365',
            license_type='Business Premium',
            total_count=50,
            available_count=48,
            expiry_date=date.today() + timedelta(days=365),
            pricing_model='MONTHLY',
            unit_price=Decimal('1500.00'),
            created_by=self.admin_user
        )
        
        self.ide_license = License.objects.create(
            software_name='JetBrains IntelliJ IDEA',
            license_type='Ultimate',
            total_count=10,
            available_count=9,
            expiry_date=date.today() + timedelta(days=200),
            pricing_model='YEARLY',
            unit_price=Decimal('60000.00'),
            created_by=self.admin_user
        )
        
        # Create permission policies
        self.dev_policy = PermissionPolicy.objects.create(
            name='開発部ポリシー',
            policy_type='DEPARTMENT',
            target_department='開発部',
            priority=2,
            allowed_device_types=['LAPTOP', 'DESKTOP'],
            allowed_software=['Microsoft Office 365', 'JetBrains IntelliJ IDEA'],
            max_devices_per_type={'LAPTOP': 2, 'DESKTOP': 1},
            created_by=self.admin_user
        )
        
        self.manager_policy = PermissionPolicy.objects.create(
            name='マネージャーポリシー',
            policy_type='POSITION',
            target_position='マネージャー',
            priority=1,
            allowed_device_types=['LAPTOP', 'DESKTOP', 'TABLET'],
            max_devices_per_type={'LAPTOP': 3, 'DESKTOP': 2, 'TABLET': 1},
            created_by=self.admin_user
        )
    
    def test_complete_employee_lifecycle(self):
        """Test complete employee lifecycle from hiring to termination."""
        # Step 1: Employee is hired (already created in setUp)
        self.assertTrue(self.dev_employee.is_active)
        self.assertEqual(self.dev_employee.status, 'ACTIVE')
        
        # Step 2: Assign resources based on permissions
        # Check permissions first
        can_laptop, reason = PermissionService.can_access_device_type(
            self.dev_employee, 'LAPTOP', log_check=False
        )
        self.assertTrue(can_laptop)
        
        can_office, reason = PermissionService.can_access_software(
            self.dev_employee, 'Microsoft Office 365', log_check=False
        )
        self.assertTrue(can_office)
        
        # Assign laptop
        laptop_assignment = self.laptop.assign_to_employee(
            employee=self.dev_employee,
            purpose='開発業務用',
            assigned_by=self.admin_user
        )
        self.assertEqual(laptop_assignment.status, 'ACTIVE')
        self.assertEqual(self.laptop.status, 'ASSIGNED')
        
        # Assign Office license
        office_assignment = LicenseAssignment.objects.create(
            license=self.office_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='業務用オフィススイート',
            assigned_by=self.admin_user
        )
        self.assertEqual(office_assignment.status, 'ACTIVE')
        self.office_license.refresh_from_db()
        self.assertEqual(self.office_license.available_count, 47)
        
        # Step 3: Employee role change
        old_position = self.dev_employee.position
        self.dev_employee.position = 'シニアエンジニア'
        self.dev_employee.updated_by = self.admin_user
        self.dev_employee.save()
        
        # Check history was created
        history = EmployeeHistory.objects.filter(
            employee=self.dev_employee,
            change_type='POSITION_CHANGE'
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_value, old_position)
        self.assertEqual(history.new_value, 'シニアエンジニア')
        
        # Step 4: Employee termination
        termination_date = date.today()
        self.dev_employee.terminate_employment(
            termination_date=termination_date,
            terminated_by=self.admin_user
        )
        
        # Check employee status
        self.assertFalse(self.dev_employee.is_active)
        self.assertEqual(self.dev_employee.status, 'INACTIVE')
        self.assertEqual(self.dev_employee.termination_date, termination_date)
        
        # Resources should be marked for recovery
        laptop_assignment.refresh_from_db()
        office_assignment.refresh_from_db()
        
        # In a real system, you might have automated processes to handle this
        # For now, we'll manually return resources
        self.laptop.return_from_employee(returned_by=self.admin_user)
        office_assignment.revoke(revoked_by=self.admin_user)
        
        # Check resources are available again
        self.laptop.refresh_from_db()
        self.assertEqual(self.laptop.status, 'AVAILABLE')
        
        self.office_license.refresh_from_db()
        self.assertEqual(self.office_license.available_count, 48)
    
    def test_permission_system_integration(self):
        """Test permission system integration with resource assignment."""
        # Test department policy application
        can_access, reason = PermissionService.can_access_device_type(
            self.dev_employee, 'LAPTOP', log_check=False
        )
        self.assertTrue(can_access)
        
        can_access, reason = PermissionService.can_access_device_type(
            self.dev_employee, 'SMARTPHONE', log_check=False
        )
        self.assertFalse(can_access)  # Not in allowed device types
        
        # Test position policy override (manager has higher priority)
        can_access, reason = PermissionService.can_access_device_type(
            self.manager_employee, 'TABLET', log_check=False
        )
        self.assertTrue(can_access)  # Manager policy allows tablets
        
        # Test individual override
        override = PermissionOverride.objects.create(
            employee=self.dev_employee,
            override_type='GRANT',
            resource_type='DEVICE',
            resource_identifier='SMARTPHONE',
            effective_from=date.today(),
            effective_until=date.today() + timedelta(days=30),
            reason='特別プロジェクト',
            created_by=self.admin_user
        )
        
        # Now should have access due to override
        can_access, reason = PermissionService.can_access_device_type(
            self.dev_employee, 'SMARTPHONE', log_check=False
        )
        self.assertTrue(can_access)
        self.assertIn('オーバーライド', reason)
    
    def test_license_management_integration(self):
        """Test license management with expiry and cost tracking."""
        # Assign licenses to employees
        dev_assignment = LicenseAssignment.objects.create(
            license=self.ide_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='開発環境',
            assigned_by=self.admin_user
        )
        
        manager_assignment = LicenseAssignment.objects.create(
            license=self.office_license,
            employee=self.manager_employee,
            start_date=date.today(),
            purpose='管理業務',
            assigned_by=self.admin_user
        )
        
        # Check license counts updated
        self.ide_license.refresh_from_db()
        self.office_license.refresh_from_db()
        
        self.assertEqual(self.ide_license.available_count, 8)
        self.assertEqual(self.office_license.available_count, 47)
        
        # Test cost calculations
        ide_monthly_cost = self.ide_license.calculate_monthly_cost()
        office_monthly_cost = self.office_license.calculate_monthly_cost()
        
        self.assertEqual(ide_monthly_cost, Decimal('5000.00'))  # 60000/12 * 1 used
        self.assertEqual(office_monthly_cost, Decimal('3000.00'))  # 1500 * 2 used
        
        # Test expiry detection
        expiring_license = License.objects.create(
            software_name='Expiring Software',
            license_type='Standard',
            total_count=5,
            available_count=5,
            expiry_date=date.today() + timedelta(days=15),  # Expires soon
            pricing_model='YEARLY',
            unit_price=Decimal('10000.00'),
            created_by=self.admin_user
        )
        
        self.assertTrue(expiring_license.is_expiring_soon())
        
        # Test assignment to expiring license should work but generate warning
        expiring_assignment = LicenseAssignment.objects.create(
            license=expiring_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='テスト用',
            assigned_by=self.admin_user
        )
        
        self.assertEqual(expiring_assignment.status, 'ACTIVE')
        self.assertTrue(expiring_assignment.is_expiring_soon())
    
    def test_device_assignment_workflow(self):
        """Test complete device assignment workflow."""
        # Step 1: Check device availability
        self.assertTrue(self.laptop.is_available)
        self.assertIsNone(self.laptop.current_assignment)
        
        # Step 2: Assign device
        assignment = self.laptop.assign_to_employee(
            employee=self.dev_employee,
            expected_return_date=date.today() + timedelta(days=365),
            purpose='開発業務用ラップトップ',
            assigned_by=self.admin_user
        )
        
        # Check assignment created correctly
        self.assertEqual(assignment.device, self.laptop)
        self.assertEqual(assignment.employee, self.dev_employee)
        self.assertEqual(assignment.status, 'ACTIVE')
        
        # Check device status updated
        self.laptop.refresh_from_db()
        self.assertEqual(self.laptop.status, 'ASSIGNED')
        self.assertFalse(self.laptop.is_available)
        self.assertEqual(self.laptop.current_assignment, assignment)
        
        # Step 3: Try to assign same device to another employee (should fail)
        with self.assertRaises(Exception):
            self.laptop.assign_to_employee(
                employee=self.manager_employee,
                purpose='管理業務用',
                assigned_by=self.admin_user
            )
        
        # Step 4: Return device
        return_date = date.today() + timedelta(days=30)
        returned_assignment = self.laptop.return_from_employee(
            return_date=return_date,
            returned_by=self.admin_user,
            notes='正常返却'
        )
        
        # Check return processed correctly
        self.assertEqual(returned_assignment.status, 'RETURNED')
        self.assertEqual(returned_assignment.actual_return_date, return_date)
        self.assertEqual(returned_assignment.return_notes, '正常返却')
        
        # Check device available again
        self.laptop.refresh_from_db()
        self.assertEqual(self.laptop.status, 'AVAILABLE')
        self.assertTrue(self.laptop.is_available)
        self.assertIsNone(self.laptop.current_assignment)
    
    def test_reporting_system_integration(self):
        """Test reporting system with real data."""
        # Create some assignments for reporting
        laptop_assignment = DeviceAssignment.objects.create(
            device=self.laptop,
            employee=self.dev_employee,
            assigned_date=date.today() - timedelta(days=30),
            purpose='開発業務',
            assigned_by=self.admin_user,
            status='ACTIVE'
        )
        
        desktop_assignment = DeviceAssignment.objects.create(
            device=self.desktop,
            employee=self.manager_employee,
            assigned_date=date.today() - timedelta(days=45),
            purpose='管理業務',
            assigned_by=self.admin_user,
            status='ACTIVE'
        )
        
        office_assignment = LicenseAssignment.objects.create(
            license=self.office_license,
            employee=self.dev_employee,
            start_date=date.today() - timedelta(days=60),
            purpose='オフィス業務',
            assigned_by=self.admin_user,
            status='ACTIVE'
        )
        
        ide_assignment = LicenseAssignment.objects.create(
            license=self.ide_license,
            employee=self.dev_employee,
            start_date=date.today() - timedelta(days=40),
            purpose='開発環境',
            assigned_by=self.admin_user,
            status='ACTIVE'
        )
        
        # Generate usage report
        usage_params = {
            'start_date': (date.today() - timedelta(days=90)).isoformat(),
            'end_date': date.today().isoformat(),
            'department': '開発部'
        }
        
        usage_report = ReportService.generate_usage_report(usage_params)
        
        # Verify report data
        self.assertIn('summary', usage_report)
        self.assertIn('device_usage', usage_report)
        self.assertIn('license_usage', usage_report)
        self.assertIn('department_breakdown', usage_report)
        
        summary = usage_report['summary']
        self.assertEqual(summary['total_devices'], 2)
        self.assertEqual(summary['total_licenses'], 2)
        self.assertEqual(summary['active_device_assignments'], 2)
        self.assertEqual(summary['active_license_assignments'], 2)
        
        # Generate cost analysis report
        cost_params = {
            'start_date': (date.today() - timedelta(days=90)).isoformat(),
            'end_date': date.today().isoformat()
        }
        
        cost_report = ReportService.generate_cost_analysis_report(cost_params)
        
        # Verify cost calculations
        self.assertIn('summary', cost_report)
        self.assertIn('license_costs', cost_report)
        
        summary = cost_report['summary']
        expected_monthly_cost = Decimal('6500.00')  # Office: 1500*1 + IDE: 5000*1
        self.assertEqual(summary['total_monthly_cost'], expected_monthly_cost)
        
        # Generate inventory report
        inventory_report = ReportService.generate_inventory_report({
            'include_devices': True,
            'include_licenses': True
        })
        
        # Verify inventory data
        self.assertIn('devices', inventory_report)
        self.assertIn('licenses', inventory_report)
        self.assertIn('summary', inventory_report)
        
        devices = inventory_report['devices']
        licenses = inventory_report['licenses']
        
        self.assertEqual(len(devices), 2)
        self.assertEqual(len(licenses), 2)
    
    def test_notification_system_integration(self):
        """Test notification system integration."""
        # Create expiring license
        expiring_license = License.objects.create(
            software_name='Expiring License',
            license_type='Standard',
            total_count=5,
            available_count=4,
            expiry_date=date.today() + timedelta(days=15),
            pricing_model='MONTHLY',
            unit_price=Decimal('1000.00'),
            created_by=self.admin_user
        )
        
        # Assign to employee
        assignment = LicenseAssignment.objects.create(
            license=expiring_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='テスト用',
            assigned_by=self.admin_user
        )
        
        # Create notification for expiring license
        notification = Notification.objects.create(
            title='ライセンス期限切れ警告',
            message=f'{expiring_license.software_name}のライセンスが間もなく期限切れになります。',
            notification_type='LICENSE_EXPIRY',
            priority='HIGH',
            user=self.admin_user,
            related_object_type='license',
            related_object_id=str(expiring_license.id)
        )
        
        # Verify notification created
        self.assertEqual(notification.title, 'ライセンス期限切れ警告')
        self.assertEqual(notification.priority, 'HIGH')
        self.assertFalse(notification.is_read)
        
        # Test notification for overdue device return
        overdue_assignment = DeviceAssignment.objects.create(
            device=self.desktop,
            employee=self.dev_employee,
            assigned_date=date.today() - timedelta(days=60),
            expected_return_date=date.today() - timedelta(days=1),  # Overdue
            purpose='テスト用',
            assigned_by=self.admin_user,
            status='OVERDUE'
        )
        
        overdue_notification = Notification.objects.create(
            title='デバイス返却期限超過',
            message=f'{self.desktop.serial_number}の返却期限が過ぎています。',
            notification_type='DEVICE_RETURN',
            priority='MEDIUM',
            user=self.dev_user,
            related_object_type='device_assignment',
            related_object_id=str(overdue_assignment.id)
        )
        
        # Verify overdue notification
        self.assertEqual(overdue_notification.notification_type, 'DEVICE_RETURN')
        self.assertEqual(overdue_notification.user, self.dev_user)
    
    def test_audit_trail_integration(self):
        """Test audit trail across all system operations."""
        # Track initial counts
        initial_employee_history = EmployeeHistory.objects.count()
        
        # Perform various operations
        # 1. Update employee
        self.dev_employee.department = '新開発部'
        self.dev_employee.updated_by = self.admin_user
        self.dev_employee.save()
        
        # 2. Assign device
        assignment = self.laptop.assign_to_employee(
            employee=self.dev_employee,
            purpose='部署移動後の新端末',
            assigned_by=self.admin_user
        )
        
        # 3. Assign license
        license_assignment = LicenseAssignment.objects.create(
            license=self.office_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='新部署での業務用',
            assigned_by=self.admin_user
        )
        
        # 4. Create permission override
        override = PermissionOverride.objects.create(
            employee=self.dev_employee,
            override_type='GRANT',
            resource_type='SOFTWARE',
            resource_identifier='Special Software',
            effective_from=date.today(),
            effective_until=date.today() + timedelta(days=30),
            reason='新部署での特別要件',
            created_by=self.admin_user
        )
        
        # Verify audit trails
        # Employee history should be created
        self.assertGreater(EmployeeHistory.objects.count(), initial_employee_history)
        
        dept_change_history = EmployeeHistory.objects.filter(
            employee=self.dev_employee,
            change_type='DEPARTMENT_CHANGE'
        ).first()
        self.assertIsNotNone(dept_change_history)
        self.assertEqual(dept_change_history.old_value, '開発部')
        self.assertEqual(dept_change_history.new_value, '新開発部')
        
        # Device assignment should have metadata
        self.assertEqual(assignment.assigned_by, self.admin_user)
        self.assertIsNotNone(assignment.created_at)
        
        # License assignment should have metadata
        self.assertEqual(license_assignment.assigned_by, self.admin_user)
        self.assertIsNotNone(license_assignment.created_at)
        
        # Permission override should have metadata
        self.assertEqual(override.created_by, self.admin_user)
        self.assertIsNotNone(override.created_at)
    
    def test_data_consistency_across_operations(self):
        """Test data consistency across complex operations."""
        # Initial state
        initial_laptop_status = self.laptop.status
        initial_office_available = self.office_license.available_count
        
        # Perform complex operation: assign multiple resources
        laptop_assignment = self.laptop.assign_to_employee(
            employee=self.dev_employee,
            purpose='開発業務',
            assigned_by=self.admin_user
        )
        
        office_assignment = LicenseAssignment.objects.create(
            license=self.office_license,
            employee=self.dev_employee,
            start_date=date.today(),
            purpose='オフィス業務',
            assigned_by=self.admin_user
        )
        
        # Verify state changes
        self.laptop.refresh_from_db()
        self.office_license.refresh_from_db()
        
        self.assertEqual(self.laptop.status, 'ASSIGNED')
        self.assertEqual(self.office_license.available_count, initial_office_available - 1)
        
        # Simulate system error and rollback
        try:
            # Start a transaction
            from django.db import transaction
            with transaction.atomic():
                # Assign another license
                ide_assignment = LicenseAssignment.objects.create(
                    license=self.ide_license,
                    employee=self.dev_employee,
                    start_date=date.today(),
                    purpose='開発環境',
                    assigned_by=self.admin_user
                )
                
                # Simulate error
                raise Exception("Simulated error")
                
        except Exception:
            pass  # Expected error
        
        # Verify original assignments are still intact
        self.laptop.refresh_from_db()
        self.office_license.refresh_from_db()
        self.ide_license.refresh_from_db()
        
        self.assertEqual(self.laptop.status, 'ASSIGNED')
        self.assertEqual(self.office_license.available_count, initial_office_available - 1)
        self.assertEqual(self.ide_license.available_count, 9)  # Should be unchanged
        
        # Verify assignments exist
        self.assertTrue(DeviceAssignment.objects.filter(id=laptop_assignment.id).exists())
        self.assertTrue(LicenseAssignment.objects.filter(id=office_assignment.id).exists())
        
        # The failed IDE assignment should not exist
        self.assertFalse(LicenseAssignment.objects.filter(
            license=self.ide_license,
            employee=self.dev_employee
        ).exists())


class APIIntegrationTest(APITestCase):
    """Test API integration across different endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@company.com',
            password='userpass123'
        )
        
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='テストユーザー',
            email='user@company.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today() - timedelta(days=365),
            created_by=self.admin_user
        )
    
    def test_complete_api_workflow(self):
        """Test complete workflow through API endpoints."""
        # Step 1: Admin login
        response = self.client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        admin_token = response.data['access']
        
        # Step 2: Create device via API
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        device_data = {
            'type': 'LAPTOP',
            'manufacturer': 'Dell',
            'model': 'Latitude 5520',
            'serial_number': 'API001',
            'purchase_date': (date.today() - timedelta(days=100)).isoformat(),
            'warranty_expiry': (date.today() + timedelta(days=265)).isoformat()
        }
        
        response = self.client.post('/api/devices/devices/', device_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device_id = response.data['id']
        
        # Step 3: Create license via API
        license_data = {
            'software_name': 'API Test Software',
            'license_type': 'Standard',
            'total_count': 10,
            'available_count': 10,
            'expiry_date': (date.today() + timedelta(days=365)).isoformat(),
            'pricing_model': 'MONTHLY',
            'unit_price': '1000.00'
        }
        
        response = self.client.post('/api/licenses/licenses/', license_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        license_id = response.data['id']
        
        # Step 4: Assign device via API
        assignment_data = {
            'employee_id': str(self.employee.id),
            'assigned_date': date.today().isoformat(),
            'expected_return_date': (date.today() + timedelta(days=365)).isoformat(),
            'purpose': 'API テスト用',
            'assignment_notes': 'API経由での割当'
        }
        
        response = self.client.post(f'/api/devices/devices/{device_id}/assign/', assignment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Assign license via API
        license_assignment_data = {
            'employee_id': str(self.employee.id),
            'start_date': date.today().isoformat(),
            'purpose': 'API テスト用ライセンス'
        }
        
        response = self.client.post(f'/api/licenses/licenses/{license_id}/assign/', license_assignment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 6: Generate report via API
        report_data = {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat(),
            'format': 'json'
        }
        
        response = self.client.post('/api/reports/generate/usage/', report_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        
        # Step 7: Regular user login and check their resources
        response = self.client.post('/api/auth/login/', {
            'username': 'user',
            'password': 'userpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_token = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        
        # Check user's device assignments
        response = self.client.get('/api/devices/device-assignments/my_assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Check user's license assignments
        response = self.client.get('/api/licenses/license-assignments/my_assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_api_error_handling(self):
        """Test API error handling across endpoints."""
        # Test unauthenticated access
        response = self.client.get('/api/devices/devices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test unauthorized access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/devices/devices/', {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test invalid data
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/devices/devices/', {
            'type': 'INVALID_TYPE',
            'manufacturer': '',
            'serial_number': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', response.data)
    
    def test_api_pagination_and_filtering(self):
        """Test API pagination and filtering."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create multiple devices
        for i in range(15):
            Device.objects.create(
                type='LAPTOP',
                manufacturer='Dell',
                model=f'Model {i}',
                serial_number=f'SN{i:03d}',
                purchase_date=date.today() - timedelta(days=100),
                warranty_expiry=date.today() + timedelta(days=265),
                created_by=self.admin_user
            )
        
        # Test pagination
        response = self.client.get('/api/devices/devices/?page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)
        
        # Test filtering
        response = self.client.get('/api/devices/devices/?type=LAPTOP')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for device in response.data['results']:
            self.assertEqual(device['type'], 'LAPTOP')
        
        # Test search
        response = self.client.get('/api/devices/devices/?search=Model 5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
    
    def test_api_performance(self):
        """Test API performance with multiple requests."""
        import time
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test data
        for i in range(50):
            Device.objects.create(
                type='LAPTOP',
                manufacturer='Dell',
                model=f'Performance Model {i}',
                serial_number=f'PERF{i:03d}',
                purchase_date=date.today() - timedelta(days=100),
                warranty_expiry=date.today() + timedelta(days=265),
                created_by=self.admin_user
            )
        
        # Measure API response time
        start_time = time.time()
        
        for i in range(10):
            response = self.client.get('/api/devices/devices/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        avg_response_time = (end_time - start_time) / 10
        
        # Should respond within reasonable time
        self.assertLess(avg_response_time, 1.0, "API response time too slow")


class SecurityIntegrationTest(APITestCase):
    """Test security features integration."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@company.com',
            password='userpass123'
        )
    
    def test_authentication_security(self):
        """Test authentication security features."""
        # Test account lockout
        for i in range(5):
            response = self.client.post('/api/auth/login/', {
                'username': 'user',
                'password': 'wrongpassword'
            })
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # User should be locked now
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_account_locked)
        
        # Even correct password should fail
        response = self.client.post('/api/auth/login/', {
            'username': 'user',
            'password': 'userpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authorization_security(self):
        """Test authorization security across endpoints."""
        # Regular user should not access admin endpoints
        self.client.force_authenticate(user=self.regular_user)
        
        admin_endpoints = [
            '/api/auth/users/',
            '/api/employees/employees/',
            '/api/devices/devices/',
            '/api/licenses/licenses/',
            '/api/reports/generate/usage/'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED])
    
    def test_data_access_security(self):
        """Test data access security and isolation."""
        # Create employees for different users
        employee1 = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='User Employee',
            email='user@company.com',
            department='IT',
            position='Developer',
            location='TOKYO',
            hire_date=date.today(),
            created_by=self.admin_user
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@company.com',
            password='otherpass123'
        )
        
        employee2 = Employee.objects.create(
            user=other_user,
            employee_id='EMP002',
            name='Other Employee',
            email='other@company.com',
            department='Sales',
            position='Sales Rep',
            location='OKINAWA',
            hire_date=date.today(),
            created_by=self.admin_user
        )
        
        # Regular user should only see their own data
        self.client.force_authenticate(user=self.regular_user)
        
        # This would need to be implemented in the actual views
        # For now, we're testing the concept
        response = self.client.get('/api/dashboard/my_resources/')
        if response.status_code == status.HTTP_200_OK:
            # Should only contain data for the authenticated user
            pass  # Implementation would verify user isolation
    
    def test_input_validation_security(self):
        """Test input validation security."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE devices; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null\x00byte"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.get(f'/api/devices/devices/?search={malicious_input}')
            # Should not cause server error
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_rate_limiting(self):
        """Test rate limiting (conceptual - would need actual implementation)."""
        # This would test rate limiting if implemented
        # For now, we test that multiple requests don't cause issues
        
        for i in range(100):
            response = self.client.post('/api/auth/login/', {
                'username': 'nonexistent',
                'password': 'password'
            })
            # Should handle multiple requests gracefully
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)