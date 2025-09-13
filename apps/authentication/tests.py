"""
Tests for authentication API endpoints.
"""

import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

from .models import LoginAttempt

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
