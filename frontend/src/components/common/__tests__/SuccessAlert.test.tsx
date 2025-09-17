import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../../i18n';
import SuccessAlert from '../SuccessAlert';

const renderWithI18n = (component: React.ReactElement) => {
  return render(
    <I18nextProvider i18n={i18n}>
      {component}
    </I18nextProvider>
  );
};

describe('SuccessAlert', () => {
  test('renders title', () => {
    renderWithI18n(<SuccessAlert title="Success!" />);
    
    expect(screen.getByText('Success!')).toBeInTheDocument();
  });

  test('renders title and message', () => {
    renderWithI18n(<SuccessAlert title="Success!" message="Operation completed successfully" />);
    
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
  });

  test('renders with icon by default', () => {
    const { container } = renderWithI18n(<SuccessAlert title="Success!" />);
    
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  test('does not render icon when showIcon is false', () => {
    const { container } = renderWithI18n(<SuccessAlert title="Success!" showIcon={false} />);
    
    expect(container.querySelector('svg')).toBeNull();
  });

  test('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = jest.fn();
    
    renderWithI18n(<SuccessAlert title="Success!" onDismiss={onDismiss} />);
    
    const dismissButton = screen.getByRole('button');
    fireEvent.click(dismissButton);
    
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  test('does not render dismiss button when onDismiss is not provided', () => {
    renderWithI18n(<SuccessAlert title="Success!" />);
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  test('applies custom className', () => {
    const { container } = renderWithI18n(<SuccessAlert title="Success!" className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });
});