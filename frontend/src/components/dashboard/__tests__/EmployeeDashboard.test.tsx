/**
 * Tests for EmployeeDashboard component
 */

import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import { render, mockUser } from '../../../test-utils';
import EmployeeDashboard from '../EmployeeDashboard';

// Mock the API
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockMyResources = {
  device_assignments: [
    {
      id: '1',
      device: {
        id: '1',
        type: 'LAPTOP',
        manufacturer: 'Dell',
        model: 'Latitude 5520',
        serial_number: 'DL001'
      },
      assigned_date: '2023-05-01',
      expected_return_date: '2024-05-01',
      purpose: '開発業務用',
      status: 'ACTIVE'
    }
  ],
  license_assignments: [
    {
      id: '1',
      license: {
        id: '1',
        software_name: 'Microsoft Office 365',
        license_type: 'Business Premium',
        expiry_date: '2024-12-31'
      },
      start_date: '2023-06-01',
      purpose: 'オフィス業務用',
      status: 'ACTIVE'
    }
  ]
};

const mockNotifications = [
  {
    id: '1',
    title: 'ライセンス期限切れ警告',
    message: 'Microsoft Office 365のライセンスが30日以内に期限切れになります。',
    notification_type: 'LICENSE_EXPIRY',
    priority: 'HIGH',
    is_read: false,
    created_at: '2023-11-01T10:00:00Z'
  },
  {
    id: '2',
    title: 'システムメンテナンス通知',
    message: '来週末にシステムメンテナンスを実施します。',
    notification_type: 'SYSTEM',
    priority: 'LOW',
    is_read: true,
    created_at: '2023-10-28T15:30:00Z'
  }
];

describe('EmployeeDashboard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  it('renders employee dashboard correctly', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
      expect(screen.getByText(/割り当てられたリソース/i)).toBeInTheDocument();
      expect(screen.getByText(/通知/i)).toBeInTheDocument();
    });

    // Check device assignment
    expect(screen.getByText('Dell Latitude 5520')).toBeInTheDocument();
    expect(screen.getByText('DL001')).toBeInTheDocument();

    // Check license assignment
    expect(screen.getByText('Microsoft Office 365')).toBeInTheDocument();
    expect(screen.getByText('Business Premium')).toBeInTheDocument();

    // Check notifications
    expect(screen.getByText('ライセンス期限切れ警告')).toBeInTheDocument();
    expect(screen.getByText('システムメンテナンス通知')).toBeInTheDocument();
  });

  it('shows empty state when no resources assigned', async () => {
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

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/割り当てられたリソースがありません/i)).toBeInTheDocument();
    });
  });

  it('opens resource request modal', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
    });

    const requestButton = screen.getByRole('button', { name: /新しいリソースを申請/i });
    await user.click(requestButton);

    expect(screen.getByText(/リソース申請/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/リソース種別/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/申請理由/i)).toBeInTheDocument();
  });

  it('submits resource request', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          resource_type: 'DEVICE',
          resource_specification: 'LAPTOP',
          reason: '新しいプロジェクト用',
          status: 'PENDING'
        })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
    });

    const requestButton = screen.getByRole('button', { name: /新しいリソースを申請/i });
    await user.click(requestButton);

    // Fill request form
    await user.selectOptions(screen.getByLabelText(/リソース種別/i), 'DEVICE');
    await user.selectOptions(screen.getByLabelText(/端末種別/i), 'LAPTOP');
    await user.type(screen.getByLabelText(/申請理由/i), '新しいプロジェクト用');

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

  it('opens return request modal', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dell Latitude 5520')).toBeInTheDocument();
    });

    const deviceCard = screen.getByText('Dell Latitude 5520').closest('.device-card');
    const returnButton = within(deviceCard!).getByRole('button', { name: /返却申請/i });
    await user.click(returnButton);

    expect(screen.getByText(/返却申請/i)).toBeInTheDocument();
    expect(screen.getByText(/Dell Latitude 5520/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/返却予定日/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/返却理由/i)).toBeInTheDocument();
  });

  it('submits return request', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          assignment_id: '1',
          return_date: '2023-12-01',
          reason: 'プロジェクト終了',
          status: 'PENDING'
        })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dell Latitude 5520')).toBeInTheDocument();
    });

    const deviceCard = screen.getByText('Dell Latitude 5520').closest('.device-card');
    const returnButton = within(deviceCard!).getByRole('button', { name: /返却申請/i });
    await user.click(returnButton);

    // Fill return form
    await user.type(screen.getByLabelText(/返却予定日/i), '2023-12-01');
    await user.type(screen.getByLabelText(/返却理由/i), 'プロジェクト終了');

    const submitButton = screen.getByRole('button', { name: /申請する/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/dashboard/return-requests/'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('プロジェクト終了')
        })
      );
    });
  });

  it('marks notification as read', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ...mockNotifications[0], is_read: true })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('ライセンス期限切れ警告')).toBeInTheDocument();
    });

    const unreadNotification = screen.getByText('ライセンス期限切れ警告').closest('.notification');
    const markReadButton = within(unreadNotification!).getByRole('button', { name: /既読にする/i });
    await user.click(markReadButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/dashboard/notifications/1/mark_read/'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  it('shows license expiry warnings', async () => {
    const expiringLicenseResources = {
      ...mockMyResources,
      license_assignments: [
        {
          ...mockMyResources.license_assignments[0],
          license: {
            ...mockMyResources.license_assignments[0].license,
            expiry_date: '2023-12-15' // Expires soon
          }
        }
      ]
    };

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(expiringLicenseResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Microsoft Office 365')).toBeInTheDocument();
    });

    // Should show expiry warning
    expect(screen.getByText(/期限切れ間近/i)).toBeInTheDocument();
    expect(screen.getByText(/2023-12-15/i)).toBeInTheDocument();
  });

  it('filters notifications by type', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('ライセンス期限切れ警告')).toBeInTheDocument();
      expect(screen.getByText('システムメンテナンス通知')).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText(/通知タイプでフィルター/i);
    await user.selectOptions(filterSelect, 'LICENSE_EXPIRY');

    // Should show only license expiry notifications
    expect(screen.getByText('ライセンス期限切れ警告')).toBeInTheDocument();
    expect(screen.queryByText('システムメンテナンス通知')).not.toBeInTheDocument();
  });

  it('shows resource usage statistics', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
    });

    // Check resource statistics
    expect(screen.getByText(/割り当て端末: 1/i)).toBeInTheDocument();
    expect(screen.getByText(/割り当てライセンス: 1/i)).toBeInTheDocument();
  });

  it('handles loading states correctly', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    expect(screen.getByText(/読み込み中/i)).toBeInTheDocument();
  });

  it('handles error states correctly', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'));

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/エラーが発生しました/i)).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh button is clicked', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    render(<EmployeeDashboard />, {
      queryClient,
      authValue: {
        user: mockUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/ダッシュボード/i)).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button', { name: /更新/i });
    
    // Mock fresh data
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMyResources)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: mockNotifications })
      });

    await user.click(refreshButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(4); // Initial 2 + refresh 2
    });
  });
});