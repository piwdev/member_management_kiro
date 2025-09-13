/**
 * Tests for EmployeeList component
 */

import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import { render, mockApiResponses, mockAdminUser } from '../../../test-utils';
import EmployeeList from '../EmployeeList';

// Mock the API
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('EmployeeList', () => {
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

  it('renders employee list correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
      expect(screen.getByText('佐藤花子')).toBeInTheDocument();
    });

    expect(screen.getByText('EMP001')).toBeInTheDocument();
    expect(screen.getByText('開発部')).toBeInTheDocument();
    expect(screen.getByText('営業部')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<EmployeeList />, {
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

    expect(screen.getByText(/読み込み中/i)).toBeInTheDocument();
  });

  it('shows error state on API failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'));

    render(<EmployeeList />, {
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
      expect(screen.getByText(/エラーが発生しました/i)).toBeInTheDocument();
    });
  });

  it('filters employees by search term', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/社員を検索/i);
    await user.type(searchInput, '田中');

    // Mock filtered response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [mockApiResponses.employees.results[0]],
        count: 1,
        next: null,
        previous: null
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('search=田中'),
        expect.any(Object)
      );
    });
  });

  it('filters employees by department', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    const departmentFilter = screen.getByLabelText(/部署でフィルター/i);
    await user.selectOptions(departmentFilter, '開発部');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [mockApiResponses.employees.results[0]],
        count: 1,
        next: null,
        previous: null
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('department=開発部'),
        expect.any(Object)
      );
    });
  });

  it('sorts employees by different columns', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    // Click on name column header to sort
    const nameHeader = screen.getByText('氏名');
    await user.click(nameHeader);

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('ordering=name'),
        expect.any(Object)
      );
    });
  });

  it('navigates to employee detail on row click', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    const employeeRow = screen.getByText('田中太郎').closest('tr');
    await user.click(employeeRow!);

    expect(mockNavigate).toHaveBeenCalledWith('/employees/1');
  });

  it('shows pagination controls', async () => {
    const paginatedResponse = {
      ...mockApiResponses.employees,
      count: 25,
      next: 'http://api/employees/?page=2',
      previous: null
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(paginatedResponse)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    expect(screen.getByText(/25件中 1-2件を表示/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /次のページ/i })).toBeInTheDocument();
  });

  it('handles pagination navigation', async () => {
    const user = userEvent.setup();
    const paginatedResponse = {
      ...mockApiResponses.employees,
      count: 25,
      next: 'http://api/employees/?page=2',
      previous: null
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(paginatedResponse)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /次のページ/i });
    await user.click(nextButton);

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        ...paginatedResponse,
        next: null,
        previous: 'http://api/employees/?page=1'
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page=2'),
        expect.any(Object)
      );
    });
  });

  it('shows employee status badges correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        ...mockApiResponses.employees,
        results: [
          ...mockApiResponses.employees.results,
          {
            id: '3',
            employee_id: 'EMP003',
            name: '退職太郎',
            email: 'retired@example.com',
            department: 'IT',
            position: 'Developer',
            location: 'TOKYO',
            status: 'INACTIVE',
            is_active: false
          }
        ]
      })
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
      expect(screen.getByText('退職太郎')).toBeInTheDocument();
    });

    // Check status badges
    const activeEmployeeRow = screen.getByText('田中太郎').closest('tr');
    const inactiveEmployeeRow = screen.getByText('退職太郎').closest('tr');

    expect(within(activeEmployeeRow!).getByText('アクティブ')).toBeInTheDocument();
    expect(within(inactiveEmployeeRow!).getByText('非アクティブ')).toBeInTheDocument();
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.employees)
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText('田中太郎')).toBeInTheDocument();
    });

    // Tab to search input
    await user.tab();
    expect(screen.getByPlaceholderText(/社員を検索/i)).toHaveFocus();

    // Tab to department filter
    await user.tab();
    expect(screen.getByLabelText(/部署でフィルター/i)).toHaveFocus();
  });

  it('shows empty state when no employees found', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [],
        count: 0,
        next: null,
        previous: null
      })
    });

    render(<EmployeeList />, {
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
      expect(screen.getByText(/社員が見つかりませんでした/i)).toBeInTheDocument();
    });
  });
});