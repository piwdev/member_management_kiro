/**
 * Integration tests for the frontend application
 * Tests complete user workflows and component interactions
 */

import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import { render, mockApiResponses, mockAdminUser, mockUser } from '../test-utils';
import App from '../App';

// Mock the API
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock router
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('Frontend Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  describe('Authentication Flow', () => {
    it('completes login to dashboard workflow', async () => {
      const user = userEvent.setup();
      
      // Mock login API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access: 'mock-token',
          refresh: 'mock-refresh-token',
          user: mockUser
        })
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: null,
          token: null,
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: false
        },
        initialEntries: ['/login']
      });

      // Should show login form
      expect(screen.getByLabelText(/ユーザー名/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/パスワード/i)).toBeInTheDocument();

      // Fill and submit login form
      await user.type(screen.getByLabelText(/ユーザー名/i), 'testuser');
      await user.type(screen.getByLabelText(/パスワード/i), 'password123');
      await user.click(screen.getByRole('button', { name: /ログイン/i }));

      // Mock dashboard data
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            device_assignments: [],
            license_assignments: []
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        });

      // Should navigate to dashboard after successful login
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('handles login failure correctly', async () => {
      const user = userEvent.setup();
      
      // Mock failed login
      mockFetch.mockRejectedValueOnce({
        response: {
          status: 401,
          data: { error: 'Invalid credentials' }
        }
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: null,
          token: null,
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: false
        },
        initialEntries: ['/login']
      });

      // Fill and submit login form with wrong credentials
      await user.type(screen.getByLabelText(/ユーザー名/i), 'testuser');
      await user.type(screen.getByLabelText(/パスワード/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /ログイン/i }));

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/ログインに失敗しました/i)).toBeInTheDocument();
      });

      // Should remain on login page
      expect(screen.getByLabelText(/ユーザー名/i)).toBeInTheDocument();
    });
  });

  describe('Employee Management Workflow', () => {
    it('completes employee creation workflow', async () => {
      const user = userEvent.setup();
      
      // Mock employees list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/employees']
      });

      await waitFor(() => {
        expect(screen.getByText('田中太郎')).toBeInTheDocument();
      });

      // Click add employee button
      const addButton = screen.getByRole('button', { name: /新しい社員を追加/i });
      await user.click(addButton);

      // Fill employee form
      await user.type(screen.getByLabelText(/社員ID/i), 'EMP003');
      await user.type(screen.getByLabelText(/氏名/i), '新入社員');
      await user.type(screen.getByLabelText(/メールアドレス/i), 'newbie@example.com');
      await user.selectOptions(screen.getByLabelText(/部署/i), '開発部');
      await user.selectOptions(screen.getByLabelText(/役職/i), 'エンジニア');
      await user.selectOptions(screen.getByLabelText(/勤務地/i), 'TOKYO');
      await user.type(screen.getByLabelText(/入社日/i), '2023-11-01');

      // Mock successful creation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '3',
          employee_id: 'EMP003',
          name: '新入社員',
          email: 'newbie@example.com',
          department: '開発部',
          position: 'エンジニア',
          location: 'TOKYO',
          status: 'ACTIVE'
        })
      });

      // Submit form
      const submitButton = screen.getByRole('button', { name: /追加/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/employees/employees/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('新入社員')
          })
        );
      });
    });

    it('completes employee detail view workflow', async () => {
      const user = userEvent.setup();
      
      // Mock employees list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/employees']
      });

      await waitFor(() => {
        expect(screen.getByText('田中太郎')).toBeInTheDocument();
      });

      // Click on employee row
      const employeeRow = screen.getByText('田中太郎').closest('tr');
      await user.click(employeeRow!);

      // Should navigate to employee detail
      expect(mockNavigate).toHaveBeenCalledWith('/employees/1');
    });
  });

  describe('Device Management Workflow', () => {
    it('completes device assignment workflow', async () => {
      const user = userEvent.setup();
      
      // Mock devices list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.devices)
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/devices']
      });

      await waitFor(() => {
        expect(screen.getByText('Dell Latitude 5520')).toBeInTheDocument();
      });

      // Find available device and click assign
      const deviceRow = screen.getByText('DL001').closest('tr');
      const assignButton = within(deviceRow!).getByRole('button', { name: /割当/i });
      
      // Mock employees for assignment dialog
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      });

      await user.click(assignButton);

      await waitFor(() => {
        expect(screen.getByText(/端末を割り当て/i)).toBeInTheDocument();
      });

      // Fill assignment form
      await user.selectOptions(screen.getByLabelText(/社員を選択/i), '1');
      await user.type(screen.getByLabelText(/使用目的/i), '開発業務用');

      // Mock successful assignment
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          device: '1',
          employee: '1',
          purpose: '開発業務用',
          status: 'ACTIVE'
        })
      });

      const confirmButton = screen.getByRole('button', { name: /割り当て/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/assign/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('開発業務用')
          })
        );
      });
    });
  });

  describe('License Management Workflow', () => {
    it('completes license assignment workflow', async () => {
      const user = userEvent.setup();
      
      // Mock licenses list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.licenses)
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/licenses']
      });

      await waitFor(() => {
        expect(screen.getByText('Microsoft Office 365')).toBeInTheDocument();
      });

      // Find license and click assign
      const licenseRow = screen.getByText('Microsoft Office 365').closest('tr');
      const assignButton = within(licenseRow!).getByRole('button', { name: /割当/i });
      
      // Mock employees for assignment dialog
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      });

      await user.click(assignButton);

      await waitFor(() => {
        expect(screen.getByText(/ライセンスを割り当て/i)).toBeInTheDocument();
      });

      // Fill assignment form
      await user.selectOptions(screen.getByLabelText(/社員を選択/i), '1');
      await user.type(screen.getByLabelText(/利用目的/i), 'オフィス業務用');

      // Mock successful assignment
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          license: '1',
          employee: '1',
          purpose: 'オフィス業務用',
          status: 'ACTIVE'
        })
      });

      const confirmButton = screen.getByRole('button', { name: /割り当て/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/assign/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('オフィス業務用')
          })
        );
      });
    });
  });

  describe('Reports Workflow', () => {
    it('completes report generation and download workflow', async () => {
      const user = userEvent.setup();
      
      // Mock reports list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/reports']
      });

      await waitFor(() => {
        expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
      });

      // Click generate report
      const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
      await user.click(generateButton);

      // Fill report form
      await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'USAGE');
      await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
      await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');
      await user.selectOptions(screen.getByLabelText(/出力形式/i), 'JSON');

      // Mock successful report generation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.reports.usage)
      });

      const submitButton = screen.getByRole('button', { name: /生成/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/reports/generate/usage/'),
          expect.objectContaining({
            method: 'POST'
          })
        );
      });

      // Should show report results
      await waitFor(() => {
        expect(screen.getByText(/総端末数: 10/i)).toBeInTheDocument();
      });
    });
  });

  describe('Employee Dashboard Workflow', () => {
    it('completes resource request workflow', async () => {
      const user = userEvent.setup();
      
      // Mock dashboard data
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            device_assignments: [],
            license_assignments: []
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/dashboard']
      });

      await waitFor(() => {
        expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      });

      // Click request resource
      const requestButton = screen.getByRole('button', { name: /新しいリソースを申請/i });
      await user.click(requestButton);

      // Fill request form
      await user.selectOptions(screen.getByLabelText(/リソース種別/i), 'DEVICE');
      await user.selectOptions(screen.getByLabelText(/端末種別/i), 'LAPTOP');
      await user.type(screen.getByLabelText(/申請理由/i), '新しいプロジェクト用');

      // Mock successful request
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          resource_type: 'DEVICE',
          resource_specification: 'LAPTOP',
          reason: '新しいプロジェクト用',
          status: 'PENDING'
        })
      });

      const submitButton = screen.getByRole('button', { name: /申請する/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/dashboard/resource-requests/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('新しいプロジェクト用')
          })
        );
      });
    });
  });

  describe('Navigation and Routing', () => {
    it('navigates between different sections correctly', async () => {
      const user = userEvent.setup();
      
      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/dashboard']
      });

      // Mock dashboard data
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            device_assignments: [],
            license_assignments: []
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        });

      await waitFor(() => {
        expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      });

      // Navigate to employees
      const employeesLink = screen.getByRole('link', { name: /社員管理/i });
      await user.click(employeesLink);

      expect(mockNavigate).toHaveBeenCalledWith('/employees');

      // Navigate to devices
      const devicesLink = screen.getByRole('link', { name: /端末管理/i });
      await user.click(devicesLink);

      expect(mockNavigate).toHaveBeenCalledWith('/devices');

      // Navigate to licenses
      const licensesLink = screen.getByRole('link', { name: /ライセンス管理/i });
      await user.click(licensesLink);

      expect(mockNavigate).toHaveBeenCalledWith('/licenses');

      // Navigate to reports
      const reportsLink = screen.getByRole('link', { name: /レポート/i });
      await user.click(reportsLink);

      expect(mockNavigate).toHaveBeenCalledWith('/reports');
    });
  });

  describe('Language Switching', () => {
    it('switches language correctly', async () => {
      const user = userEvent.setup();
      
      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/dashboard']
      });

      // Mock dashboard data
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            device_assignments: [],
            license_assignments: []
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        });

      await waitFor(() => {
        expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      });

      // Find language switch button
      const languageSwitch = screen.getByRole('button', { name: /English/i });
      await user.click(languageSwitch);

      // Should switch to English
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      // Switch back to Japanese
      const japaneseSwitch = screen.getByRole('button', { name: /日本語/i });
      await user.click(japaneseSwitch);

      await waitFor(() => {
        expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      // Mock API error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<App />, {
        queryClient,
        authValue: {
          user: mockAdminUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/employees']
      });

      await waitFor(() => {
        expect(screen.getByText(/エラーが発生しました/i)).toBeInTheDocument();
      });
    });

    it('handles unauthorized access correctly', async () => {
      // Mock 401 response
      mockFetch.mockRejectedValueOnce({
        response: { status: 401 }
      });

      render(<App />, {
        queryClient,
        authValue: {
          user: null,
          token: null,
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: false
        },
        initialEntries: ['/employees']
      });

      // Should redirect to login
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });
  });

  describe('Responsive Design', () => {
    it('adapts to mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      // Mock dashboard data
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            device_assignments: [],
            license_assignments: []
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        });

      render(<App />, {
        queryClient,
        authValue: {
          user: mockUser,
          token: 'mock-token',
          login: jest.fn(),
          logout: jest.fn(),
          isLoading: false,
          isAuthenticated: true
        },
        initialEntries: ['/dashboard']
      });

      await waitFor(() => {
        expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      });

      // Should show mobile navigation
      expect(screen.getByRole('button', { name: /メニュー/i })).toBeInTheDocument();
    });
  });
});