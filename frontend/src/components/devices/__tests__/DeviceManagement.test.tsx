/**
 * Tests for DeviceManagement component
 */

import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import { render, mockApiResponses, mockAdminUser } from '../../../test-utils';
import DeviceManagement from '../DeviceManagement';

// Mock the API
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('DeviceManagement', () => {
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

  it('renders device management interface correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dell Latitude 5520')).toBeInTheDocument();
      expect(screen.getByText('HP EliteDesk 800')).toBeInTheDocument();
    });

    expect(screen.getByText('DL001')).toBeInTheDocument();
    expect(screen.getByText('HP001')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /新しい端末を追加/i })).toBeInTheDocument();
  });

  it('opens device creation modal', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const addButton = screen.getByRole('button', { name: /新しい端末を追加/i });
    await user.click(addButton);

    expect(screen.getByText(/端末を追加/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/端末種別/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/メーカー/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/モデル/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/シリアル番号/i)).toBeInTheDocument();
  });

  it('creates new device successfully', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.devices)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '3',
          type: 'TABLET',
          manufacturer: 'Apple',
          model: 'iPad Pro',
          serial_number: 'IPAD001',
          status: 'AVAILABLE',
          purchase_date: '2023-06-01',
          warranty_expiry: '2025-06-01'
        })
      });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const addButton = screen.getByRole('button', { name: /新しい端末を追加/i });
    await user.click(addButton);

    // Fill form
    await user.selectOptions(screen.getByLabelText(/端末種別/i), 'TABLET');
    await user.type(screen.getByLabelText(/メーカー/i), 'Apple');
    await user.type(screen.getByLabelText(/モデル/i), 'iPad Pro');
    await user.type(screen.getByLabelText(/シリアル番号/i), 'IPAD001');
    await user.type(screen.getByLabelText(/購入日/i), '2023-06-01');
    await user.type(screen.getByLabelText(/保証期限/i), '2025-06-01');

    const submitButton = screen.getByRole('button', { name: /追加/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/devices/'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('TABLET')
        })
      );
    });
  });

  it('shows device assignment dialog', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.devices)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    // Find available device row and click assign button
    const deviceRow = screen.getByText('DL001').closest('tr');
    const assignButton = within(deviceRow!).getByRole('button', { name: /割当/i });
    await user.click(assignButton);

    await waitFor(() => {
      expect(screen.getByText(/端末を割り当て/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/社員を選択/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/使用目的/i)).toBeInTheDocument();
    });
  });

  it('assigns device to employee', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.devices)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.employees)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          device: '1',
          employee: '1',
          assigned_date: '2023-06-01',
          purpose: '開発業務用',
          status: 'ACTIVE'
        })
      });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const deviceRow = screen.getByText('DL001').closest('tr');
    const assignButton = within(deviceRow!).getByRole('button', { name: /割当/i });
    await user.click(assignButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/社員を選択/i)).toBeInTheDocument();
    });

    // Fill assignment form
    await user.selectOptions(screen.getByLabelText(/社員を選択/i), '1');
    await user.type(screen.getByLabelText(/使用目的/i), '開発業務用');

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

  it('shows device return dialog for assigned devices', async () => {
    const user = userEvent.setup();
    const assignedDevicesResponse = {
      ...mockApiResponses.devices,
      results: [
        {
          ...mockApiResponses.devices.results[1],
          status: 'ASSIGNED',
          current_assignment: {
            id: '1',
            employee_name: '田中太郎',
            assigned_date: '2023-05-01',
            purpose: '開発業務用'
          }
        }
      ]
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(assignedDevicesResponse)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true
      }
    });

    await waitFor(() => {
      expect(screen.getByText('HP EliteDesk 800')).toBeInTheDocument();
    });

    const deviceRow = screen.getByText('HP001').closest('tr');
    const returnButton = within(deviceRow!).getByRole('button', { name: /返却/i });
    await user.click(returnButton);

    expect(screen.getByText(/端末を返却/i)).toBeInTheDocument();
    expect(screen.getByText(/田中太郎/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/返却日/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/返却時の備考/i)).toBeInTheDocument();
  });

  it('filters devices by type', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const typeFilter = screen.getByLabelText(/端末種別でフィルター/i);
    await user.selectOptions(typeFilter, 'LAPTOP');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [mockApiResponses.devices.results[0]],
        count: 1,
        next: null,
        previous: null
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('type=LAPTOP'),
        expect.any(Object)
      );
    });
  });

  it('filters devices by status', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const statusFilter = screen.getByLabelText(/ステータスでフィルター/i);
    await user.selectOptions(statusFilter, 'AVAILABLE');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [mockApiResponses.devices.results[0]],
        count: 1,
        next: null,
        previous: null
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('status=AVAILABLE'),
        expect.any(Object)
      );
    });
  });

  it('shows device statistics', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.devices)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          total_devices: 10,
          available_devices: 6,
          assigned_devices: 3,
          maintenance_devices: 1,
          status_breakdown: {
            AVAILABLE: 6,
            ASSIGNED: 3,
            MAINTENANCE: 1
          },
          type_breakdown: {
            LAPTOP: 5,
            DESKTOP: 3,
            TABLET: 2
          }
        })
      });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    // Check statistics display
    expect(screen.getByText(/総端末数: 10/i)).toBeInTheDocument();
    expect(screen.getByText(/利用可能: 6/i)).toBeInTheDocument();
    expect(screen.getByText(/貸出中: 3/i)).toBeInTheDocument();
  });

  it('handles device deletion', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const deviceRow = screen.getByText('DL001').closest('tr');
    const deleteButton = within(deviceRow!).getByRole('button', { name: /削除/i });
    await user.click(deleteButton);

    // Confirm deletion
    expect(screen.getByText(/端末を削除しますか/i)).toBeInTheDocument();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({})
    });

    const confirmButton = screen.getByRole('button', { name: /削除する/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/devices/1/'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  it('shows validation errors in device form', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.devices)
    });

    render(<DeviceManagement />, {
      queryClient,
      authValue: {
        user: mockAdminUser,
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

    const addButton = screen.getByRole('button', { name: /新しい端末を追加/i });
    await user.click(addButton);

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /追加/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/端末種別は必須です/i)).toBeInTheDocument();
      expect(screen.getByText(/メーカーは必須です/i)).toBeInTheDocument();
      expect(screen.getByText(/モデルは必須です/i)).toBeInTheDocument();
      expect(screen.getByText(/シリアル番号は必須です/i)).toBeInTheDocument();
    });
  });
});