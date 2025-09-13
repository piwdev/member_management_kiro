import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Device, Employee } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface DeviceAssignmentDialogProps {
  device: Device;
  onAssign: () => void;
  onCancel: () => void;
}

interface AssignmentFormData {
  employeeId: string;
  purpose: string;
  returnDate?: string;
}

const DeviceAssignmentDialog: React.FC<DeviceAssignmentDialogProps> = ({
  device,
  onAssign,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [formData, setFormData] = useState<AssignmentFormData>({
    employeeId: '',
    purpose: '',
    returnDate: '',
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

    // Validate return date if provided
    if (formData.returnDate) {
      const returnDate = new Date(formData.returnDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (returnDate <= today) {
        errors.returnDate = ['返却予定日は明日以降の日付を設定してください'];
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
        deviceId: device.id,
        employeeId: formData.employeeId,
        purpose: formData.purpose,
        returnDate: formData.returnDate || undefined,
      };

      await apiClient.post(`/devices/${device.id}/assign/`, submitData);
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

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'LAPTOP': return 'ラップトップ';
      case 'DESKTOP': return 'デスクトップ';
      case 'TABLET': return 'タブレット';
      case 'SMARTPHONE': return 'スマートフォン';
      default: return type;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
              <svg
                className="h-6 w-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mt-2">
              端末貸出
            </h3>
            
            {/* Device Info */}
            <div className="mt-4 p-3 bg-gray-50 rounded-md text-left">
              <div className="text-sm font-medium text-gray-900">
                {device.manufacturer} {device.model}
              </div>
              <div className="text-sm text-gray-600">
                {getTypeLabel(device.type)} • {device.serialNumber}
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
                  placeholder="例: 開発業務用、営業活動用、テスト用など"
                />
                {fieldErrors.purpose && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.purpose[0]}</p>
                )}
              </div>

              {/* Return Date (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  返却予定日 (任意)
                </label>
                <input
                  type="date"
                  name="returnDate"
                  value={formData.returnDate}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.returnDate ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {fieldErrors.returnDate && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.returnDate[0]}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  返却予定日を設定しない場合は無期限貸出となります
                </p>
              </div>

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
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
                >
                  {loading && <LoadingSpinner size="sm" className="mr-2" />}
                  貸出実行
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeviceAssignmentDialog;