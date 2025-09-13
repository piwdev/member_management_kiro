"""
Unit tests for employee models and serializers.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
import uuid

from .models import Employee, EmployeeHistory
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer,
    EmployeeCreateSerializer, EmployeeUpdateSerializer,
    EmployeeTerminationSerializer
)

User = get_user_model()


class EmployeeModelTest(TestCase):
    """Test cases for Employee model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_create_employee(self):
        """Test creating a new employee."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            name_kana='タナカタロウ',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            phone_number='090-1234-5678',
            created_by=self.admin_user
        )
        
        self.assertEqual(employee.employee_id, 'EMP001')
        self.assertEqual(employee.name, '田中太郎')
        self.assertEqual(employee.department, '開発部')
        self.assertEqual(employee.status, 'ACTIVE')
        self.assertTrue(employee.is_active)
        self.assertEqual(str(employee), 'EMP001 - 田中太郎')
    
    def test_employee_id_uniqueness(self):
        """Test that employee ID must be unique."""
        Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1)
        )
        
        # Create another user for the second employee
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            Employee.objects.create(
                user=user2,
                employee_id='EMP001',  # Duplicate employee ID
                name='佐藤花子',
                email='sato@example.com',
                department='営業部',
                position='営業',
                location='OKINAWA',
                hire_date=date(2023, 4, 1)
            )
    
    def test_email_uniqueness(self):
        """Test that email must be unique."""
        Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1)
        )
        
        # Create another user for the second employee
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            Employee.objects.create(
                user=user2,
                employee_id='EMP002',
                name='佐藤花子',
                email='tanaka@example.com',  # Duplicate email
                department='営業部',
                position='営業',
                location='OKINAWA',
                hire_date=date(2023, 4, 1)
            )
    
    def test_full_name_with_kana_property(self):
        """Test full_name_with_kana property."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            name_kana='タナカタロウ',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1)
        )
        
        self.assertEqual(employee.full_name_with_kana, '田中太郎 (タナカタロウ)')
        
        # Test without kana
        employee.name_kana = ''
        self.assertEqual(employee.full_name_with_kana, '田中太郎')
    
    def test_is_active_property(self):
        """Test is_active property."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1)
        )
        
        # Active employee
        self.assertTrue(employee.is_active)
        
        # Inactive status
        employee.status = 'INACTIVE'
        employee.save()
        self.assertFalse(employee.is_active)
        
        # Active status but terminated
        employee.status = 'ACTIVE'
        employee.termination_date = date.today() - timedelta(days=1)
        employee.save()
        self.assertFalse(employee.is_active)
    
    def test_terminate_employment(self):
        """Test employee termination."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1)
        )
        
        # Terminate employment
        termination_date = date.today()
        employee.terminate_employment(
            termination_date=termination_date,
            terminated_by=self.admin_user
        )
        
        employee.refresh_from_db()
        self.assertEqual(employee.termination_date, termination_date)
        self.assertEqual(employee.status, 'INACTIVE')
        self.assertFalse(employee.is_active)
        
        # Check history record was created
        history = EmployeeHistory.objects.filter(
            employee=employee,
            change_type='TERMINATION'
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.changed_by, self.admin_user)
    
    def test_reactivate_employment(self):
        """Test employee reactivation."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            status='INACTIVE',
            termination_date=date.today() - timedelta(days=30)
        )
        
        # Reactivate employment
        employee.reactivate_employment(reactivated_by=self.admin_user)
        
        employee.refresh_from_db()
        self.assertIsNone(employee.termination_date)
        self.assertEqual(employee.status, 'ACTIVE')
        self.assertTrue(employee.is_active)
        
        # Check history record was created
        history = EmployeeHistory.objects.filter(
            employee=employee,
            change_type='REACTIVATION'
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.changed_by, self.admin_user)


class EmployeeHistoryModelTest(TestCase):
    """Test cases for EmployeeHistory model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            created_by=self.admin_user
        )
    
    def test_create_history_record(self):
        """Test creating a history record."""
        history = EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='UPDATE',
            field_name='department',
            old_value='開発部',
            new_value='営業部',
            changed_by=self.admin_user,
            notes='部署異動'
        )
        
        self.assertEqual(history.employee, self.employee)
        self.assertEqual(history.change_type, 'UPDATE')
        self.assertEqual(history.field_name, 'department')
        self.assertEqual(history.old_value, '開発部')
        self.assertEqual(history.new_value, '営業部')
        self.assertEqual(history.changed_by, self.admin_user)
        self.assertEqual(str(history), f'{self.employee.name} - 更新 ({history.changed_at})')
    
    def test_history_ordering(self):
        """Test that history records are ordered by changed_at descending."""
        # Create multiple history records
        history1 = EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='CREATE',
            changed_by=self.admin_user
        )
        
        history2 = EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='UPDATE',
            field_name='position',
            old_value='エンジニア',
            new_value='シニアエンジニア',
            changed_by=self.admin_user
        )
        
        # Get all history records
        history_records = list(EmployeeHistory.objects.all())
        
        # Should be ordered by changed_at descending (newest first)
        self.assertEqual(history_records[0], history2)
        self.assertEqual(history_records[1], history1)


class EmployeeSerializerTest(TestCase):
    """Test cases for Employee serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            name='田中太郎',
            name_kana='タナカタロウ',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            phone_number='090-1234-5678',
            created_by=self.admin_user
        )
    
    def test_employee_list_serializer(self):
        """Test EmployeeListSerializer."""
        serializer = EmployeeListSerializer(self.employee)
        data = serializer.data
        
        self.assertEqual(data['employee_id'], 'EMP001')
        self.assertEqual(data['name'], '田中太郎')
        self.assertEqual(data['email'], 'tanaka@example.com')
        self.assertEqual(data['department'], '開発部')
        self.assertEqual(data['location'], 'TOKYO')
        self.assertEqual(data['location_display'], '東京')
        self.assertEqual(data['status'], 'ACTIVE')
        self.assertEqual(data['status_display'], 'アクティブ')
        self.assertTrue(data['is_active'])
    
    def test_employee_detail_serializer(self):
        """Test EmployeeDetailSerializer."""
        serializer = EmployeeDetailSerializer(self.employee)
        data = serializer.data
        
        self.assertEqual(data['employee_id'], 'EMP001')
        self.assertEqual(data['name'], '田中太郎')
        self.assertEqual(data['name_kana'], 'タナカタロウ')
        self.assertEqual(data['full_name_with_kana'], '田中太郎 (タナカタロウ)')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertIn('history_records', data)
    
    def test_employee_create_serializer_valid_data(self):
        """Test EmployeeCreateSerializer with valid data."""
        data = {
            'employee_id': 'EMP002',
            'name': '佐藤花子',
            'name_kana': 'サトウハナコ',
            'email': 'sato@example.com',
            'department': '営業部',
            'position': '営業',
            'location': 'OKINAWA',
            'hire_date': '2023-04-01',
            'phone_number': '090-9876-5432',
            'username': 'sato',
            'password': 'password123'
        }
        
        # Mock request context
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        serializer = EmployeeCreateSerializer(
            data=data,
            context={'request': MockRequest(self.admin_user)}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        employee = serializer.save()
        
        self.assertEqual(employee.employee_id, 'EMP002')
        self.assertEqual(employee.name, '佐藤花子')
        self.assertEqual(employee.email, 'sato@example.com')
        self.assertEqual(employee.created_by, self.admin_user)
        
        # Check that user account was created
        user = User.objects.get(username='sato')
        self.assertEqual(user.email, 'sato@example.com')
        self.assertEqual(user.employee_id, 'EMP002')
        
        # Check that history record was created
        history = EmployeeHistory.objects.filter(
            employee=employee,
            change_type='CREATE'
        ).first()
        self.assertIsNotNone(history)
    
    def test_employee_create_serializer_duplicate_employee_id(self):
        """Test EmployeeCreateSerializer with duplicate employee ID."""
        data = {
            'employee_id': 'EMP001',  # Already exists
            'name': '佐藤花子',
            'email': 'sato@example.com',
            'department': '営業部',
            'position': '営業',
            'location': 'OKINAWA',
            'hire_date': '2023-04-01',
            'username': 'sato',
            'password': 'password123'
        }
        
        serializer = EmployeeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('employee_id', serializer.errors)
    
    def test_employee_create_serializer_duplicate_email(self):
        """Test EmployeeCreateSerializer with duplicate email."""
        data = {
            'employee_id': 'EMP002',
            'name': '佐藤花子',
            'email': 'tanaka@example.com',  # Already exists
            'department': '営業部',
            'position': '営業',
            'location': 'OKINAWA',
            'hire_date': '2023-04-01',
            'username': 'sato',
            'password': 'password123'
        }
        
        serializer = EmployeeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_employee_create_serializer_future_hire_date(self):
        """Test EmployeeCreateSerializer with future hire date."""
        future_date = date.today() + timedelta(days=30)
        data = {
            'employee_id': 'EMP002',
            'name': '佐藤花子',
            'email': 'sato@example.com',
            'department': '営業部',
            'position': '営業',
            'location': 'OKINAWA',
            'hire_date': future_date.isoformat(),
            'username': 'sato',
            'password': 'password123'
        }
        
        serializer = EmployeeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('hire_date', serializer.errors)
    
    def test_employee_update_serializer(self):
        """Test EmployeeUpdateSerializer."""
        data = {
            'name': '田中太郎（更新）',
            'department': '営業部',
            'position': 'マネージャー',
            'phone_number': '090-1111-2222'
        }
        
        # Mock request context
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        serializer = EmployeeUpdateSerializer(
            self.employee,
            data=data,
            partial=True,
            context={'request': MockRequest(self.admin_user)}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_employee = serializer.save()
        
        self.assertEqual(updated_employee.name, '田中太郎（更新）')
        self.assertEqual(updated_employee.department, '営業部')
        self.assertEqual(updated_employee.position, 'マネージャー')
        self.assertEqual(updated_employee.updated_by, self.admin_user)
        
        # Check that history records were created for changes
        history_records = EmployeeHistory.objects.filter(
            employee=updated_employee,
            change_type__in=['UPDATE', 'DEPARTMENT_CHANGE', 'POSITION_CHANGE']
        )
        self.assertTrue(history_records.exists())
    
    def test_employee_termination_serializer(self):
        """Test EmployeeTerminationSerializer."""
        data = {
            'termination_date': date.today().isoformat(),
            'notes': '自己都合退職'
        }
        
        # Mock request context
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        serializer = EmployeeTerminationSerializer(
            data=data,
            context={'request': MockRequest(self.admin_user)}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        terminated_employee = serializer.save(self.employee)
        
        terminated_employee.refresh_from_db()
        self.assertEqual(terminated_employee.status, 'INACTIVE')
        self.assertEqual(terminated_employee.termination_date, date.today())
        self.assertFalse(terminated_employee.is_active)
        
        # Check that termination history record was created
        history = EmployeeHistory.objects.filter(
            employee=terminated_employee,
            change_type='TERMINATION'
        ).first()
        self.assertIsNotNone(history)
        self.assertIn('自己都合退職', history.notes)
    
    def test_employee_termination_serializer_future_date(self):
        """Test EmployeeTerminationSerializer with future termination date."""
        future_date = date.today() + timedelta(days=30)
        data = {
            'termination_date': future_date.isoformat()
        }
        
        serializer = EmployeeTerminationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('termination_date', serializer.errors)


class EmployeeAPITest(APITestCase):
    """Test cases for Employee API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create employee for regular user
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='田中太郎',
            name_kana='タナカタロウ',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            created_by=self.admin_user
        )
        
        # Create another employee
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.other_employee = Employee.objects.create(
            user=self.other_user,
            employee_id='EMP002',
            name='佐藤花子',
            email='sato@example.com',
            department='営業部',
            position='営業',
            location='OKINAWA',
            hire_date=date(2023, 5, 1),
            created_by=self.admin_user
        )
    
    def test_employee_list_as_admin(self):
        """Test employee list endpoint as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/employees/employees/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that both employees are returned
        employee_ids = [emp['employee_id'] for emp in response.data['results']]
        self.assertIn('EMP001', employee_ids)
        self.assertIn('EMP002', employee_ids)
    
    def test_employee_list_as_regular_user(self):
        """Test employee list endpoint as regular user."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/employees/employees/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Regular users can see active employees
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_employee_list_unauthenticated(self):
        """Test employee list endpoint without authentication."""
        response = self.client.get('/api/employees/employees/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_employee_detail(self):
        """Test employee detail endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/employees/employees/{self.employee.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], 'EMP001')
        self.assertEqual(response.data['name'], '田中太郎')
        self.assertIn('history_records', response.data)
    
    def test_employee_create_as_admin(self):
        """Test creating employee as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'employee_id': 'EMP003',
            'name': '山田次郎',
            'name_kana': 'ヤマダジロウ',
            'email': 'yamada@example.com',
            'department': 'マーケティング部',
            'position': 'マネージャー',
            'location': 'REMOTE',
            'hire_date': '2023-06-01',
            'phone_number': '090-1111-2222',
            'username': 'yamada',
            'password': 'password123'
        }
        
        response = self.client.post('/api/employees/employees/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['employee_id'], 'EMP003')
        self.assertEqual(response.data['name'], '山田次郎')
        
        # Check that user account was created
        user = User.objects.get(username='yamada')
        self.assertEqual(user.email, 'yamada@example.com')
        
        # Check that employee was created
        employee = Employee.objects.get(employee_id='EMP003')
        self.assertEqual(employee.name, '山田次郎')
        self.assertEqual(employee.created_by, self.admin_user)
    
    def test_employee_create_as_regular_user(self):
        """Test creating employee as regular user (should fail)."""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'employee_id': 'EMP003',
            'name': '山田次郎',
            'email': 'yamada@example.com',
            'department': 'マーケティング部',
            'position': 'マネージャー',
            'location': 'REMOTE',
            'hire_date': '2023-06-01',
            'username': 'yamada',
            'password': 'password123'
        }
        
        response = self.client.post('/api/employees/employees/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_employee_update_as_admin(self):
        """Test updating employee as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'name': '田中太郎（更新）',
            'department': '営業部',
            'position': 'シニアエンジニア'
        }
        
        response = self.client.patch(f'/api/employees/employees/{self.employee.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '田中太郎（更新）')
        self.assertEqual(response.data['department'], '営業部')
        
        # Check that employee was updated
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.name, '田中太郎（更新）')
        self.assertEqual(self.employee.updated_by, self.admin_user)
        
        # Check that history records were created
        history_records = EmployeeHistory.objects.filter(employee=self.employee)
        self.assertTrue(history_records.exists())
    
    def test_employee_terminate(self):
        """Test employee termination endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'termination_date': date.today().isoformat(),
            'notes': '自己都合退職'
        }
        
        response = self.client.post(f'/api/employees/employees/{self.employee.id}/terminate/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Check that employee was terminated
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, 'INACTIVE')
        self.assertEqual(self.employee.termination_date, date.today())
        
        # Check that history record was created
        history = EmployeeHistory.objects.filter(
            employee=self.employee,
            change_type='TERMINATION'
        ).first()
        self.assertIsNotNone(history)
        self.assertIn('自己都合退職', history.notes)
    
    def test_employee_terminate_already_terminated(self):
        """Test terminating already terminated employee."""
        self.client.force_authenticate(user=self.admin_user)
        
        # First terminate the employee
        self.employee.terminate_employment(terminated_by=self.admin_user)
        
        data = {
            'termination_date': date.today().isoformat()
        }
        
        response = self.client.post(f'/api/employees/employees/{self.employee.id}/terminate/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_employee_reactivate(self):
        """Test employee reactivation endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        # First terminate the employee
        self.employee.terminate_employment(terminated_by=self.admin_user)
        
        response = self.client.post(f'/api/employees/employees/{self.employee.id}/reactivate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Check that employee was reactivated
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, 'ACTIVE')
        self.assertIsNone(self.employee.termination_date)
        
        # Check that history record was created
        history = EmployeeHistory.objects.filter(
            employee=self.employee,
            change_type='REACTIVATION'
        ).first()
        self.assertIsNotNone(history)
    
    def test_employee_reactivate_active_employee(self):
        """Test reactivating active employee (should fail)."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(f'/api/employees/employees/{self.employee.id}/reactivate/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_employee_history(self):
        """Test employee history endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create some history records
        EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='UPDATE',
            field_name='department',
            old_value='開発部',
            new_value='営業部',
            changed_by=self.admin_user
        )
        
        response = self.client.get(f'/api/employees/employees/{self.employee.id}/history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) > 0)
    
    def test_employee_statistics(self):
        """Test employee statistics endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/employees/employees/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_employees', response.data)
        self.assertIn('active_employees', response.data)
        self.assertIn('department_breakdown', response.data)
        self.assertIn('location_breakdown', response.data)
        self.assertEqual(response.data['total_employees'], 2)
        self.assertEqual(response.data['active_employees'], 2)
    
    def test_employee_statistics_as_regular_user(self):
        """Test employee statistics endpoint as regular user (should fail)."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/employees/employees/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_my_profile(self):
        """Test my profile endpoint."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/employees/employees/my_profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], 'EMP001')
        self.assertEqual(response.data['name'], '田中太郎')
    
    def test_my_profile_no_employee_profile(self):
        """Test my profile endpoint for user without employee profile."""
        # Create user without employee profile
        user_without_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@example.com',
            password='password123'
        )
        
        self.client.force_authenticate(user=user_without_profile)
        
        response = self.client.get('/api/employees/employees/my_profile/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_search_suggestions(self):
        """Test search suggestions endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/employees/employees/search_suggestions/?q=田中')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertTrue(len(response.data['suggestions']) > 0)
        self.assertEqual(response.data['suggestions'][0]['name'], '田中太郎')
    
    def test_search_suggestions_short_query(self):
        """Test search suggestions with short query."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/employees/employees/search_suggestions/?q=田')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['suggestions'], [])
    
    def test_employee_filtering(self):
        """Test employee filtering by various parameters."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter by department
        response = self.client.get('/api/employees/employees/?department=開発部')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['department'], '開発部')
        
        # Filter by location
        response = self.client.get('/api/employees/employees/?location=TOKYO')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['location'], 'TOKYO')
        
        # Filter by status
        response = self.client.get('/api/employees/employees/?status=ACTIVE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_employee_search(self):
        """Test employee search functionality."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Search by name
        response = self.client.get('/api/employees/employees/?search=田中')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '田中太郎')
        
        # Search by employee ID
        response = self.client.get('/api/employees/employees/?search=EMP001')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['employee_id'], 'EMP001')
    
    def test_employee_ordering(self):
        """Test employee ordering functionality."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Order by name
        response = self.client.get('/api/employees/employees/?ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [emp['name'] for emp in response.data['results']]
        self.assertEqual(names, sorted(names))
        
        # Order by employee_id descending
        response = self.client.get('/api/employees/employees/?ordering=-employee_id')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        employee_ids = [emp['employee_id'] for emp in response.data['results']]
        self.assertEqual(employee_ids, sorted(employee_ids, reverse=True))


class EmployeeHistoryAPITest(APITestCase):
    """Test cases for Employee History API endpoints."""
    
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
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            user=self.regular_user,
            employee_id='EMP001',
            name='田中太郎',
            email='tanaka@example.com',
            department='開発部',
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            created_by=self.admin_user
        )
        
        # Create history records
        self.history1 = EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='CREATE',
            changed_by=self.admin_user,
            notes='社員レコード作成'
        )
        
        self.history2 = EmployeeHistory.objects.create(
            employee=self.employee,
            change_type='UPDATE',
            field_name='department',
            old_value='開発部',
            new_value='営業部',
            changed_by=self.admin_user
        )
    
    def test_history_list_as_admin(self):
        """Test history list endpoint as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/employees/employee-history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_history_list_as_regular_user_same_department(self):
        """Test history list as regular user in same department."""
        # Create a new user and employee profile for regular user in same department
        regular_user_2 = User.objects.create_user(
            username='regular2',
            email='regular2@example.com',
            password='regularpass123'
        )
        
        Employee.objects.create(
            user=regular_user_2,
            employee_id='EMP999',
            name='Regular User',
            email='regular2@example.com',
            department='開発部',  # Same department as the employee in history
            position='エンジニア',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=regular_user_2)
        
        response = self.client.get('/api/employees/employee-history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see history for employees in same department
        self.assertIn('results', response.data)
    
    def test_history_list_as_regular_user_different_department(self):
        """Test history list as regular user in different department."""
        # Create a new user and employee profile for regular user in different department
        regular_user_3 = User.objects.create_user(
            username='regular3',
            email='regular3@example.com',
            password='regularpass123'
        )
        
        Employee.objects.create(
            user=regular_user_3,
            employee_id='EMP998',
            name='Regular User 3',
            email='regular3@example.com',
            department='営業部',  # Different department
            position='営業',
            location='TOKYO',
            hire_date=date(2023, 4, 1),
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=regular_user_3)
        
        response = self.client.get('/api/employees/employee-history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not see history for employees in different department
        self.assertEqual(len(response.data['results']), 0)
    
    def test_history_detail(self):
        """Test history detail endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/employees/employee-history/{self.history1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['change_type'], 'CREATE')
        self.assertEqual(response.data['notes'], '社員レコード作成')
    
    def test_history_filtering(self):
        """Test history filtering by various parameters."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter by employee
        response = self.client.get(f'/api/employees/employee-history/?employee={self.employee.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Filter by change type
        response = self.client.get('/api/employees/employee-history/?change_type=CREATE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['change_type'], 'CREATE')
    
    def test_history_ordering(self):
        """Test history ordering functionality."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Default ordering should be by changed_at descending (newest first)
        response = self.client.get('/api/employees/employee-history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # The second history record should come first (newer)
        self.assertEqual(response.data['results'][0]['change_type'], 'UPDATE')
        self.assertEqual(response.data['results'][1]['change_type'], 'CREATE')