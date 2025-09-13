/**
 * Tests for LoginForm component
 */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockUnauthenticatedContextValue } from '../../../test-utils';
import LoginForm from '../LoginForm';

// Mock the API
const mockLogin = jest.fn();
jest.mock('../../../lib/api', () => ({
  login: (...args: any[]) => mockLogin(...args)
}));

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders login form correctly', () => {
    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    expect(screen.getByLabelText(/ユーザー名/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/パスワード/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ログイン/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup();
    
    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const submitButton = screen.getByRole('button', { name: /ログイン/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/ユーザー名は必須です/i)).toBeInTheDocument();
      expect(screen.getByText(/パスワードは必須です/i)).toBeInTheDocument();
    });
  });

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue({
      access: 'mock-token',
      refresh: 'mock-refresh-token',
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      }
    });

    const mockLoginFn = jest.fn();
    render(<LoginForm />, {
      authValue: {
        ...mockUnauthenticatedContextValue,
        login: mockLoginFn
      }
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
      expect(mockLoginFn).toHaveBeenCalled();
    });
  });

  it('shows error message on login failure', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));

    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/ログインに失敗しました/i)).toBeInTheDocument();
    });
  });

  it('disables submit button while loading', async () => {
    const user = userEvent.setup();
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/ログイン中/i)).toBeInTheDocument();
  });

  it('handles account lockout error', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue({
      response: {
        status: 401,
        data: { error: 'アカウントがロックされています' }
      }
    });

    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/アカウントがロックされています/i)).toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);

    // Tab navigation
    await user.tab();
    expect(usernameInput).toHaveFocus();

    await user.tab();
    expect(passwordInput).toHaveFocus();

    await user.tab();
    expect(screen.getByRole('button', { name: /ログイン/i })).toHaveFocus();
  });

  it('remembers username if "Remember me" is checked', async () => {
    const user = userEvent.setup();
    const mockSetItem = jest.fn();
    Object.defineProperty(window, 'localStorage', {
      value: {
        setItem: mockSetItem,
        getItem: jest.fn(),
        removeItem: jest.fn()
      }
    });

    render(<LoginForm />, {
      authValue: mockUnauthenticatedContextValue
    });

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const rememberCheckbox = screen.getByLabelText(/ログイン情報を記憶/i);

    await user.type(usernameInput, 'testuser');
    await user.click(rememberCheckbox);

    expect(mockSetItem).toHaveBeenCalledWith('rememberedUsername', 'testuser');
  });
});