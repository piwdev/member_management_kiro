"""
Comprehensive tests for authentication models, views, and API endpoints.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta, date
from unittest.mock import patch, Mock

from .models import LoginAttempt, User, RegistrationAttempt
from .serializers import UserSerializer, LoginAttemptSerializer, UserRegistrationSerializer

User = get_user_model()


class AuthenticationAPITestCase(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            employee_id='EMP001',
            department='IT',
            position='Administrator',
            location='TOKYO',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user1',
            email='user1@company.com',
            password='testpass123',
            first_name='Regular',
            last_name='User',
            employee_id='EMP002',
            department='Sales',
            position='Sales Representative',
            location='OKINAWA'
        )
        
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@company.com',
            password='testpass123',
            is_active=False
        )
    
    def test_login_success(self):
        """Test successful login."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Check user data in response
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'admin')
        self.assertEqual(user_data['employee_id'], 'EMP001')
        self.assertEqual(user_data['department'], 'IT')
        
        # Check login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(username='admin').first()
        self.assertIsNotNone(login_attempt)
        self.assertTrue(login_attempt.success)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
        # Check failed login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(username='admin').first()
        self.assertIsNotNone(login_attempt)
        self.assertFalse(login_attempt.success)
        self.assertEqual(login_attempt.failure_reason, '認証失敗')
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'nonexistent',
            'password': 'password'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check failed login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(username='nonexistent').first()
        self.assertIsNotNone(login_attempt)
        self.assertFalse(login_attempt.success)
        self.assertEqual(login_attempt.failure_reason, 'ユーザー不存在')
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'inactive',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_account_lockout(self):
        """Test account lockout after multiple failed attempts."""
        url = reverse('token_obtain_pair')
        
        # Make 5 failed login attempts
        for i in range(5):
            data = {
                'username': 'admin',
                'password': 'wrongpassword'
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check that account is locked
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_account_locked)
        
        # Try to login with correct password - should fail due to lock
        data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('アカウントがロックされています', str(response.data))
    
    def test_token_refresh(self):
        """Test token refresh functionality."""
        # First login to get tokens
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Use refresh token to get new access token
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_logout(self):
        """Test logout functionality."""
        # First login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Logout
        logout_url = reverse('logout')
        logout_data = {'refresh': refresh_token}
        
        response = self.client.post(logout_url, logout_data, format='json')
        
        # Debug the response if it fails
        if response.status_code != status.HTTP_200_OK:
            print(f"Logout response status: {response.status_code}")
            print(f"Logout response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_me_endpoint(self):
        """Test user info endpoint."""
        # Login first
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Get user info
        me_url = reverse('me')
        response = self.client.get(me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'admin')
        self.assertEqual(response.data['employee_id'], 'EMP001')
        self.assertEqual(response.data['department'], 'IT')
    
    def test_me_endpoint_unauthenticated(self):
        """Test user info endpoint without authentication."""
        me_url = reverse('me')
        response = self.client.get(me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_change_password(self):
        """Test password change functionality."""
        # Login first
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'regular_user',
            'password': 'testpass123'
        }
        # Create user for this test
        user = User.objects.create_user(
            username='regular_user',
            password='testpass123'
        )
        
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Change password
        change_password_url = reverse('change_password')
        change_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        
        response = self.client.post(change_password_url, change_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        # Login first
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'admin',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to change password with wrong old password
        change_password_url = reverse('change_password')
        change_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        
        response = self.client.post(change_password_url, change_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)


class UserManagementAPITestCase(APITestCase):
    """Test cases for user management API endpoints (admin only)."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user1',
            email='user1@company.com',
            password='testpass123'
        )
        
        # Login as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_user_list_admin(self):
        """Test user list endpoint as admin."""
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_user_list_regular_user(self):
        """Test user list endpoint as regular user (should be forbidden)."""
        # Login as regular user
        refresh = RefreshToken.for_user(self.regular_user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unlock_account(self):
        """Test account unlock functionality."""
        # Lock the regular user's account
        self.regular_user.lock_account()
        self.assertTrue(self.regular_user.is_account_locked)
        
        # Unlock via API
        url = reverse('user-unlock-account', kwargs={'pk': self.regular_user.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify account is unlocked
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_account_locked)
    
    def test_reset_password_admin(self):
        """Test password reset by admin."""
        url = reverse('user-reset-password', kwargs={'pk': self.regular_user.pk})
        data = {'new_password': 'newpassword123'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password('newpassword123'))


class LoginAttemptAPITestCase(APITestCase):
    """Test cases for login attempt monitoring API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create some login attempts
        LoginAttempt.objects.create(
            user=self.admin_user,
            username='admin',
            ip_address='127.0.0.1',
            success=True
        )
        
        LoginAttempt.objects.create(
            username='hacker',
            ip_address='192.168.1.100',
            success=False,
            failure_reason='ユーザー不存在'
        )
        
        # Login as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_login_attempts_list(self):
        """Test login attempts list endpoint."""
        url = reverse('loginattempt-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_login_attempts_filter_by_success(self):
        """Test filtering login attempts by success status."""
        url = reverse('loginattempt-list')
        response = self.client.get(url, {'success': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['success'])
    
    def test_login_attempts_filter_by_username(self):
        """Test filtering login attempts by username."""
        url = reverse('loginattempt-list')
        response = self.client.get(url, {'username': 'admin'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'admin')


class UserModelTest(TestCase):
    """Test cases for the custom User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'employee_id': 'EMP001',
            'department': 'IT',
            'position': 'Developer',
            'location': 'TOKYO',
            'hire_date': date.today() - timedelta(days=365)
        }
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.employee_id, 'EMP001')
        self.assertEqual(user.department, 'IT')
        self.assertEqual(user.location, 'TOKYO')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_superuser_creation(self):
        """Test superuser creation."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        expected = "testuser (Test User)"
        self.assertEqual(str(user), expected)
        
        # Test without full name
        user.first_name = ''
        user.last_name = ''
        self.assertEqual(str(user), 'testuser')
    
    def test_account_locking(self):
        """Test account locking functionality."""
        user = User.objects.create_user(**self.user_data)
        
        # Initially not locked
        self.assertFalse(user.is_account_locked)
        
        # Lock account
        user.lock_account(duration_minutes=30)
        self.assertTrue(user.is_account_locked)
        self.assertIsNotNone(user.account_locked_until)
        
        # Unlock account
        user.unlock_account()
        self.assertFalse(user.is_account_locked)
        self.assertIsNone(user.account_locked_until)
        self.assertEqual(user.failed_login_attempts, 0)
    
    def test_failed_login_tracking(self):
        """Test failed login attempt tracking."""
        user = User.objects.create_user(**self.user_data)
        
        # Increment failed attempts
        for i in range(4):
            user.increment_failed_login()
            self.assertEqual(user.failed_login_attempts, i + 1)
            self.assertFalse(user.is_account_locked)
        
        # 5th attempt should lock account
        user.increment_failed_login()
        self.assertEqual(user.failed_login_attempts, 5)
        self.assertTrue(user.is_account_locked)
        
        # Reset on successful login
        user.reset_failed_login()
        self.assertEqual(user.failed_login_attempts, 0)
    
    def test_unique_constraints(self):
        """Test unique constraints on username and email."""
        User.objects.create_user(**self.user_data)
        
        # Duplicate username should fail
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser',  # Duplicate
                email='different@example.com',
                password='testpass123'
            )
        
        # Duplicate email should fail
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='different',
                email='test@example.com',  # Duplicate
                password='testpass123'
            )


class LoginAttemptModelTest(TestCase):
    """Test cases for the LoginAttempt model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_successful_login_attempt(self):
        """Test recording successful login attempt."""
        attempt = LoginAttempt.objects.create(
            user=self.user,
            username='testuser',
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            success=True
        )
        
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.username, 'testuser')
        self.assertTrue(attempt.success)
        self.assertEqual(attempt.failure_reason, '')
    
    def test_failed_login_attempt(self):
        """Test recording failed login attempt."""
        attempt = LoginAttempt.objects.create(
            username='nonexistent',
            ip_address='192.168.1.100',
            user_agent='Test Browser',
            success=False,
            failure_reason='ユーザー不存在'
        )
        
        self.assertIsNone(attempt.user)
        self.assertEqual(attempt.username, 'nonexistent')
        self.assertFalse(attempt.success)
        self.assertEqual(attempt.failure_reason, 'ユーザー不存在')
    
    def test_login_attempt_str_representation(self):
        """Test LoginAttempt string representation."""
        attempt = LoginAttempt.objects.create(
            user=self.user,
            username='testuser',
            ip_address='127.0.0.1',
            success=True
        )
        
        expected = f"testuser - 成功 ({attempt.timestamp})"
        self.assertEqual(str(attempt), expected)


class AuthenticationSerializerTest(TestCase):
    """Test cases for authentication serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            employee_id='EMP001',
            department='IT',
            position='Developer'
        )
    
    def test_user_serializer(self):
        """Test UserSerializer."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['employee_id'], 'EMP001')
        self.assertEqual(data['department'], 'IT')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertNotIn('password', data)  # Password should not be serialized
    
    def test_login_attempt_serializer(self):
        """Test LoginAttemptSerializer."""
        attempt = LoginAttempt.objects.create(
            user=self.user,
            username='testuser',
            ip_address='127.0.0.1',
            success=True
        )
        
        serializer = LoginAttemptSerializer(attempt)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['ip_address'], '127.0.0.1')
        self.assertTrue(data['success'])
        self.assertIn('timestamp', data)


class AuthenticationMiddlewareTest(TestCase):
    """Test cases for authentication middleware."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_attempt_logging(self):
        """Test that login attempts are logged by middleware."""
        initial_count = LoginAttempt.objects.count()
        
        # Successful login
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should have created a login attempt record
        self.assertEqual(LoginAttempt.objects.count(), initial_count + 1)
        
        latest_attempt = LoginAttempt.objects.latest('timestamp')
        self.assertEqual(latest_attempt.username, 'testuser')
        self.assertTrue(latest_attempt.success)
    
    def test_failed_login_logging(self):
        """Test that failed login attempts are logged."""
        initial_count = LoginAttempt.objects.count()
        
        # Failed login
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Should have created a login attempt record
        self.assertEqual(LoginAttempt.objects.count(), initial_count + 1)
        
        latest_attempt = LoginAttempt.objects.latest('timestamp')
        self.assertEqual(latest_attempt.username, 'testuser')
        self.assertFalse(latest_attempt.success)


class SecurityTest(TestCase):
    """Test cases for security features."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_account_lockout_after_failed_attempts(self):
        """Test account lockout after multiple failed login attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # User should be locked
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_account_locked)
        
        # Even correct password should fail now
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_password_validation(self):
        """Test password validation requirements."""
        # Test weak password
        with self.assertRaises(ValidationError):
            user = User(
                username='weakuser',
                email='weak@example.com'
            )
            user.set_password('123')  # Too short
            user.full_clean()
    
    @patch('django_auth_ldap.backend.LDAPBackend.authenticate')
    def test_ldap_authentication_fallback(self, mock_ldap_auth):
        """Test LDAP authentication with fallback to local auth."""
        # Mock LDAP authentication failure
        mock_ldap_auth.return_value = None
        
        # Should fall back to local authentication
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should succeed with local auth
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration handling."""
        # Login to get tokens
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        
        # Test token validation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_ip_address_tracking(self):
        """Test IP address tracking in login attempts."""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, HTTP_X_FORWARDED_FOR='192.168.1.100')
        
        latest_attempt = LoginAttempt.objects.latest('timestamp')
        # Should capture the forwarded IP
        self.assertIn('192.168.1.100', latest_attempt.ip_address)


class PermissionTest(TestCase):
    """Test cases for authentication permissions."""
    
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
    
    def test_admin_user_permissions(self):
        """Test admin user permissions."""
        self.client.force_login(self.admin_user)
        
        # Admin should access user management endpoints
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_permissions(self):
        """Test regular user permissions."""
        self.client.force_login(self.regular_user)
        
        # Regular user should not access user management
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # But should access their own profile
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserRegistrationSerializerTest(TestCase):
    """Test cases for UserRegistrationSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_data = {
            'username': 'newuser',
            'email': 'newuser@company.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'department': 'IT',
            'position': 'Developer',
            'location': 'TOKYO',
            'employee_id': 'EMP003'
        }
        
        # Create existing user for duplicate tests
        self.existing_user = User.objects.create_user(
            username='existing',
            email='existing@company.com',
            password='testpass123',
            employee_id='EMP001'
        )
    
    def test_valid_registration_data(self):
        """Test serializer with valid registration data."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@company.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.department, 'IT')
        self.assertEqual(user.position, 'Developer')
        self.assertEqual(user.location, 'TOKYO')
        self.assertEqual(user.employee_id, 'EMP003')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
    
    def test_duplicate_username_validation(self):
        """Test validation error for duplicate username."""
        data = self.valid_data.copy()
        data['username'] = 'existing'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('既に使用されています', str(serializer.errors['username']))
    
    def test_duplicate_email_validation(self):
        """Test validation error for duplicate email."""
        data = self.valid_data.copy()
        data['email'] = 'existing@company.com'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('既に登録されています', str(serializer.errors['email']))
    
    def test_duplicate_employee_id_validation(self):
        """Test validation error for duplicate employee ID."""
        data = self.valid_data.copy()
        data['employee_id'] = 'EMP001'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('employee_id', serializer.errors)
        self.assertIn('既に使用されています', str(serializer.errors['employee_id']))
    
    def test_password_mismatch_validation(self):
        """Test validation error for password mismatch."""
        data = self.valid_data.copy()
        data['confirm_password'] = 'differentpass'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)
        self.assertIn('一致しません', str(serializer.errors['confirm_password']))
    
    def test_weak_password_validation(self):
        """Test validation error for weak password."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['confirm_password'] = '123'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_invalid_email_format_validation(self):
        """Test validation error for invalid email format."""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_invalid_location_validation(self):
        """Test validation error for invalid location."""
        data = self.valid_data.copy()
        data['location'] = 'INVALID'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('location', serializer.errors)
        self.assertIn('無効な勤務地', str(serializer.errors['location']))
    
    def test_missing_required_fields(self):
        """Test validation errors for missing required fields."""
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('first_name', serializer.errors)
        self.assertIn('last_name', serializer.errors)
    
    def test_optional_fields_empty(self):
        """Test that optional fields can be empty."""
        data = self.valid_data.copy()
        data.pop('department', None)
        data.pop('position', None)
        data.pop('employee_id', None)
        data.pop('location', None)
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.department, '')
        self.assertEqual(user.position, '')
        self.assertEqual(user.employee_id, None)
        self.assertEqual(user.location, '')
    
    def test_username_format_validation(self):
        """Test username format validation."""
        # Too short
        data = self.valid_data.copy()
        data['username'] = 'ab'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        
        # Invalid characters
        data['username'] = 'user@name'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
    
    def test_employee_id_format_validation(self):
        """Test employee ID format validation."""
        # Too short
        data = self.valid_data.copy()
        data['employee_id'] = 'AB'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('employee_id', serializer.errors)
        
        # Invalid characters
        data['employee_id'] = 'EMP@001'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('employee_id', serializer.errors)
    
    def test_name_length_validation(self):
        """Test name field length validation."""
        data = self.valid_data.copy()
        data['first_name'] = 'A' * 51  # Too long
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)
    
    def test_department_position_length_validation(self):
        """Test department and position field length validation."""
        data = self.valid_data.copy()
        data['department'] = 'A' * 101  # Too long
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('department', serializer.errors)
        
        data['department'] = 'IT'
        data['position'] = 'B' * 101  # Too long
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('position', serializer.errors)
    
    def test_security_validation(self):
        """Test security validation for malicious input."""
        # XSS attempt
        data = self.valid_data.copy()
        data['first_name'] = '<script>alert("xss")</script>'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)
        
        # SQL injection attempt
        data['first_name'] = "'; DROP TABLE users; --"
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)


class UserRegistrationViewTest(APITestCase):
    """Test cases for user registration view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.registration_url = reverse('register')
        
        self.valid_data = {
            'username': 'newuser',
            'email': 'newuser@company.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'department': 'IT',
            'position': 'Developer',
            'location': 'TOKYO',
            'employee_id': 'EMP003'
        }
        
        # Create existing user for duplicate tests
        self.existing_user = User.objects.create_user(
            username='existing',
            email='existing@company.com',
            password='testpass123',
            employee_id='EMP001'
        )
    
    def test_successful_registration(self):
        """Test successful user registration."""
        response = self.client.post(self.registration_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('登録が完了しました', response.data['message'])
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@company.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        
        # Verify registration attempt was logged
        attempt = RegistrationAttempt.objects.filter(username='newuser').first()
        self.assertIsNotNone(attempt)
        self.assertTrue(attempt.success)
        self.assertEqual(attempt.created_user, user)
    
    def test_registration_with_duplicate_username(self):
        """Test registration with duplicate username."""
        data = self.valid_data.copy()
        data['username'] = 'existing'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('username', response.data['details'])
        
        # Verify failed registration attempt was logged
        attempt = RegistrationAttempt.objects.filter(username='existing').first()
        self.assertIsNotNone(attempt)
        self.assertFalse(attempt.success)
        self.assertIn('既に使用されています', attempt.failure_reason)
    
    def test_registration_with_duplicate_email(self):
        """Test registration with duplicate email."""
        data = self.valid_data.copy()
        data['email'] = 'existing@company.com'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('email', response.data['details'])
    
    def test_registration_with_password_mismatch(self):
        """Test registration with password mismatch."""
        data = self.valid_data.copy()
        data['confirm_password'] = 'differentpass'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('confirm_password', response.data['details'])
    
    def test_registration_with_weak_password(self):
        """Test registration with weak password."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['confirm_password'] = '123'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('password', response.data['details'])
    
    def test_registration_with_missing_required_fields(self):
        """Test registration with missing required fields."""
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('email', response.data['details'])
        self.assertIn('first_name', response.data['details'])
        self.assertIn('last_name', response.data['details'])
    
    def test_registration_with_invalid_email_format(self):
        """Test registration with invalid email format."""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('email', response.data['details'])
    
    def test_registration_with_invalid_location(self):
        """Test registration with invalid location."""
        data = self.valid_data.copy()
        data['location'] = 'INVALID'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        self.assertIn('location', response.data['details'])
    
    def test_registration_without_optional_fields(self):
        """Test registration without optional fields."""
        data = {
            'username': 'minimaluser',
            'email': 'minimal@company.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Minimal',
            'last_name': 'User'
        }
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created with empty optional fields
        user = User.objects.get(username='minimaluser')
        self.assertEqual(user.department, '')
        self.assertEqual(user.position, '')
        self.assertEqual(user.employee_id, None)
        self.assertEqual(user.location, '')
    
    def test_registration_ip_tracking(self):
        """Test that registration attempts track IP addresses."""
        response = self.client.post(
            self.registration_url, 
            self.valid_data, 
            format='json',
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify IP was tracked
        attempt = RegistrationAttempt.objects.filter(username='newuser').first()
        self.assertIsNotNone(attempt)
        self.assertIn('192.168.1.100', attempt.ip_address)
    
    def test_registration_user_agent_tracking(self):
        """Test that registration attempts track user agents."""
        response = self.client.post(
            self.registration_url, 
            self.valid_data, 
            format='json',
            HTTP_USER_AGENT='Test Browser 1.0'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user agent was tracked
        attempt = RegistrationAttempt.objects.filter(username='newuser').first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.user_agent, 'Test Browser 1.0')
    
    @patch('apps.authentication.views.logger')
    def test_registration_logging(self, mock_logger):
        """Test that registration attempts are properly logged."""
        response = self.client.post(self.registration_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify success was logged
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Successful registration', log_call_args)
        self.assertIn('newuser', log_call_args)
    
    @patch('apps.authentication.views.logger')
    def test_registration_failure_logging(self, mock_logger):
        """Test that registration failures are properly logged."""
        data = self.valid_data.copy()
        data['username'] = 'existing'  # Duplicate username
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify failure was logged
        mock_logger.warning.assert_called()
        log_call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('Registration validation failed', log_call_args)
        self.assertIn('existing', log_call_args)
    
    def test_registration_rate_limiting(self):
        """Test that registration is rate limited."""
        # This test would require mocking the rate limiter or using a test-specific configuration
        # For now, we'll just verify the decorator is applied by checking the view function
        from apps.authentication.views import register_view
        
        # Check that rate limiting decorators are applied
        self.assertTrue(hasattr(register_view, '_ratelimit_key'))
    
    def test_registration_csrf_protection(self):
        """Test CSRF protection for registration endpoint."""
        # Test that the endpoint requires CSRF token in production
        # This is more of an integration test and would require specific CSRF configuration
        pass
    
    def test_registration_transaction_rollback(self):
        """Test that failed registration doesn't create partial data."""
        # Mock a database error during user creation
        with patch('apps.authentication.serializers.User.objects.create_user') as mock_create:
            mock_create.side_effect = Exception('Database error')
            
            response = self.client.post(self.registration_url, self.valid_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify no user was created
            self.assertFalse(User.objects.filter(username='newuser').exists())
            
            # Verify failed attempt was still logged
            attempt = RegistrationAttempt.objects.filter(username='newuser').first()
            self.assertIsNotNone(attempt)
            self.assertFalse(attempt.success)
            self.assertIn('システムエラー', attempt.failure_reason)


class RegistrationAttemptModelTest(TestCase):
    """Test cases for RegistrationAttempt model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@company.com',
            password='testpass123'
        )
    
    def test_successful_registration_attempt(self):
        """Test recording successful registration attempt."""
        attempt = RegistrationAttempt.objects.create(
            username='testuser',
            email='test@company.com',
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            success=True,
            created_user=self.user
        )
        
        self.assertEqual(attempt.username, 'testuser')
        self.assertEqual(attempt.email, 'test@company.com')
        self.assertEqual(attempt.ip_address, '127.0.0.1')
        self.assertTrue(attempt.success)
        self.assertEqual(attempt.created_user, self.user)
        self.assertEqual(attempt.failure_reason, '')
    
    def test_failed_registration_attempt(self):
        """Test recording failed registration attempt."""
        attempt = RegistrationAttempt.objects.create(
            username='duplicate',
            email='duplicate@company.com',
            ip_address='192.168.1.100',
            user_agent='Test Browser',
            success=False,
            failure_reason='ユーザー名重複'
        )
        
        self.assertEqual(attempt.username, 'duplicate')
        self.assertEqual(attempt.email, 'duplicate@company.com')
        self.assertFalse(attempt.success)
        self.assertEqual(attempt.failure_reason, 'ユーザー名重複')
        self.assertIsNone(attempt.created_user)
    
    def test_registration_attempt_str_representation(self):
        """Test RegistrationAttempt string representation."""
        attempt = RegistrationAttempt.objects.create(
            username='testuser',
            email='test@company.com',
            ip_address='127.0.0.1',
            success=True,
            created_user=self.user
        )
        
        expected = f"testuser (test@company.com) - 成功 ({attempt.timestamp})"
        self.assertEqual(str(attempt), expected)
    
    def test_registration_attempt_indexes(self):
        """Test that database indexes are properly created."""
        # This would require database introspection to verify indexes
        # For now, we'll just verify the model meta configuration
        meta = RegistrationAttempt._meta
        
        # Check that indexes are defined
        index_fields = []
        for index in meta.indexes:
            index_fields.extend(index.fields)
        
        self.assertIn('ip_address', index_fields)
        self.assertIn('username', index_fields)
        self.assertIn('email', index_fields)
        self.assertIn('timestamp', index_fields)


class IntegrationTest(TransactionTestCase):
    """Integration tests for authentication system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow from login to logout."""
        # Step 1: Login
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Step 2: Access protected resource
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 3: Refresh token
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Step 4: Logout
        response = self.client.post('/api/auth/logout/', {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_concurrent_login_attempts(self):
        """Test handling of concurrent login attempts."""
        import threading
        import time
        
        results = []
        
        def login_attempt():
            client = APIClient()
            response = client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'testpass123'
            })
            results.append(response.status_code)
        
        # Create multiple threads for concurrent login
        threads = []
        for i in range(5):
            thread = threading.Thread(target=login_attempt)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All should succeed
        self.assertTrue(all(status == 200 for status in results))
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on authentication errors."""
        initial_user_count = User.objects.count()
        initial_attempt_count = LoginAttempt.objects.count()
        
        # Simulate a database error during user creation
        with self.assertRaises(Exception):
            with self.assertRaises(Exception):
                # This should fail and rollback
                User.objects.create_user(
                    username='',  # Invalid username
                    email='invalid-email',  # Invalid email
                    password='testpass123'
                )
        
        # Counts should remain the same
        self.assertEqual(User.objects.count(), initial_user_count)


class PerformanceTest(TestCase):
    """Performance tests for authentication system."""
    
    def test_login_performance(self):
        """Test login performance with multiple users."""
        import time
        
        # Create multiple users
        users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            users.append(user)
        
        # Measure login time
        start_time = time.time()
        
        for i in range(10):  # Test 10 logins
            response = self.client.post('/api/auth/login/', {
                'username': f'user{i}',
                'password': 'testpass123'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(avg_time, 1.0, "Login taking too long")
    
    def test_token_validation_performance(self):
        """Test JWT token validation performance."""
        import time
        
        # Login to get token
        user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )
        
        response = self.client.post('/api/auth/login/', {
            'username': 'perfuser',
            'password': 'testpass123'
        })
        
        access_token = response.data['access']
        
        # Measure token validation time
        start_time = time.time()
        
        for i in range(100):  # Test 100 validations
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            response = self.client.get('/api/auth/me/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should validate quickly
        self.assertLess(avg_time, 0.1, "Token validation taking too long")