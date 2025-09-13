import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../lib/api';
import { useToast } from '../common/ToastContainer';

interface ResourceRequestFormProps {
  type: 'device' | 'license';
  onSuccess: () => void;
  onCancel: () => void;
}

interface RequestFormData {
  type: 'device' | 'license';
  deviceType?: string;
  softwareName?: string;
  purpose: string;
  startDate: string;
  endDate?: string;
  businessJustification: string;
}

const ResourceRequestForm: React.FC<ResourceRequestFormProps> = ({
  type,
  onSuccess,
  onCancel,
}) => {
  const { t } = useTranslation();
  const { showSuccess, showError } = useToast();
  const [formData, setFormData] = useState<RequestFormData>({
    type,
    deviceType: '',
    softwareName: '',
    purpose: '',
    startDate: '',
    endDate: '',
    businessJustification: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const deviceTypes = [
    { value: 'LAPTOP', label: 'ラップトップ' },
    { value: 'DESKTOP', label: 'デスクトップ' },
    { value: 'TABLET', label: 'タブレット' },
    { value: 'SMARTPHONE', label: 'スマートフォン' },
  ];

  const submitMutation = useMutation({
    mutationFn: async (data: RequestFormData) => {
      const response = await apiClient.post('/requests/', data);
      return response.data;
    },
    onSuccess: () => {
      showSuccess(
        '申請が送信されました',
        '申請内容を確認後、承認・却下の結果をお知らせします。'
      );
      onSuccess();
    },
    onError: (error: any) => {
      if (error.response?.data?.details) {
        setErrors(error.response.data.details);
      } else {
        showError(
          '申請の送信に失敗しました',
          'しばらく時間をおいて再度お試しください。'
        );
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Record<string, string> = {};
    
    if (type === 'device' && !formData.deviceType) {
      newErrors.deviceType = t('employeeDashboard.validation.deviceTypeRequired');
    }
    
    if (type === 'license' && !formData.softwareName) {
      newErrors.softwareName = t('employeeDashboard.validation.softwareNameRequired');
    }
    
    if (!formData.purpose.trim()) {
      newErrors.purpose = t('employeeDashboard.validation.purposeRequired');
    }
    
    if (!formData.startDate) {
      newErrors.startDate = t('employeeDashboard.validation.startDateRequired');
    }
    
    if (!formData.businessJustification.trim()) {
      newErrors.businessJustification = t('employeeDashboard.validation.businessJustificationRequired');
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    submitMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof RequestFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {type === 'device' 
                ? t('employeeDashboard.requestForm.deviceRequest')
                : t('employeeDashboard.requestForm.licenseRequest')
              }
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

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Device Type or Software Name */}
            {type === 'device' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.requestForm.deviceType')} *
                </label>
                <select
                  value={formData.deviceType || ''}
                  onChange={(e) => handleInputChange('deviceType', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.deviceType ? 'border-red-300' : 'border-gray-300'
                  }`}
                >
                  <option value="">選択してください</option>
                  {deviceTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                {errors.deviceType && (
                  <p className="mt-1 text-sm text-red-600">{errors.deviceType}</p>
                )}
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.requestForm.softwareName')} *
                </label>
                <input
                  type="text"
                  value={formData.softwareName || ''}
                  onChange={(e) => handleInputChange('softwareName', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.softwareName ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="例: Microsoft Office, Adobe Creative Suite"
                />
                {errors.softwareName && (
                  <p className="mt-1 text-sm text-red-600">{errors.softwareName}</p>
                )}
              </div>
            )}

            {/* Purpose */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employeeDashboard.requestForm.purpose')} *
              </label>
              <textarea
                value={formData.purpose}
                onChange={(e) => handleInputChange('purpose', e.target.value)}
                rows={3}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  errors.purpose ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder={t('employeeDashboard.requestForm.purposePlaceholder')}
              />
              {errors.purpose && (
                <p className="mt-1 text-sm text-red-600">{errors.purpose}</p>
              )}
            </div>

            {/* Usage Period */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.requestForm.startDate')} *
                </label>
                <input
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => handleInputChange('startDate', e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.startDate ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {errors.startDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.startDate}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employeeDashboard.requestForm.endDateOptional')}
                </label>
                <input
                  type="date"
                  value={formData.endDate || ''}
                  onChange={(e) => handleInputChange('endDate', e.target.value)}
                  min={formData.startDate || new Date().toISOString().split('T')[0]}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Business Justification */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employeeDashboard.requestForm.businessJustification')} *
              </label>
              <textarea
                value={formData.businessJustification}
                onChange={(e) => handleInputChange('businessJustification', e.target.value)}
                rows={4}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  errors.businessJustification ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder={t('employeeDashboard.requestForm.businessJustificationPlaceholder')}
              />
              {errors.businessJustification && (
                <p className="mt-1 text-sm text-red-600">{errors.businessJustification}</p>
              )}
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('employeeDashboard.requestForm.cancel')}
              </button>
              <button
                type="submit"
                disabled={submitMutation.isPending}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
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
                  t('employeeDashboard.requestForm.submit')
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResourceRequestForm;