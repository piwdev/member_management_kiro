/**
 * E2E tests for user registration flow
 */

import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to registration page
    await page.goto('/register');
  });

  test('should complete full registration flow successfully', async ({ page }) => {
    // Fill out the registration form
    await page.fill('[name="username"]', 'testuser123');
    await page.fill('[name="email"]', 'testuser123@example.com');
    await page.fill('[name="password"]', 'testpassword123');
    await page.fill('[name="confirmPassword"]', 'testpassword123');
    await page.fill('[name="firstName"]', 'Test');
    await page.fill('[name="lastName"]', 'User');
    await page.fill('[name="department"]', 'IT');
    await page.fill('[name="position"]', 'Developer');
    await page.selectOption('[name="location"]', 'TOKYO');
    await page.fill('[name="employeeId"]', 'EMP123');

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for success message or redirect
    await expect(page).toHaveURL('/login', { timeout: 10000 });
    
    // Check for success message (if using toast notifications)
    // await expect(page.locator('.toast-success')).toBeVisible();
  });

  test('should show validation errors for empty required fields', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Check for validation errors
    await expect(page.locator('text=ユーザー名は必須です')).toBeVisible();
    await expect(page.locator('text=メールアドレスは必須です')).toBeVisible();
    await expect(page.locator('text=パスワードは必須です')).toBeVisible();
    await expect(page.locator('text=名は必須です')).toBeVisible();
    await expect(page.locator('text=姓は必須です')).toBeVisible();
  });

  test('should show password mismatch error', async ({ page }) => {
    await page.fill('[name="password"]', 'password123');
    await page.fill('[name="confirmPassword"]', 'differentpassword');
    
    // Trigger validation by blurring the confirm password field
    await page.blur('[name="confirmPassword"]');

    await expect(page.locator('text=パスワードが一致しません')).toBeVisible();
  });

  test('should show server validation errors for duplicate username', async ({ page }) => {
    // Fill form with existing username (assuming there's test data)
    await page.fill('[name="username"]', 'admin'); // Assuming admin user exists
    await page.fill('[name="email"]', 'newemail@example.com');
    await page.fill('[name="password"]', 'testpassword123');
    await page.fill('[name="confirmPassword"]', 'testpassword123');
    await page.fill('[name="firstName"]', 'Test');
    await page.fill('[name="lastName"]', 'User');

    await page.click('button[type="submit"]');

    // Check for server error
    await expect(page.locator('text=このユーザー名は既に使用されています')).toBeVisible();
  });

  test('should navigate to login page from registration page', async ({ page }) => {
    // Click the login link
    await page.click('text=ログインはこちら');

    // Should navigate to login page
    await expect(page).toHaveURL('/login');
  });

  test('should redirect authenticated users away from registration page', async ({ page }) => {
    // First login as an existing user
    await page.goto('/login');
    await page.fill('[name="username"]', 'admin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await expect(page).toHaveURL('/');

    // Try to navigate to registration page
    await page.goto('/register');

    // Should be redirected away from registration page
    await expect(page).toHaveURL('/');
  });

  test('should handle form field validation on blur', async ({ page }) => {
    // Focus and blur username field without entering anything
    await page.focus('[name="username"]');
    await page.blur('[name="username"]');

    await expect(page.locator('text=ユーザー名は必須です')).toBeVisible();

    // Enter username and blur - error should disappear
    await page.fill('[name="username"]', 'testuser');
    await page.blur('[name="username"]');

    await expect(page.locator('text=ユーザー名は必須です')).not.toBeVisible();
  });

  test('should enforce maxLength on input fields', async ({ page }) => {
    // Test department field max length (100 characters)
    const longDepartment = 'A'.repeat(150);
    await page.fill('[name="department"]', longDepartment);
    
    const departmentValue = await page.inputValue('[name="department"]');
    expect(departmentValue.length).toBeLessThanOrEqual(100);

    // Test employee ID field max length (20 characters)
    const longEmployeeId = '1'.repeat(30);
    await page.fill('[name="employeeId"]', longEmployeeId);
    
    const employeeIdValue = await page.inputValue('[name="employeeId"]');
    expect(employeeIdValue.length).toBeLessThanOrEqual(20);
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through form fields
    await page.keyboard.press('Tab');
    await expect(page.locator('[name="username"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('[name="email"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('[name="password"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('[name="confirmPassword"]')).toBeFocused();
  });

  test('should show loading state during form submission', async ({ page }) => {
    // Fill form with valid data
    await page.fill('[name="username"]', 'testuser456');
    await page.fill('[name="email"]', 'testuser456@example.com');
    await page.fill('[name="password"]', 'testpassword123');
    await page.fill('[name="confirmPassword"]', 'testpassword123');
    await page.fill('[name="firstName"]', 'Test');
    await page.fill('[name="lastName"]', 'User');

    // Submit form
    await page.click('button[type="submit"]');

    // Check for loading state (button should be disabled)
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Check for loading spinner
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
  });
});

test.describe('Registration and Login Integration', () => {
  test('should allow login after successful registration', async ({ page }) => {
    const username = `testuser${Date.now()}`;
    const email = `${username}@example.com`;
    const password = 'testpassword123';

    // Register new user
    await page.goto('/register');
    await page.fill('[name="username"]', username);
    await page.fill('[name="email"]', email);
    await page.fill('[name="password"]', password);
    await page.fill('[name="confirmPassword"]', password);
    await page.fill('[name="firstName"]', 'Test');
    await page.fill('[name="lastName"]', 'User');

    await page.click('button[type="submit"]');

    // Wait for redirect to login page
    await expect(page).toHaveURL('/login', { timeout: 10000 });

    // Now try to login with the newly registered user
    await page.fill('[name="username"]', username);
    await page.fill('[name="password"]', password);
    await page.click('button[type="submit"]');

    // Should successfully login and redirect to dashboard
    await expect(page).toHaveURL('/', { timeout: 10000 });
    
    // Check for user info or dashboard elements
    await expect(page.locator(`text=${username}`)).toBeVisible();
  });
});