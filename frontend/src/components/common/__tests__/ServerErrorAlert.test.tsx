import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../../i18n';
import ServerErrorAlert from '../ServerErrorAlert';

const renderWithI18n = (component: React.ReactElement) => {
  return render(
    <I18nextProvider i18n={i18n}>
      {component}
    </I18nextProvider>
  );
};

describe('ServerErrorAlert', () => {
  test('renders general error message', () => {
    renderWithI18n(<ServerErrorAlert error="Something went wrong" />);
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  test('renders field errors', () => {
    const errors = {
      username: 'Username is required',
      email: 'Email is invalid'
    };
    
    renderWithI18n(<ServerErrorAlert errors={errors} />);
    
    expect(screen.getByText('Username is required')).toBeInTheDocument();
    expect(screen.getByText('Email is invalid')).toBeInTheDocument();
  });

  test('renders both general error and field errors', () => {
    const errors = {
      username: 'Username is required'
    };
    
    renderWithI18n(<ServerErrorAlert error="General error" errors={errors} />);
    
    expect(screen.getByText('General error')).toBeInTheDocument();
    expect(screen.getByText('Username is required')).toBeInTheDocument();
  });

  test('does not render when no errors provided', () => {
    const { container } = renderWithI18n(<ServerErrorAlert />);
    
    expect(container.firstChild).toBeNull();
  });

  test('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = jest.fn();
    
    renderWithI18n(<ServerErrorAlert error="Test error" onDismiss={onDismiss} />);
    
    const dismissButton = screen.getByRole('button');
    fireEvent.click(dismissButton);
    
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  test('does not render dismiss button when onDismiss is not provided', () => {
    renderWithI18n(<ServerErrorAlert error="Test error" />);
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});