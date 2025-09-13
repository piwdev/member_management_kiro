/**
 * E2E tests for authentication flows
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/auth/login/', async route => {
      if (route.request().method() === 'POST') {
        const postData = route.request().postData();
        if (postData?.includes('testuser') && postData?.includes('password123')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              access: 'mock-access-token',
              refresh: 'mock-refresh-token',
              user: {
                id: '1',
                username: 'testuser',
                email: 'test@example.com',
                employee_id: 'EMP001',
                department: 'IT',
                position: 'Developer',
                full_name: 'Test User',
                is_staff: false
              }
            })
          });
        } else {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid credentials'
            })
          });
        }
      }
    });

    // Mock dashboard API
    await page.route('**/api/dashboard/my-resources/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_assignments: [],
          license_assignments: []
        })
      });
    });

    await page.route('**/api/dashboard/notifications/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: []
        })
      });
    });
  });

  test('successful login flow', async ({ page }) => {
    await page.goto('/login');

    // Check login form is visible
    await expect(page.getByLabel('ユーザー名')).toBeVisible();
    await expect(page.getByLabel('パスワード')).toBeVisible();

    // Fill login form
    await page.getByLabel('ユーザー名').fill('testuser');
    await page.getByLabel('パスワード').fill('password123');

    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('ダッシュボード')).toBeVisible();
  });

  test('failed login flow', async ({ page }) => {
    await page.goto('/login');

    // Fill login form with wrong credentials
    await page.getByLabel('ユーザー名').fill('testuser');
    await page.getByLabel('パスワード').fill('wrongpassword');

    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();

    // Should show error message
    await expect(page.getByText('ログインに失敗しました')).toBeVisible();

    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('form validation', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    await page.getByRole('button', { name: 'ログイン' }).click();

    // Should show validation errors
    await expect(page.getByText('ユーザー名は必須です')).toBeVisible();
    await expect(page.getByText('パスワードは必須です')).toBeVisible();
  });

  test('remember me functionality', async ({ page }) => {
    await page.goto('/login');

    // Fill form and check remember me
    await page.getByLabel('ユーザー名').fill('testuser');
    await page.getByLabel('パスワード').fill('password123');
    await page.getByLabel('ログイン情報を記憶').check();

    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();

    // Check localStorage
    const rememberedUsername = await page.evaluate(() => 
      localStorage.getItem('rememberedUsername')
    );
    expect(rememberedUsername).toBe('testuser');
  });

  test('logout functionality', async ({ page }) => {
    // Mock logout API
    await page.route('**/api/auth/logout/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Logged out successfully' })
      });
    });

    // Login first
    await page.goto('/login');
    await page.getByLabel('ユーザー名').fill('testuser');
    await page.getByLabel('パスワード').fill('password123');
    await page.getByRole('button', { name: 'ログイン' }).click();

    await expect(page).toHaveURL('/dashboard');

    // Click logout
    await page.getByRole('button', { name: 'ログアウト' }).click();

    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test('protected route access', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/employees');

    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test('keyboard navigation', async ({ page }) => {
    await page.goto('/login');

    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('ユーザー名')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel('パスワード')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'ログイン' })).toBeFocused();
  });

  test('loading state during login', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/auth/login/', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'mock-token',
          refresh: 'mock-refresh',
          user: { id: '1', username: 'testuser' }
        })
      });
    });

    await page.goto('/login');

    await page.getByLabel('ユーザー名').fill('testuser');
    await page.getByLabel('パスワード').fill('password123');
    await page.getByRole('button', { name: 'ログイン' }).click();

    // Should show loading state
    await expect(page.getByText('ログイン中')).toBeVisible();
    await expect(page.getByRole('button', { name: 'ログイン' })).toBeDisabled();
  });
});