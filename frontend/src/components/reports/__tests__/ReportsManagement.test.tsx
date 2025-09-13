/**
 * Tests for ReportsManagement component
 */

import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import { render, mockApiResponses, mockAdminUser } from '../../../test-utils';
import ReportsManagement from '../ReportsManagement';

// Mock the API
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock file download
const mockCreateObjectURL = jest.fn();
const mockRevokeObjectURL = jest.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

// Mock link click for download
const mockClick = jest.fn();
HTMLAnchorElement.prototype.click = mockClick;

describe('ReportsManagement', () => {
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

  it('renders reports management interface correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [
          {
            id: '1',
            name: 'Usage Report',
            report_type: 'USAGE',
            generated_at: '2023-11-01T10:00:00Z',
            generated_by_name: 'Admin User',
            file_size: 1024
          },
          {
            id: '2',
            name: 'Cost Analysis',
            report_type: 'COST',
            generated_at: '2023-10-28T15:30:00Z',
            generated_by_name: 'Admin User',
            file_size: 2048
          }
        ],
        count: 2,
        next: null,
        previous: null
      })
    });

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
      expect(screen.getByText('Usage Report')).toBeInTheDocument();
      expect(screen.getByText('Cost Analysis')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /新しいレポートを生成/i })).toBeInTheDocument();
  });

  it('opens report generation modal', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
    });

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    expect(screen.getByText(/レポート生成/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/レポート種別/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/開始日/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/終了日/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/出力形式/i)).toBeInTheDocument();
  });

  it('generates usage report successfully', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.reports.usage)
      });

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill form
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'USAGE');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');
    await user.selectOptions(screen.getByLabelText(/出力形式/i), 'JSON');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/reports/generate/usage/'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('2023-10-01')
        })
      );
    });

    // Should show report results
    await waitFor(() => {
      expect(screen.getByText(/総端末数: 10/i)).toBeInTheDocument();
      expect(screen.getByText(/総ライセンス数: 5/i)).toBeInTheDocument();
    });
  });

  it('generates cost analysis report successfully', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.reports.cost)
      });

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill form
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'COST');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');
    await user.selectOptions(screen.getByLabelText(/出力形式/i), 'JSON');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/reports/generate/cost/'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    // Should show cost analysis results
    await waitFor(() => {
      expect(screen.getByText(/月額コスト: ¥75,000/i)).toBeInTheDocument();
      expect(screen.getByText(/年額コスト: ¥900,000/i)).toBeInTheDocument();
    });
  });

  it('downloads report as CSV', async () => {
    const user = userEvent.setup();
    const csvContent = 'software_name,monthly_cost\nMicrosoft Office 365,22500';
    
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve(csvContent),
        headers: new Headers({ 'content-type': 'text/csv' })
      });

    mockCreateObjectURL.mockReturnValue('blob:mock-url');

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill form for CSV download
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'COST');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');
    await user.selectOptions(screen.getByLabelText(/出力形式/i), 'CSV');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalledWith(expect.any(Blob));
      expect(mockClick).toHaveBeenCalled();
    });
  });

  it('downloads report as PDF', async () => {
    const user = userEvent.setup();
    const pdfContent = new ArrayBuffer(1024);
    
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        arrayBuffer: () => Promise.resolve(pdfContent),
        headers: new Headers({ 'content-type': 'application/pdf' })
      });

    mockCreateObjectURL.mockReturnValue('blob:mock-url');

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill form for PDF download
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'INVENTORY');
    await user.selectOptions(screen.getByLabelText(/出力形式/i), 'PDF');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalledWith(expect.any(Blob));
      expect(mockClick).toHaveBeenCalled();
    });
  });

  it('filters reports by type', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [
          {
            id: '1',
            name: 'Usage Report',
            report_type: 'USAGE',
            generated_at: '2023-11-01T10:00:00Z',
            generated_by_name: 'Admin User',
            file_size: 1024
          }
        ],
        count: 1,
        next: null,
        previous: null
      })
    });

    render(<ReportsManagement />, {
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
      expect(screen.getByText('Usage Report')).toBeInTheDocument();
    });

    const typeFilter = screen.getByLabelText(/レポート種別でフィルター/i);
    await user.selectOptions(typeFilter, 'USAGE');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: [
          {
            id: '1',
            name: 'Usage Report',
            report_type: 'USAGE',
            generated_at: '2023-11-01T10:00:00Z',
            generated_by_name: 'Admin User',
            file_size: 1024
          }
        ],
        count: 1,
        next: null,
        previous: null
      })
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('report_type=USAGE'),
        expect.any(Object)
      );
    });
  });

  it('downloads existing report file', async () => {
    const user = userEvent.setup();
    const reportContent = new ArrayBuffer(1024);
    
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            {
              id: '1',
              name: 'Usage Report',
              report_type: 'USAGE',
              generated_at: '2023-11-01T10:00:00Z',
              generated_by_name: 'Admin User',
              file_size: 1024,
              file_path: '/reports/usage_report.pdf'
            }
          ],
          count: 1,
          next: null,
          previous: null
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        arrayBuffer: () => Promise.resolve(reportContent),
        headers: new Headers({ 'content-type': 'application/pdf' })
      });

    mockCreateObjectURL.mockReturnValue('blob:mock-url');

    render(<ReportsManagement />, {
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
      expect(screen.getByText('Usage Report')).toBeInTheDocument();
    });

    const reportRow = screen.getByText('Usage Report').closest('tr');
    const downloadButton = within(reportRow!).getByRole('button', { name: /ダウンロード/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/reports/1/download/'),
        expect.any(Object)
      );
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
    });
  });

  it('deletes report successfully', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            {
              id: '1',
              name: 'Usage Report',
              report_type: 'USAGE',
              generated_at: '2023-11-01T10:00:00Z',
              generated_by_name: 'Admin User',
              file_size: 1024
            }
          ],
          count: 1,
          next: null,
          previous: null
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({})
      });

    render(<ReportsManagement />, {
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
      expect(screen.getByText('Usage Report')).toBeInTheDocument();
    });

    const reportRow = screen.getByText('Usage Report').closest('tr');
    const deleteButton = within(reportRow!).getByRole('button', { name: /削除/i });
    await user.click(deleteButton);

    // Confirm deletion
    expect(screen.getByText(/レポートを削除しますか/i)).toBeInTheDocument();
    
    const confirmButton = screen.getByRole('button', { name: /削除する/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/reports/1/'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  it('shows report generation progress', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill and submit form
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'USAGE');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/生成中/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('handles report generation errors', async () => {
    const user = userEvent.setup();
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
      })
      .mockRejectedValueOnce(new Error('Report generation failed'));

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Fill and submit form
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'USAGE');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-01');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-31');

    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/レポート生成に失敗しました/i)).toBeInTheDocument();
    });
  });

  it('validates report generation form', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ results: [], count: 0, next: null, previous: null })
    });

    render(<ReportsManagement />, {
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
      expect(screen.getByText(/レポート管理/i)).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /新しいレポートを生成/i });
    await user.click(generateButton);

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /生成/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/レポート種別は必須です/i)).toBeInTheDocument();
    });

    // Fill report type but invalid date range
    await user.selectOptions(screen.getByLabelText(/レポート種別/i), 'USAGE');
    await user.type(screen.getByLabelText(/開始日/i), '2023-10-31');
    await user.type(screen.getByLabelText(/終了日/i), '2023-10-01'); // End before start

    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/終了日は開始日より後である必要があります/i)).toBeInTheDocument();
    });
  });
});