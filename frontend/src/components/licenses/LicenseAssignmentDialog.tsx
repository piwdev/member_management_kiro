import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { License, Employee } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface LicenseAssignmentDialogProps {
  license: License;
  onAssign: () => void;
  onCancel: () => void;
}

interface AssignmentFormData {
  employeeId: string;
  purpose: string;
  startDate: string;
  endDate?: string;
}

const LicenseAssignmentDialog: React.FC<LicenseAssignmentDialogProps> = ({
  license,
  onAssign,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [formData, setFormData] = useState<AssignmentFormData>({
    employeeId: '',
    purpose: '',
    startDate: new Date().toISOString().split('T')[0], // Today's date
    endDate: '',
  });
  const [loading, setLoading] = useState(false);
  const [employeesLoading, setEmployeesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      setEmployeesLoading(true);
      const response = await apiClient.get('/employees/?status=ACTIVE');
      setEmployees(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setEmployeesLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
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

    if (!formData.employeeId) {
      errors.employeeId = ['割当先社員を選択してください'];
    }

    if (!formData.purpose.trim()) {
      errors.purpose = ['使用目的は必須です'];
    }

    if (!formData.startDate) {
      errors.startDate = ['利用開始日は必須です'];
    }

    // Validate dates
    if (formData.startDate && formData.endDate) {
      const startDate = new Date(formData.startDate);
      const endDate = new Date(formData.endDate);
      
      if (endDate <= startDate) {
        errors.endDate = ['利用終了日は利用開始日より後の日付を設定してください'];
      }
    }

    // Validate against license expiry
    if (formData.startDate) {
      const startDate = new Date(formData.startDate);
      const licenseExpiry = new Date(license.expiryDate);
      
      if (startDate >= licenseExpiry) {
        errors.startDate = ['利用開始日はライセンス有効期限より前の日付を設定してください'];
      }
    }

    if (formData.endDate) {
      const endDate = new Date(formData.endDate);
      const licenseExpiry = new Date(license.expiryDate);
      
      if (endDate > licenseExpiry) {
        errors.endDate = ['利用終了日はライセンス有効期限以内に設定してください'];
      }
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
        licenseId: license.id,
        employeeId: formData.employeeId,
        purpose: formData.purpose,
        startDate: formData.startDate,
        endDate: formData.endDate || undefined,
      };

      await apiClient.post(`/licenses/${license.id}/assign/`, submitData);
      onAssign();
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

  const getPricingModelLabel = (model: string) => {
    switch (model) {
      case 'MONTHLY': return '月額';
      case 'YEARLY': return '年額';
      case 'PERPETUAL': return '買い切り';
      default: return model;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mt-2">
              ライセンス割当
            </h3>
            
            {/* License Info */}
            <div className="mt-4 p-3 bg-gray-50 rounded-md text-left">
              <div className="text-sm font-medium text-gray-900">
                {license.softwareName}
              </div>
              <div className="text-sm text-gray-600">
                {license.licenseType} • {getPricingModelLabel(license.pricingModel)}
              </div>
              <div className="text-sm text-gray-600">
                利用可能: {license.availableCount} / {license.totalCount}
              </div>
              <div className="text-sm text-gray-600">
                有効期限: {formatDate(license.expiryDate)}
              </div>
              <div className="text-sm text-gray-600">
                単価: {formatCurrency(license.unitPrice)}
              </div>
            </div>
          </div>

          {/* Form */}
          {employeesLoading ? (
            <LoadingSpinner />
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <ErrorMessage message={error} />}

              {/* Employee Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  割当先社員 <span className="text-red-500">*</span>
                </label>
                <select
                  name="employeeId"
                  value={formData.employeeId}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.employeeId ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">社員を選択してください</option>
                  {employees.map(employee => (
                    <option key={employee.id} value={employee.id}>
                      {employee.name} ({employee.employeeId}) - {employee.department}
                    </option>
                  ))}
                </select>
                {fieldErrors.employeeId && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.employeeId[0]}</p>
                )}
              </div>

              {/* Purpose */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  使用目的 <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="purpose"
                  value={formData.purpose}
                  onChange={handleInputChange}
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.purpose ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="例: 開発業務用、デザイン作業用、営業資料作成用など"
                />
                {fieldErrors.purpose && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.purpose[0]}</p>
                )}
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  利用開始日 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="startDate"
                  value={formData.startDate}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.startDate ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {fieldErrors.startDate && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.startDate[0]}</p>
                )}
              </div>

              {/* End Date (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  利用終了日 (任意)
                </label>
                <input
                  type="date"
                  name="endDate"
                  value={formData.endDate}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.endDate ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {fieldErrors.endDate && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.endDate[0]}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  利用終了日を設定しない場合はライセンス有効期限まで利用可能です
                </p>
              </div>

              {/* Cost Information */}
              {license.pricingModel !== 'PERPETUAL' && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        <strong>コスト情報:</strong> このライセンスの{getPricingModelLabel(license.pricingModel)}料金は {formatCurrency(license.unitPrice)} です。
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4">
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
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 flex items-center"
                >
                  {loading && <LoadingSpinner size="sm" className="mr-2" />}
                  割当実行
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default LicenseAssignmentDialog;