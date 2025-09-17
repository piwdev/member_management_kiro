import React from 'react';
import { useTranslation } from 'react-i18next';

interface ServerErrorAlertProps {
  error?: string | null;
  errors?: Record<string, string>;
  onDismiss?: () => void;
  className?: string;
}

const ServerErrorAlert: React.FC<ServerErrorAlertProps> = ({ 
  error, 
  errors,
  onDismiss,
  className = '' 
}) => {
  const { t } = useTranslation();

  // Don't show if no errors
  if (!error && (!errors || Object.keys(errors).length === 0)) {
    return null;
  }

  const hasFieldErrors = errors && Object.keys(errors).length > 0;
  const hasGeneralError = error && error.trim().length > 0;

  return (
    <div className={`rounded-md bg-red-50 border border-red-200 p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          {hasGeneralError && (
            <h3 className="text-sm font-medium text-red-800 mb-2">
              {error}
            </h3>
          )}
          
          {hasFieldErrors && (
            <div>
              <h3 className="text-sm font-medium text-red-800 mb-2">
                {t('auth.registrationFailed')}
              </h3>
              <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                {Object.entries(errors).map(([field, message]) => (
                  <li key={field}>
                    <span className="font-medium">
                      {t(`auth.${field}`, { defaultValue: field })}:
                    </span>{' '}
                    {message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onDismiss}
                className="inline-flex bg-red-50 rounded-md p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50 focus:ring-red-600 transition-colors duration-200"
                aria-label={t('common.cancel')}
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServerErrorAlert;