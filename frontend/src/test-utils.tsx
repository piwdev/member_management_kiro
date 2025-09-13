/**
 * Test utilities for React components
 * Provides custom render function with providers and common test helpers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n';
import { AuthProvider } from './contexts/AuthContext';

// Mock user for testing
export const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  employee_id: 'EMP001',
  department: 'IT',
  position: 'Developer',
  location: 'TOKYO',
  full_name: 'Test User',
  is_staff: false,
  is_superuser: false
};

export const mockAdminUser = {
  ...mockUser,
  id: '2',
  username: 'admin',
  email: 'admin@example.com',
  employee_id: 'ADMIN001',
  position: 'Administrator',
  is_staff: true,
  is_superuser: true
};

// Mock auth context value
export const mockAuthContextValue = {
  user: mockUser,
  token: 'mock-token',
  login: jest.fn(),
  logout: jest.fn(),
  isLoading: false,
  isAuthenticated: true
};

export const mockUnauthenticatedContextValue = {
  user: null,
  token: null,
  login: jest.fn(),
  logout: jest.fn(),
  isLoading: false,
  isAuthenticated: false
};

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authValue?: typeof mockAuthContextValue;
  queryClient?: QueryClient;
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: ReactElement,
  {
    authValue = mockAuthContextValue,
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
        mutations: {
          retry: false,
        },
      },
    }),
    initialEntries = ['/'],
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <I18nextProvider i18n={i18n}>
            <AuthProvider value={authValue}>
              {children}
            </AuthProvider>
          </I18nextProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Mock API responses
export const mockApiResponses = {
  employees: {
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
    count: 2,
    next: null,
    previous: null
  },
  
  devices: {
    results: [
      {
        id: '1',
        type: 'LAPTOP',
        manufacturer: 'Dell',
        model: 'Latitude 5520',
        serial_number: 'DL001',
        status: 'AVAILABLE',
        purchase_date: '2023-01-15',
        warranty_expiry: '2026-01-15'
      },
      {
        id: '2',
        type: 'DESKTOP',
        manufacturer: 'HP',
        model: 'EliteDesk 800',
        serial_number: 'HP001',
        status: 'ASSIGNED',
        purchase_date: '2022-12-01',
        warranty_expiry: '2025-12-01'
      }
    ],
    count: 2,
    next: null,
    previous: null
  },
  
  licenses: {
    results: [
      {
        id: '1',
        software_name: 'Microsoft Office 365',
        license_type: 'Business Premium',
        total_count: 50,
        available_count: 35,
        used_count: 15,
        expiry_date: '2024-12-31',
        pricing_model: 'MONTHLY',
        unit_price: '1500.00'
      },
      {
        id: '2',
        software_name: 'JetBrains IntelliJ IDEA',
        license_type: 'Ultimate',
        total_count: 10,
        available_count: 7,
        used_count: 3,
        expiry_date: '2024-08-15',
        pricing_model: 'YEARLY',
        unit_price: '60000.00'
      }
    ],
    count: 2,
    next: null,
    previous: null
  },
  
  reports: {
    usage: {
      summary: {
        total_devices: 10,
        total_licenses: 5,
        active_assignments: 8,
        total_employees: 25
      },
      device_usage: [
        {
          device_serial: 'DL001',
          device_type: 'LAPTOP',
          employee_name: '田中太郎',
          department: '開発部',
          assigned_date: '2023-06-01'
        }
      ],
      license_usage: [
        {
          software_name: 'Microsoft Office 365',
          employee_name: '田中太郎',
          department: '開発部',
          assigned_date: '2023-06-01'
        }
      ]
    },
    
    cost: {
      summary: {
        total_monthly_cost: 75000,
        total_yearly_cost: 900000
      },
      license_costs: [
        {
          software_name: 'Microsoft Office 365',
          monthly_cost: 22500,
          yearly_cost: 270000,
          used_count: 15
        }
      ]
    }
  }
};

// Test helpers
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null
  });
  window.IntersectionObserver = mockIntersectionObserver;
};

// Mock localStorage
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock fetch
export const createMockFetch = (responses: Record<string, any>) => {
  return jest.fn((url: string) => {
    const matchedResponse = Object.entries(responses).find(([pattern]) => 
      url.includes(pattern)
    );
    
    if (matchedResponse) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(matchedResponse[1])
      });
    }
    
    return Promise.reject(new Error(`No mock response for ${url}`));
  });
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { renderWithProviders as render };