import React from 'react';

interface FieldErrorProps {
  error?: string;
  touched?: boolean;
  className?: string;
}

const FieldError: React.FC<FieldErrorProps> = ({ 
  error, 
  touched = true, 
  className = '' 
}) => {
  if (!error || !touched) return null;

  return (
    <div className={`mt-1 flex items-center ${className}`}>
      <svg
        className="h-4 w-4 text-red-500 mr-1 flex-shrink-0"
        fill="currentColor"
        viewBox="0 0 20 20"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <p className="text-sm text-red-600" role="alert">
        {error}
      </p>
    </div>
  );
};

export default FieldError;