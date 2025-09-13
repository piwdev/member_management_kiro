import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Device } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface DeviceFormProps {
  device?: Device;
  onSave: (device: Device) => void;
  onCancel: () => void;
}

interface DeviceFormData {
  type: 'LAPTOP' | 'DESKTOP' | 'TABLET' | 'SMARTPHONE';
  manufacturer: string;
  model: string;
  serialNumber: string;
  purchaseDate: string;
  warrantyExpiry: string;
  status: 'AVAILABLE' | 'ASSIGNED' | 'MAINTENANCE' | 'DISPOSED';
}

const DeviceForm: React.FC<DeviceFormProps> = ({
  device,
  onSave,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<DeviceFormData>({
    type: 'LAPTOP',
    manufacturer: '',
    model: '',
    serialNumber: '',
    purchaseDate: '',
    warrantyExpiry: '',
    status: 'AVAILABLE',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const isEditing = !!device;

  useEffect(() => {
    if (device) {
      setFormData({
        type: device.type,
        manufacturer: device.manufacturer,
        model: device.model,
        serialNumber: device.serialNumber,
        purchaseDate: device.purchaseDate.split('T')[0], // Convert to YYYY-MM-DD format
        warrantyExpiry: device.warrantyExpiry.split('T')[0], // Convert to YYYY-MM-DD format
        status: device.status,
      });
    }
  }, [device]);

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

    if (!formData.manufacturer.trim()) {
      errors.manufacturer = ['メーカーは必須です'];
    }

    if (!formData.model.trim()) {
      errors.model = ['モデルは必須です'];
    }

    if (!formData.serialNumber.trim()) {
      errors.serialNumber = ['シリアル番号は必須です'];
    }

    if (!formData.purchaseDate) {
      errors.purchaseDate = ['購入日は必須です'];
    }

    if (!formData.warrantyExpiry) {
      errors.warrantyExpiry = ['保証期限は必須です'];
    }

    // Validate that warranty expiry is after purchase date
    if (formData.purchaseDate && formData.warrantyExpiry) {
      const purchaseDate = new Date(formData.purchaseDate);
      const warrantyDate = new Date(formData.warrantyExpiry);
      if (warrantyDate <= purchaseDate) {
        errors.warrantyExpiry = ['保証期限は購入日より後の日付を設定してください'];
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
        ...formData,
        purchaseDate: formData.purchaseDate, // Keep as YYYY-MM-DD format for API
        warrantyExpiry: formData.warrantyExpiry, // Keep as YYYY-MM-DD format for API
      };

      let response;
      if (isEditing) {
        response = await apiClient.put(`/devices/${device.id}/`, submitData);
      } else {
        response = await apiClient.post('/devices/', submitData);
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

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'LAPTOP': return 'ラップトップ';
      case 'DESKTOP': return 'デスクトップ';
      case 'TABLET': return 'タブレット';
      case 'SMARTPHONE': return 'スマートフォン';
      default: return type;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'AVAILABLE': return '利用可能';
      case 'ASSIGNED': return '貸出中';
      case 'MAINTENANCE': return '修理中';
      case 'DISPOSED': return '廃棄';
      default: return status;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {isEditing ? '端末情報編集' : '新規端末登録'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {error && <ErrorMessage message={error} />}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Device Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.type')} <span className="text-red-500">*</span>
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.type ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="LAPTOP">{getTypeLabel('LAPTOP')}</option>
                <option value="DESKTOP">{getTypeLabel('DESKTOP')}</option>
                <option value="TABLET">{getTypeLabel('TABLET')}</option>
                <option value="SMARTPHONE">{getTypeLabel('SMARTPHONE')}</option>
              </select>
              {fieldErrors.type && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.type[0]}</p>
              )}
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.status')} <span className="text-red-500">*</span>
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.status ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="AVAILABLE">{getStatusLabel('AVAILABLE')}</option>
                <option value="ASSIGNED">{getStatusLabel('ASSIGNED')}</option>
                <option value="MAINTENANCE">{getStatusLabel('MAINTENANCE')}</option>
                <option value="DISPOSED">{getStatusLabel('DISPOSED')}</option>
              </select>
              {fieldErrors.status && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.status[0]}</p>
              )}
            </div>

            {/* Manufacturer */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.manufacturer')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="manufacturer"
                value={formData.manufacturer}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.manufacturer ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: Apple, Dell, Lenovo"
              />
              {fieldErrors.manufacturer && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.manufacturer[0]}</p>
              )}
            </div>

            {/* Model */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.model')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="model"
                value={formData.model}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.model ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例: MacBook Pro 14-inch, ThinkPad X1"
              />
              {fieldErrors.model && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.model[0]}</p>
              )}
            </div>

            {/* Serial Number */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.serialNumber')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="serialNumber"
                value={formData.serialNumber}
                onChange={handleInputChange}
                disabled={isEditing} // Serial number should not be editable
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.serialNumber ? 'border-red-500' : 'border-gray-300'
                } ${isEditing ? 'bg-gray-100' : ''}`}
                placeholder="例: ABC123456789"
              />
              {fieldErrors.serialNumber && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.serialNumber[0]}</p>
              )}
            </div>

            {/* Purchase Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.purchaseDate')} <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="purchaseDate"
                value={formData.purchaseDate}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.purchaseDate ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {fieldErrors.purchaseDate && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.purchaseDate[0]}</p>
              )}
            </div>

            {/* Warranty Expiry */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('devices.warrantyExpiry')} <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="warrantyExpiry"
                value={formData.warrantyExpiry}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  fieldErrors.warrantyExpiry ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {fieldErrors.warrantyExpiry && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.warrantyExpiry[0]}</p>
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

export default DeviceForm;