import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../lib/api';
import { DeviceAssignment, LicenseAssignment } from '../../types';
import { useToast } from '../common/ToastContainer';

interface ReturnRequestFormProps {
  deviceAssignments: DeviceAssignment[];
  licenseAssignments: LicenseAssignment[];
  onSuccess: () => void;
  onCancel: () => void;
}

interface ReturnFormData {
  resourceType: 'device' | 'license';
  resourceId: string;
  returnDate: string;
  returnReason: string;
}

const ReturnRequestForm: React.FC<ReturnRequestFormProps> = ({
  deviceAssignments,
  licenseAssignments,
  onSuccess,
  onCancel,
}) => {
  const { t } = useTranslation();
  const { showSuccess, showError } = useToast();
  const [formData, setFormData] = useState<ReturnFormData>({
    resourceType: 'device',
    resourceId: '',
    returnDate: '',
    returnReason: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const submitMutation = useMutation({
    mutationFn: async (data: ReturnFormData) => {
      const endpoint = data.resourceType === 'device' 
        ? `/device-assignments/${data.resourceId}/return-request/`
        : `/license-assignments/${data.resourceId}/return-request/`;
      
      const response = await apiClient.post(endpoint, {
        returnDate: data.returnDate,
        returnReason: data.returnReason,
      });
      return response.data;
    },
    onSuccess: () => {
      showSuccess(
        '返却申請が送信されました',
        '申請内容を確認後、返却処理を行います。'
      );
      onSuccess();
    },
    onError: (error: any) => {
      if (error.response?.data?.details) {
        setErrors(error.response.data.details);
      } else {
        showError(
          '返却申請の送信に失敗しました',
          'しばらく時間をおいて再度お試しください。'
        );
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Record<string, string> = {};
    
    if (!formData.resourceId) {
      newErrors.resourceId = t('employeeDashboard.validation.resourceRequired');
    }
    
    if (!formData.returnDate) {
      newErrors.returnDate = t('employeeDashboard.validation.returnDateRequired');
    }
    
    if (!formData.returnReason.trim()) {
      newErrors.returnReason = t('employeeDashboard.validation.returnReasonRequired');
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    submitMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof ReturnFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleResourceTypeChange = (type: 'device' | 'license') => {
    setFormData(prev => ({
      ...prev,
      resourceType: type,
      resourceId: '', // Reset resource selection when type changes
    }));
    if (errors.resourceId) {
      setErrors(prev => ({ ...prev, resourceId: '' }));
    }
  };

  const getAvailableResources = () => {
    if (formData.resourceType === 'device') {
      return deviceAssignments.filter(assignment => assignment.status === 'ACTIVE');
    } else {
      return licenseAssignments.filter(assignment => assignment.status === 'ACTIVE');
    }
  };

  const getResourceDisplayName = (resource: DeviceAssignment | LicenseAssignment) => {
    if (formData.resourceType === 'device') {
      const deviceAssignment = resource as DeviceAssignment;
      return `${deviceAssignment.device?.manufacturer} ${deviceAssignment.device?.model} (${deviceAssignment.device?.serialNumber})`;
    } else {
      const licenseAssignment = resource as LicenseAssignment;
      return `${licenseAssignment.license?.softwareName} (${licenseAssignment.license?.licenseType})`;
    }
  };

  const availableResources = getAvailableResources();

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {t('employeeDashboard.returnForm.title')}
            </h3>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {availableResources.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-2.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 009.586 13H7" />
              </svg>
              <p className="mt-2 text-sm text-gray-500">
                返却可能なリソースがありません
              </p>
              <button
                onClick={onCancel}
                className="mt-4 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                閉じる
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Resource Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  リソース種別
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="device"
                      checked={formData.resourceType === 'device'}
                      onChange={(e) => handleResourceTypeChange(e.target.value as 'device' | 'license')}
                      className="mr-2"
                    />
                    端末 ({deviceAssignments.filter(a => a.status === 'ACTIVE').length}件)
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="license"
                      checked={formData.resourceType === 'license'}
                      onChange={(e) => handleResourceTypeChange(e.target.value as 'device' | 'license')}
                      className="mr-2"
                    />
                    ライセンス ({licenseAssignments.filter(a => a.status === 'ACTIVE').length}件)
                  </label>
                </div>
              </div>

              {/* Resource Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.returnForm.selectResource')} *
                </label>
                <select
                  value={formData.resourceId}
                  onChange={(e) => handleInputChange('resourceId', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.resourceId ? 'border-red-300' : 'border-gray-300'
                  }`}
                >
                  <option value="">選択してください</option>
                  {availableResources.map((resource) => (
                    <option key={resource.id} value={resource.id}>
                      {getResourceDisplayName(resource)}
                    </option>
                  ))}
                </select>
                {errors.resourceId && (
                  <p className="mt-1 text-sm text-red-600">{errors.resourceId}</p>
                )}
              </div>

              {/* Return Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.returnForm.returnDate')} *
                </label>
                <input
                  type="date"
                  value={formData.returnDate}
                  onChange={(e) => handleInputChange('returnDate', e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.returnDate ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {errors.returnDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.returnDate}</p>
                )}
              </div>

              {/* Return Reason */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.returnForm.returnReason')} *
                </label>
                <textarea
                  value={formData.returnReason}
                  onChange={(e) => handleInputChange('returnReason', e.target.value)}
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.returnReason ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder={t('employeeDashboard.returnForm.returnReasonPlaceholder')}
                />
                {errors.returnReason && (
                  <p className="mt-1 text-sm text-red-600">{errors.returnReason}</p>
                )}
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {t('employeeDashboard.returnForm.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={submitMutation.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  {submitMutation.isPending ? (
                    <div className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      送信中...
                    </div>
                  ) : (
                    t('employeeDashboard.returnForm.submit')
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReturnRequestForm;