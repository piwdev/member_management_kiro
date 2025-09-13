import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { License } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface LicenseFormProps {
  license?: License;
  onSave: (license: License) => void;
  onCancel: () => void;
}

interface LicenseFormData {
  softwareName: string;
  licenseType: string;
  totalCount: number;
  expiryDate: string;
  licenseKey: string;
  pricingModel: 'MONTHLY' | 'YEARLY' | 'PERPETUAL';
  unitPrice: number;
}

const LicenseForm: React.FC<LicenseFormProps> = ({
  license,
  onSave,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<LicenseFormData>({
    softwareName: '',
    licenseType: '',
    totalCount: 1,
    expiryDate: '',
    licenseKey: '',
    pricingModel: 'YEARLY',
    unitPrice: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const isEditing = !!license;

  useEffect(() => {
    if (license) {
      setFormData({
        softwareName: license.softwareName,
        licenseType: license.licenseType,
        totalCount: license.totalCount,
        expiryDate: license.expiryDate.split('T')[0], // Convert to YYYY-MM-DD format
        licenseKey: license.licenseKey || '',
        pricingModel: license.pricingModel,
        unitPrice: license.unitPrice,
      });
    }
  }, [license]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    if (type === 'number') {
      processedValue = value === '' ? 0 : Number(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue,
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

    if (!formData.softwareName.trim()) {
      errors.softwareName = ['ソフトウェア名は必須です'];
    }

    if (!formData.licenseType.trim()) {
      errors.licenseType = ['ライセンス種別は必須です'];
    }

    if (formData.totalCount <= 0) {
      errors.totalCount = ['購入数は1以上である必要があります'];
    }

    if (!formData.expiryDate) {
      errors.expiryDate = ['有効期限は必須です'];
    } else {
      const expiryDate = new Date(formData.expiryDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (expiryDate <= today) {
        errors.expiryDate = ['有効期限は明日以降の日付を設定してください'];
      }
    }

    if (formData.unitPrice < 0) {
      errors.unitPrice = ['単価は0以上である必要があります'];
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
        expiryDate: formData.expiryDate, // Keep as YYYY-MM-DD format for API
        licenseKey: formData.licenseKey || undefined, // Convert empty string to undefined
      };

      let response;
      if (isEditing) {
        response = await apiClient.put(`/licenses/${license.id}/`, submitData);
      } else {
        response = await apiClient.post('/licenses/', submitData);
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

  const getPricingModelLabel = (model: string) => {
    switch (model) {
      case 'MONTHLY': return '月額';
      case 'YEARLY': return '年額';
      case 'PERPETUAL': return '買い切り';
      default: return model;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount);
  };

  const calculateTotalCost = (): number => {
    switch (formData.pricingModel) {
      case 'MONTHLY':
        return formData.totalCount * formData.unitPrice * 12; // Annual cost
      case 'YEARLY':
        return formData.totalCount * formData.unitPrice;
      case 'PERPETUAL':
        return formData.totalCount * formData.unitPrice;
      default:
        return 0;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {isEditing ? 'ライセンス情報編集' : '新規ライセンス登録'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {error && <ErrorMessage message={error} />}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Software Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.softwareName')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="softwareName"
                value={formData.softwareName}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.softwareName ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: Microsoft Office 365, Adobe Creative Suite"
              />
              {fieldErrors.softwareName && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.softwareName[0]}</p>
              )}
            </div>

            {/* License Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.licenseType')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="licenseType"
                value={formData.licenseType}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.licenseType ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: Business Premium, Enterprise"
              />
              {fieldErrors.licenseType && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.licenseType[0]}</p>
              )}
            </div>

            {/* Total Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.totalCount')} <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                name="totalCount"
                value={formData.totalCount}
                onChange={handleInputChange}
                min="1"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.totalCount ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {fieldErrors.totalCount && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.totalCount[0]}</p>
              )}
            </div>

            {/* Pricing Model */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.pricingModel')} <span className="text-red-500">*</span>
              </label>
              <select
                name="pricingModel"
                value={formData.pricingModel}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.pricingModel ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="MONTHLY">{getPricingModelLabel('MONTHLY')}</option>
                <option value="YEARLY">{getPricingModelLabel('YEARLY')}</option>
                <option value="PERPETUAL">{getPricingModelLabel('PERPETUAL')}</option>
              </select>
              {fieldErrors.pricingModel && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.pricingModel[0]}</p>
              )}
            </div>

            {/* Unit Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.unitPrice')} <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                name="unitPrice"
                value={formData.unitPrice}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.unitPrice ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="0"
              />
              {fieldErrors.unitPrice && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.unitPrice[0]}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {formData.pricingModel === 'MONTHLY' ? '月額単価' : 
                 formData.pricingModel === 'YEARLY' ? '年額単価' : '買い切り単価'}
              </p>
            </div>

            {/* Expiry Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('licenses.expiryDate')} <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="expiryDate"
                value={formData.expiryDate}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.expiryDate ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {fieldErrors.expiryDate && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.expiryDate[0]}</p>
              )}
            </div>

            {/* License Key */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ライセンスキー (任意)
              </label>
              <textarea
                name="licenseKey"
                value={formData.licenseKey}
                onChange={handleInputChange}
                rows={3}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.licenseKey ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="ライセンスキーまたはアクティベーション情報"
              />
              {fieldErrors.licenseKey && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.licenseKey[0]}</p>
              )}
            </div>
          </div>

          {/* Cost Summary */}
          {formData.unitPrice > 0 && formData.totalCount > 0 && (
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="text-sm font-medium text-blue-900 mb-2">コスト概算</h3>
              <div className="space-y-1 text-sm text-blue-800">
                <div className="flex justify-between">
                  <span>単価:</span>
                  <span>{formatCurrency(formData.unitPrice)}</span>
                </div>
                <div className="flex justify-between">
                  <span>購入数:</span>
                  <span>{formData.totalCount} ライセンス</span>
                </div>
                <div className="flex justify-between font-medium border-t border-blue-200 pt-1">
                  <span>
                    {formData.pricingModel === 'MONTHLY' ? '年間総コスト:' : 
                     formData.pricingModel === 'YEARLY' ? '年間総コスト:' : '総コスト:'}
                  </span>
                  <span>{formatCurrency(calculateTotalCost())}</span>
                </div>
                {formData.pricingModel === 'MONTHLY' && (
                  <div className="flex justify-between text-xs">
                    <span>月額総コスト:</span>
                    <span>{formatCurrency(formData.totalCount * formData.unitPrice)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

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

export default LicenseForm;