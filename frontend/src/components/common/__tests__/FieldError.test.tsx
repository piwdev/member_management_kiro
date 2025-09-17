import React from 'react';
import { render, screen } from '@testing-library/react';
import FieldError from '../FieldError';

describe('FieldError', () => {
  test('renders error message when error and touched are provided', () => {
    render(<FieldError error="This field is required" touched={true} />);
    
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  test('does not render when error is not provided', () => {
    const { container } = render(<FieldError touched={true} />);
    
    expect(container.firstChild).toBeNull();
  });

  test('does not render when touched is false', () => {
    const { container } = render(<FieldError error="This field is required" touched={false} />);
    
    expect(container.firstChild).toBeNull();
  });

  test('does not render when touched is not provided and defaults to true but no error', () => {
    const { container } = render(<FieldError />);
    
    expect(container.firstChild).toBeNull();
  });

  test('renders with custom className', () => {
    const { container } = render(
      <FieldError error="Test error" touched={true} className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });
});