import React from 'react';
import { useTranslation } from 'react-i18next';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  text,
  className = ''
}) => {
  const { t } = useTranslation();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  // If className is provided, render just the spinner without the container
  if (className) {
    return (
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]} ${className}`}></div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`}></div>
      {text && (
        <p className="mt-2 text-sm text-gray-600">{text}</p>
      )}
      {!text && (
        <p className="mt-2 text-sm text-gray-600">{t('common.loading')}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;