import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Employee } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface EmployeeFormProps {
  employee?: Employee;
  onSave: (employee: Employee) => void;
  onCancel: () => void;
}

interface EmployeeFormData {
  employeeId: string;
  name: string;
  email: string;
  department: string;
  position: string;
  location: 'TOKYO' | 'OKINAWA' | 'REMOTE';
  hireDate: string;
  status: 'ACTIVE' | 'INACTIVE';
}

const EmployeeForm: React.FC<EmployeeFormProps> = ({
  employee,
  onSave,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<EmployeeFormData>({
    employeeId: '',
    name: '',
    email: '',
    department: '',
    position: '',
    location: 'TOKYO',
    hireDate: '',
    status: 'ACTIVE',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const isEditing = !!employee;

  useEffect(() => {
    if (employee) {
      setFormData({
        employeeId: employee.employeeId,
        name: employee.name,
        email: employee.email,
        department: employee.department,
        position: employee.position,
        location: employee.location,
        hireDate: employee.hireDate.split('T')[0], // Convert to YYYY-MM-DD format
        status: employee.status,
      });
    }
  }, [employee]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: [],
      }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string[]> = {};

    if (!formData.employeeId.trim()) {
      errors.employeeId = ['社員IDは必須です'];
    }

    if (!formData.name.trim()) {
      errors.name = ['氏名は必須です'];
    }

    if (!formData.email.trim()) {
      errors.email = ['メールアドレスは必須です'];
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = ['有効なメールアドレスを入力してください'];
    }

    if (!formData.department.trim()) {
      errors.department = ['部署は必須です'];
    }

    if (!formData.position.trim()) {
      errors.position = ['役職は必須です'];
    }

    if (!formData.hireDate) {
      errors.hireDate = ['入社日は必須です'];
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const submitData = {
        ...formData,
        hireDate: formData.hireDate, // Keep as YYYY-MM-DD format for API
      };

      let response;
      if (isEditing) {
        response = await apiClient.put(`/employees/${employee.id}/`, submitData);
      } else {
        response = await apiClient.post('/employees/', submitData);
      }

      onSave(response.data);
    } catch (err: any) {
      if (err.response?.data?.details) {
        setFieldErrors(err.response.data.details);
      } else {
        setError(err.response?.data?.message || t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const getLocationLabel = (location: string) => {
    switch (location) {
      case 'TOKYO': return '東京';
      case 'OKINAWA': return '沖縄';
      case 'REMOTE': return 'リモート';
      default: return location;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'アクティブ';
      case 'INACTIVE': return '非アクティブ';
      default: return status;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {isEditing ? '社員情報編集' : '新規社員登録'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {error && <ErrorMessage message={error} />}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Employee ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.employeeId')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="employeeId"
                value={formData.employeeId}
                onChange={handleInputChange}
                disabled={isEditing} // Employee ID should not be editable
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.employeeId ? 'border-red-500' : 'border-gray-300'
                } ${isEditing ? 'bg-gray-100' : ''}`}
                placeholder="例: EMP001"
              />
              {fieldErrors.employeeId && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.employeeId[0]}</p>
              )}
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.name')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: 田中太郎"
              />
              {fieldErrors.name && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.name[0]}</p>
              )}
            </div>

            {/* Email */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.email')} <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.email ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: tanaka@company.com"
              />
              {fieldErrors.email && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.email[0]}</p>
              )}
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.department')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.department ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: 開発部"
              />
              {fieldErrors.department && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.department[0]}</p>
              )}
            </div>

            {/* Position */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.position')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="position"
                value={formData.position}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.position ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: シニアエンジニア"
              />
              {fieldErrors.position && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.position[0]}</p>
              )}
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.location')} <span className="text-red-500">*</span>
              </label>
              <select
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.location ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="TOKYO">{getLocationLabel('TOKYO')}</option>
                <option value="OKINAWA">{getLocationLabel('OKINAWA')}</option>
                <option value="REMOTE">{getLocationLabel('REMOTE')}</option>
              </select>
              {fieldErrors.location && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.location[0]}</p>
              )}
            </div>

            {/* Hire Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.hireDate')} <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="hireDate"
                value={formData.hireDate}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.hireDate ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {fieldErrors.hireDate && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.hireDate[0]}</p>
              )}
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.status')} <span className="text-red-500">*</span>
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.status ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="ACTIVE">{getStatusLabel('ACTIVE')}</option>
                <option value="INACTIVE">{getStatusLabel('INACTIVE')}</option>
              </select>
              {fieldErrors.status && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.status[0]}</p>
              )}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
            >
              {loading && <LoadingSpinner size="sm" className="mr-2" />}
              {t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmployeeForm;