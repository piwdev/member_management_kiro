import { RegisterFormData } from '../types';

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string, t: (key: string) => string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push(t('auth.validation.passwordTooShort'));
  }
  
  if (!/[A-Za-z]/.test(password)) {
    errors.push(t('auth.validation.passwordNeedsLetter'));
  }
  
  if (!/\d/.test(password)) {
    errors.push(t('auth.validation.passwordNeedsNumber'));
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateEmployeeId = (employeeId: string): boolean => {
  // Employee ID format validation (alphanumeric, 3-20 characters)
  if (!employeeId) return true; // Optional field
  const employeeIdRegex = /^[A-Za-z0-9]{3,20}$/;
  return employeeIdRegex.test(employeeId);
};

export const validateRegistrationForm = (
  formData: RegisterFormData,
  t: (key: string) => string
): ValidationResult => {
  const errors: Record<string, string> = {};

  // Username validation
  if (!formData.username.trim()) {
    errors.username = t('auth.validation.usernameRequired');
  } else if (formData.username.length < 3) {
    errors.username = t('auth.validation.usernameMinLength');
  } else if (formData.username.length > 150) {
    errors.username = t('auth.validation.usernameMaxLength');
  } else if (!/^[A-Za-z0-9_.-]+$/.test(formData.username)) {
    errors.username = t('auth.validation.usernameInvalidChars');
  }

  // Email validation
  if (!formData.email.trim()) {
    errors.email = t('auth.validation.emailRequired');
  } else if (!validateEmail(formData.email)) {
    errors.email = t('auth.validation.emailInvalid');
  }

  // Password validation
  if (!formData.password) {
    errors.password = t('auth.validation.passwordRequired');
  } else {
    const passwordValidation = validatePassword(formData.password, t);
    if (!passwordValidation.isValid) {
      errors.password = passwordValidation.errors[0]; // Show first error
    }
  }

  // Confirm password validation
  if (!formData.confirmPassword) {
    errors.confirmPassword = t('auth.validation.confirmPasswordRequired');
  } else if (formData.password !== formData.confirmPassword) {
    errors.confirmPassword = t('auth.validation.passwordMismatch');
  }

  // First name validation
  if (!formData.firstName.trim()) {
    errors.firstName = t('auth.validation.firstNameRequired');
  } else if (formData.firstName.length > 30) {
    errors.firstName = t('auth.validation.firstNameMaxLength');
  }

  // Last name validation
  if (!formData.lastName.trim()) {
    errors.lastName = t('auth.validation.lastNameRequired');
  } else if (formData.lastName.length > 30) {
    errors.lastName = t('auth.validation.lastNameMaxLength');
  }

  // Department validation (optional but with length limit)
  if (formData.department && formData.department.length > 100) {
    errors.department = t('auth.validation.departmentMaxLength');
  }

  // Position validation (optional but with length limit)
  if (formData.position && formData.position.length > 100) {
    errors.position = t('auth.validation.positionMaxLength');
  }

  // Employee ID validation (optional)
  if (formData.employeeId && !validateEmployeeId(formData.employeeId)) {
    errors.employeeId = t('auth.validation.employeeIdInvalid');
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// Enhanced debounce with cancellation support
export const createDebouncedFunction = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
) => {
  let timeoutId: NodeJS.Timeout;
  
  const debouncedFunc = (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    return new Promise<ReturnType<T>>((resolve, reject) => {
      timeoutId = setTimeout(async () => {
        try {
          const result = await func(...args);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, delay);
    });
  };
  
  const cancel = () => {
    clearTimeout(timeoutId);
  };
  
  return { debouncedFunc, cancel };
};