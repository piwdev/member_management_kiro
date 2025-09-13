/**
 * E2E tests for employee management
 */

import { test, expect } from '@playwright/test';

test.describe('Employee Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-admin-token');
      localStorage.setItem('auth_user', JSON.stringify({
        id: '1',
        username: 'admin',
        is_staff: true,
        is_superuser: true
      }));
    });

    // Mock employees API
    await page.route('**/api/employees/employees/', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                id: '1',
                employee_id: 'EMP001',
                name: '田中太郎',
                email: 'tanaka@example.com',
                department: '開発部',
                position: 'エンジニア',
                location: 'TOKYO',
                status: 'ACTIVE',
                is_active: true,
                hire_date: '2022-04-01'
              },
              {
                id: '2',
                employee_id: 'EMP002',
                name: '佐藤花子',
                email: 'sato@example.com',
                department: '営業部',
                position: 'マネージャー',
                location: 'OKINAWA',
                status: 'ACTIVE',
                is_active: true,
                hire_date: '2021-10-01'
              }
            ],
            count: 2,
            next: null,
            previous: null
          })
        });
      } else if (route.request().method() === 'POST') {
        const postData = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '3',
            employee_id: postData.employee_id,
            name: postData.name,
            email: postData.email,
            department: postData.department,
            position: postData.position,
            location: postData.location,
            status: 'ACTIVE',
            is_active: true,
            hire_date: postData.hire_date
          })
        });
      }
    });

    // Mock employee detail API
    await page.route('**/api/employees/employees/1/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1',
          employee_id: 'EMP001',
          name: '田中太郎',
          name_kana: 'タナカタロウ',
          email: 'tanaka@example.com',
          department: '開発部',
          position: 'エンジニア',
          location: 'TOKYO',
          status: 'ACTIVE',
          is_active: true,
          hire_date: '2022-04-01',
          phone_number: '090-1234-5678',
          history_records: []
        })
      });
    });
  });

  test('displays employee list', async ({ page }) => {
    await page.goto('/employees');

    // Check page title
    await expect(page.getByText('社員管理')).toBeVisible();

    // Check employee data is displayed
    await expect(page.getByText('田中太郎')).toBeVisible();
    await expect(page.getByText('佐藤花子')).toBeVisible();
    await expect(page.getByText('EMP001')).toBeVisible();
    await expect(page.getByText('開発部')).toBeVisible();
    await expect(page.getByText('営業部')).toBeVisible();

    // Check add button is present
    await expect(page.getByRole('button', { name: '新しい社員を追加' })).toBeVisible();
  });

  test('creates new employee', async ({ page }) => {
    await page.goto('/employees');

    // Click add employee button
    await page.getByRole('button', { name: '新しい社員を追加' }).click();

    // Check modal is open
    await expect(page.getByText('社員を追加')).toBeVisible();

    // Fill form
    await page.getByLabel('社員ID').fill('EMP003');
    await page.getByLabel('氏名').fill('山田次郎');
    await page.getByLabel('氏名（カナ）').fill('ヤマダジロウ');
    await page.getByLabel('メールアドレス').fill('yamada@example.com');
    await page.getByLabel('部署').selectOption('マーケティング部');
    await page.getByLabel('役職').selectOption('マネージャー');
    await page.getByLabel('勤務地').selectOption('REMOTE');
    await page.getByLabel('入社日').fill('2023-11-01');
    await page.getByLabel('電話番号').fill('090-9999-8888');

    // Submit form
    await page.getByRole('button', { name: '追加' }).click();

    // Check success message or modal close
    await expect(page.getByText('社員を追加')).not.toBeVisible();
  });

  test('validates employee form', async ({ page }) => {
    await page.goto('/employees');

    // Click add employee button
    await page.getByRole('button', { name: '新しい社員を追加' }).click();

    // Try to submit empty form
    await page.getByRole('button', { name: '追加' }).click();

    // Check validation errors
    await expect(page.getByText('社員IDは必須です')).toBeVisible();
    await expect(page.getByText('氏名は必須です')).toBeVisible();
    await expect(page.getByText('メールアドレスは必須です')).toBeVisible();
  });

  test('searches employees', async ({ page }) => {
    // Mock search API
    await page.route('**/api/employees/employees/?search=田中', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: '1',
              employee_id: 'EMP001',
              name: '田中太郎',
              email: 'tanaka@example.com',
              department: '開発部',
              position: 'エンジニア',
              location: 'TOKYO',
              status: 'ACTIVE',
              is_active: true
            }
          ],
          count: 1,
          next: null,
          previous: null
        })
      });
    });

    await page.goto('/employees');

    // Type in search box
    await page.getByPlaceholder('社員を検索').fill('田中');

    // Check filtered results
    await expect(page.getByText('田中太郎')).toBeVisible();
    await expect(page.getByText('佐藤花子')).not.toBeVisible();
  });

  test('filters employees by department', async ({ page }) => {
    // Mock filter API
    await page.route('**/api/employees/employees/?department=開発部', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: '1',
              employee_id: 'EMP001',
              name: '田中太郎',
              email: 'tanaka@example.com',
              department: '開発部',
              position: 'エンジニア',
              location: 'TOKYO',
              status: 'ACTIVE',
              is_active: true
            }
          ],
          count: 1,
          next: null,
          previous: null
        })
      });
    });

    await page.goto('/employees');

    // Select department filter
    await page.getByLabel('部署でフィルター').selectOption('開発部');

    // Check filtered results
    await expect(page.getByText('田中太郎')).toBeVisible();
    await expect(page.getByText('佐藤花子')).not.toBeVisible();
  });

  test('sorts employees by column', async ({ page }) => {
    await page.goto('/employees');

    // Click on name column header
    await page.getByText('氏名').click();

    // Check that API was called with ordering parameter
    await page.waitForRequest(req => 
      req.url().includes('ordering=name')
    );
  });

  test('navigates to employee detail', async ({ page }) => {
    await page.goto('/employees');

    // Click on employee row
    await page.getByText('田中太郎').click();

    // Check navigation to detail page
    await expect(page).toHaveURL('/employees/1');
    await expect(page.getByText('社員詳細')).toBeVisible();
    await expect(page.getByText('EMP001')).toBeVisible();
  });

  test('handles pagination', async ({ page }) => {
    // Mock paginated response
    await page.route('**/api/employees/employees/', async route => {
      const url = new URL(route.request().url());
      const page_param = url.searchParams.get('page');
      
      if (page_param === '2') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                id: '3',
                employee_id: 'EMP003',
                name: '山田次郎',
                email: 'yamada@example.com',
                department: 'HR',
                position: 'Manager',
                location: 'TOKYO',
                status: 'ACTIVE',
                is_active: true
              }
            ],
            count: 25,
            next: null,
            previous: 'http://api/employees/?page=1'
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                id: '1',
                employee_id: 'EMP001',
                name: '田中太郎',
                email: 'tanaka@example.com',
                department: '開発部',
                position: 'エンジニア',
                location: 'TOKYO',
                status: 'ACTIVE',
                is_active: true
              },
              {
                id: '2',
                employee_id: 'EMP002',
                name: '佐藤花子',
                email: 'sato@example.com',
                department: '営業部',
                position: 'マネージャー',
                location: 'OKINAWA',
                status: 'ACTIVE',
                is_active: true
              }
            ],
            count: 25,
            next: 'http://api/employees/?page=2',
            previous: null
          })
        });
      }
    });

    await page.goto('/employees');

    // Check pagination info
    await expect(page.getByText('25件中 1-2件を表示')).toBeVisible();

    // Click next page
    await page.getByRole('button', { name: '次のページ' }).click();

    // Check page 2 content
    await expect(page.getByText('山田次郎')).toBeVisible();
  });

  test('handles loading state', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/employees/employees/', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [],
          count: 0,
          next: null,
          previous: null
        })
      });
    });

    await page.goto('/employees');

    // Check loading state
    await expect(page.getByText('読み込み中')).toBeVisible();
  });

  test('handles error state', async ({ page }) => {
    // Mock API error
    await page.route('**/api/employees/employees/', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal server error'
        })
      });
    });

    await page.goto('/employees');

    // Check error state
    await expect(page.getByText('エラーが発生しました')).toBeVisible();
  });

  test('keyboard navigation', async ({ page }) => {
    await page.goto('/employees');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await expect(page.getByPlaceholder('社員を検索')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel('部署でフィルター')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: '新しい社員を追加' })).toBeFocused();
  });

  test('responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/employees');

    // Check mobile-specific elements
    await expect(page.getByRole('button', { name: 'メニュー' })).toBeVisible();
    
    // Check that table is responsive
    await expect(page.getByText('田中太郎')).toBeVisible();
  });
});