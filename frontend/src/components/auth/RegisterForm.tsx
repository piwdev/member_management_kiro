import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { Navigate, Link, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../common/LoadingSpinner';
import FieldError from '../common/FieldError';
import ServerErrorAlert from '../common/ServerErrorAlert';
import SuccessAlert from '../common/SuccessAlert';
import LanguageSwitch from '../common/LanguageSwitch';
import { useToast } from '../common/ToastContainer';
import { RegisterFormData } from '../../types';
import { validateRegistrationForm, createDebouncedFunction } from '../../utils/validation';
import { checkUsernameAvailability, checkEmailAvailability } from '../../lib/api';

// Memoized form field component to prevent unnecessary re-renders
const FormField = React.memo<{
  id: string;
  name: string;
  type: string;
  label: string;
  placeholder: string;
  value: string;
  error?: string;
  touched?: boolean;
  required?: boolean;
  maxLength?: number;
  disabled?: boolean;
  isLoading?: boolean;
  loadingText?: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
}>(({ 
  id, name, type, label, placeholder, value, error, touched, required, 
  maxLength, disabled, isLoading, loadingText, onChange, onBlur 
}) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700">
      {label} {required && '*'}
      {isLoading && (
        <span className="ml-2 inline-flex items-center">
          <LoadingSpinner size="sm" className="h-3 w-3" />
          <span className="ml-1 text-xs text-gray-500">{loadingText}</span>
        </span>
      )}
    </label>
    <input
      id={id}
      name={name}
      type={type}
      required={required}
      maxLength={maxLength}
      className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
        error && touched ? 'border-red-300' : 'border-gray-300'
      } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      disabled={disabled}
    />
    <FieldError error={error} touched={touched} />
  </div>
));

// Memoized select field component
const SelectField = React.memo<{
  id: string;
  name: string;
  label: string;
  value: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onBlur: (e: React.FocusEvent<HTMLSelectElement>) => void;
}>(({ id, name, label, value, options, disabled, onChange, onBlur }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700">
      {label}
    </label>
    <select
      id={id}
      name={name}
      className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      disabled={disabled}
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
));

const RegisterForm: React.FC = () => {
  const { t } = useTranslation();
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    department: '',
    position: '',
    location: '',
    employeeId: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [serverFieldErrors, setServerFieldErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSuccess, setIsSuccess] = useState(false);
  const [redirectCountdown, setRedirectCountdown] = useState(5);
  const [fieldValidationLoading, setFieldValidationLoading] = useState<Record<string, boolean>>({});
  
  // Refs to track debounced function instances
  const debouncedFunctionsRef = useRef<{
    username?: { debouncedFunc: any; cancel: () => void };
    email?: { debouncedFunc: any; cancel: () => void };
  }>({});

  // Memoized validation function to prevent unnecessary re-creation
  const validateForm = useCallback((data: RegisterFormData) => {
    return validateRegistrationForm(data, t);
  }, [t]);

  // Debounced duplicate checking functions
  const checkUsernameDuplicate = useCallback(async (username: string) => {
    if (!username || username.length < 3) return;
    
    setFieldValidationLoading(prev => ({ ...prev, username: true }));
    try {
      const result = await checkUsernameAvailability(username);
      if (!result.available) {
        setErrors(prev => ({ ...prev, username: t('auth.validation.usernameExists') }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          if (newErrors.username === t('auth.validation.usernameExists')) {
            delete newErrors.username;
          }
          return newErrors;
        });
      }
    } catch (error) {
      console.error('Username availability check failed:', error);
    } finally {
      setFieldValidationLoading(prev => ({ ...prev, username: false }));
    }
  }, [t]);

  const checkEmailDuplicate = useCallback(async (email: string) => {
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return;
    
    setFieldValidationLoading(prev => ({ ...prev, email: true }));
    try {
      const result = await checkEmailAvailability(email);
      if (!result.available) {
        setErrors(prev => ({ ...prev, email: t('auth.validation.emailExists') }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          if (newErrors.email === t('auth.validation.emailExists')) {
            delete newErrors.email;
          }
          return newErrors;
        });
      }
    } catch (error) {
      console.error('Email availability check failed:', error);
    } finally {
      setFieldValidationLoading(prev => ({ ...prev, email: false }));
    }
  }, [t]);

  // Create debounced functions with memoization
  const debouncedUsernameCheck = useMemo(() => {
    // Cancel previous debounced function if it exists
    if (debouncedFunctionsRef.current.username) {
      debouncedFunctionsRef.current.username.cancel();
    }
    
    const { debouncedFunc, cancel } = createDebouncedFunction(checkUsernameDuplicate, 500);
    debouncedFunctionsRef.current.username = { debouncedFunc, cancel };
    return debouncedFunc;
  }, [checkUsernameDuplicate]);

  const debouncedEmailCheck = useMemo(() => {
    // Cancel previous debounced function if it exists
    if (debouncedFunctionsRef.current.email) {
      debouncedFunctionsRef.current.email.cancel();
    }
    
    const { debouncedFunc, cancel } = createDebouncedFunction(checkEmailDuplicate, 500);
    debouncedFunctionsRef.current.email = { debouncedFunc, cancel };
    return debouncedFunc;
  }, [checkEmailDuplicate]);

  // Debounced local validation
  const debouncedLocalValidation = useMemo(() => {
    const { debouncedFunc } = createDebouncedFunction((data: RegisterFormData) => {
      const validation = validateForm(data);
      setErrors(prev => ({ ...prev, ...validation.errors }));
    }, 300);
    return debouncedFunc;
  }, [validateForm]);

  // Memoized form validation result to prevent unnecessary re-calculations
  const formValidationResult = useMemo(() => {
    return validateForm(formData);
  }, [formData, validateForm]);

  // Effect to validate form on mount and when translation changes
  useEffect(() => {
    setErrors(formValidationResult.errors);
  }, [formValidationResult.errors]);

  // Effect to handle success countdown and redirect
  useEffect(() => {
    if (isSuccess && redirectCountdown > 0) {
      const timer = setTimeout(() => {
        setRedirectCountdown(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (isSuccess && redirectCountdown === 0) {
      navigate('/login');
    }
  }, [isSuccess, redirectCountdown, navigate]);

  // Cleanup effect to cancel debounced functions on unmount
  useEffect(() => {
    const currentFunctions = debouncedFunctionsRef.current;
    return () => {
      // Cancel all debounced functions when component unmounts
      Object.values(currentFunctions).forEach(({ cancel }) => {
        if (cancel) cancel();
      });
    };
  }, []);

  // Memoized location options to prevent recreation on every render
  const locationOptions = useMemo(() => [
    { value: '', label: t('auth.location') },
    { value: 'TOKYO', label: t('auth.locations.TOKYO') },
    { value: 'OKINAWA', label: t('auth.locations.OKINAWA') },
    { value: 'REMOTE', label: t('auth.locations.REMOTE') }
  ], [t]);

  // Memoized form submission disabled state
  const isSubmitDisabled = useMemo(() => {
    return isLoading || !formValidationResult.isValid || 
           fieldValidationLoading.username || fieldValidationLoading.email;
  }, [isLoading, formValidationResult.isValid, fieldValidationLoading.username, fieldValidationLoading.email]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    const newFormData = { ...formData, [name]: value };
    setFormData(newFormData);
    
    // Mark field as touched
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // Clear server errors when user starts typing
    if (serverError) {
      setServerError(null);
    }
    if (serverFieldErrors[name]) {
      setServerFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    
    // Clear existing validation errors for the field being edited
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[name];
      return newErrors;
    });
    
    // Trigger debounced local validation
    debouncedLocalValidation(newFormData);
    
    // Trigger debounced duplicate checking for username and email
    if (name === 'username' && value.trim().length >= 3) {
      debouncedUsernameCheck(value.trim());
    } else if (name === 'email' && value.trim()) {
      debouncedEmailCheck(value.trim());
    }
  }, [formData, serverError, serverFieldErrors, debouncedLocalValidation, debouncedUsernameCheck, debouncedEmailCheck]);

  const handleBlur = useCallback((e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // Immediate validation on blur for better UX
    const validation = validateForm(formData);
    setErrors(prev => ({ ...prev, ...validation.errors }));
  }, [formData, validateForm]);

  const validateFormForSubmit = useCallback((): boolean => {
    const validation = validateForm(formData);
    setErrors(validation.errors);
    return validation.isValid;
  }, [formData, validateForm]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);
    
    if (!validateFormForSubmit()) return;
    
    setIsLoading(true);
    
    try {
      await register(formData);
      
      // Set success state
      setIsSuccess(true);
      
      // Show success toast
      showSuccess(
        t('auth.registrationSuccess'),
        t('auth.registrationSuccessMessage')
      );
      
    } catch (err: any) {
      if (err.response?.data?.details) {
        // Handle field-specific errors from server
        const serverErrors: Record<string, string> = {};
        Object.keys(err.response.data.details).forEach(field => {
          const messages = err.response.data.details[field];
          if (Array.isArray(messages) && messages.length > 0) {
            serverErrors[field] = messages[0];
          }
        });
        setServerFieldErrors(serverErrors);
        setErrors(prev => ({ ...prev, ...serverErrors }));
        
        // Show toast for field errors
        showError(
          t('auth.registrationFailed'), 
          t('common.error')
        );
      } else {
        const errorMessage = err.response?.data?.message || t('auth.registrationFailed');
        setServerError(errorMessage);
        showError(t('auth.registrationFailed'), errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  }, [formData, validateFormForSubmit, register, showSuccess, showError, t]);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-end mb-4">
            <LanguageSwitch />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Asset License Management
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {t('auth.register')}
          </p>
        </div>
        
        {isSuccess && (
          <div className="mt-8 space-y-4">
            <SuccessAlert
              title={t('auth.registrationSuccess')}
              message={t('auth.registrationSuccessCountdown', { seconds: redirectCountdown })}
            />
            <div className="text-center">
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              >
                {t('auth.loginHere')}
              </button>
            </div>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit} style={{ display: isSuccess ? 'none' : 'block' }}>
          <div className="space-y-4">
            <FormField
              id="username"
              name="username"
              type="text"
              label={t('auth.username')}
              placeholder={t('auth.username')}
              value={formData.username}
              error={errors.username}
              touched={touched.username}
              required
              disabled={isLoading}
              isLoading={fieldValidationLoading.username}
              loadingText={t('common.checking')}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="email"
              name="email"
              type="email"
              label={t('auth.email')}
              placeholder={t('auth.email')}
              value={formData.email}
              error={errors.email}
              touched={touched.email}
              required
              disabled={isLoading}
              isLoading={fieldValidationLoading.email}
              loadingText={t('common.checking')}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="password"
              name="password"
              type="password"
              label={t('auth.password')}
              placeholder={t('auth.password')}
              value={formData.password}
              error={errors.password}
              touched={touched.password}
              required
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              label={t('auth.confirmPassword')}
              placeholder={t('auth.confirmPassword')}
              value={formData.confirmPassword}
              error={errors.confirmPassword}
              touched={touched.confirmPassword}
              required
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="firstName"
              name="firstName"
              type="text"
              label={t('auth.firstName')}
              placeholder={t('auth.firstName')}
              value={formData.firstName}
              error={errors.firstName}
              touched={touched.firstName}
              required
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="lastName"
              name="lastName"
              type="text"
              label={t('auth.lastName')}
              placeholder={t('auth.lastName')}
              value={formData.lastName}
              error={errors.lastName}
              touched={touched.lastName}
              required
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="department"
              name="department"
              type="text"
              label={t('auth.department')}
              placeholder={t('auth.department')}
              value={formData.department}
              maxLength={100}
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="position"
              name="position"
              type="text"
              label={t('auth.position')}
              placeholder={t('auth.position')}
              value={formData.position}
              maxLength={100}
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <SelectField
              id="location"
              name="location"
              label={t('auth.location')}
              value={formData.location}
              options={locationOptions}
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />

            <FormField
              id="employeeId"
              name="employeeId"
              type="text"
              label={t('auth.employeeId')}
              placeholder={t('auth.employeeId')}
              value={formData.employeeId || ''}
              error={errors.employeeId}
              touched={touched.employeeId}
              maxLength={20}
              disabled={isLoading}
              onChange={handleInputChange}
              onBlur={handleBlur}
            />
          </div>

          <ServerErrorAlert 
            error={serverError} 
            errors={serverFieldErrors}
            onDismiss={() => {
              setServerError(null);
              setServerFieldErrors({});
            }}
          />

          <div>
            <button
              type="submit"
              disabled={isSubmitDisabled}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">{t('common.loading')}</span>
                </div>
              ) : fieldValidationLoading.username || fieldValidationLoading.email ? (
                <div className="flex items-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">{t('common.checking')}</span>
                </div>
              ) : (
                t('auth.register')
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              {t('auth.alreadyHaveAccount')}{' '}
              <Link
                to="/login"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                {t('auth.loginHere')}
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterForm;