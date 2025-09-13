import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Device, DeviceAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface DeviceListProps {
  onDeviceSelect?: (device: Device) => void;
  onDeviceEdit?: (device: Device) => void;
  onDeviceDelete?: (device: Device) => void;
  onDeviceAssign?: (device: Device) => void;
  onDeviceReturn?: (device: Device) => void;
}

const DeviceList: React.FC<DeviceListProps> = ({
  onDeviceSelect,
  onDeviceEdit,
  onDeviceDelete,
  onDeviceAssign,
  onDeviceReturn,
}) => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [assignments, setAssignments] = useState<DeviceAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [manufacturerFilter, setManufacturerFilter] = useState('');

  // Get unique values for filters
  const deviceTypes = ['LAPTOP', 'DESKTOP', 'TABLET', 'SMARTPHONE'];
  const manufacturers = Array.from(new Set(devices.map(device => device.manufacturer)));

  useEffect(() => {
    fetchDevices();
    fetchAssignments();
  }, []);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/devices/');
      setDevices(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignments = async () => {
    try {
      const response = await apiClient.get('/devices/assignments/');
      setAssignments(response.data.results || response.data);
    } catch (err: any) {
      console.error('Failed to fetch assignments:', err);
    }
  };

  const getActiveAssignment = (deviceId: string): DeviceAssignment | undefined => {
    return assignments.find(assignment => 
      assignment.deviceId === deviceId && assignment.status === 'ACTIVE'
    );
  };

  const filteredDevices = devices.filter(device => {
    const matchesSearch = device.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         device.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         device.serialNumber.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = !typeFilter || device.type === typeFilter;
    const matchesStatus = !statusFilter || device.status === statusFilter;
    const matchesManufacturer = !manufacturerFilter || device.manufacturer === manufacturerFilter;

    return matchesSearch && matchesType && matchesStatus && matchesManufacturer;
  });

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

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return 'bg-green-100 text-green-800';
      case 'ASSIGNED':
        return 'bg-blue-100 text-blue-800';
      case 'MAINTENANCE':
        return 'bg-yellow-100 text-yellow-800';
      case 'DISPOSED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'LAPTOP':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'DESKTOP':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'TABLET':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'SMARTPHONE':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={fetchDevices} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">{t('devices.title')}</h1>
        <button
          onClick={() => window.location.href = '/devices/new'}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          {t('common.add')} {t('devices.title')}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('common.search')}
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="メーカー、モデル、シリアル番号"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('devices.type')}
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {deviceTypes.map(type => (
                <option key={type} value={type}>{getTypeLabel(type)}</option>
              ))}
            </select>
          </div>

          {/* Manufacturer Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('devices.manufacturer')}
            </label>
            <select
              value={manufacturerFilter}
              onChange={(e) => setManufacturerFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {manufacturers.map(manufacturer => (
                <option key={manufacturer} value={manufacturer}>{manufacturer}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('devices.status')}
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              <option value="AVAILABLE">利用可能</option>
              <option value="ASSIGNED">貸出中</option>
              <option value="MAINTENANCE">修理中</option>
              <option value="DISPOSED">廃棄</option>
            </select>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {filteredDevices.length} 件の端末が見つかりました
          </span>
          <button
            onClick={() => {
              fetchDevices();
              fetchAssignments();
            }}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Device Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDevices.map((device) => {
          const activeAssignment = getActiveAssignment(device.id);
          return (
            <div
              key={device.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onDeviceSelect?.(device)}
            >
              <div className="p-6">
                {/* Device Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                      {getDeviceIcon(device.type)}
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-gray-900">
                        {device.manufacturer}
                      </h3>
                      <p className="text-sm text-gray-500">{device.model}</p>
                    </div>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(device.status)}`}>
                    {getStatusLabel(device.status)}
                  </span>
                </div>

                {/* Device Details */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">種別:</span>
                    <span className="text-gray-900">{getTypeLabel(device.type)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">シリアル番号:</span>
                    <span className="text-gray-900 font-mono text-xs">{device.serialNumber}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">購入日:</span>
                    <span className="text-gray-900">{formatDate(device.purchaseDate)}</span>
                  </div>
                  {activeAssignment && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">割当先:</span>
                      <span className="text-gray-900">{activeAssignment.employee?.name}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeviceEdit?.(device);
                    }}
                    className="flex-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md font-medium"
                  >
                    {t('common.edit')}
                  </button>
                  
                  {device.status === 'AVAILABLE' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeviceAssign?.(device);
                      }}
                      className="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md font-medium"
                    >
                      貸出
                    </button>
                  )}
                  
                  {device.status === 'ASSIGNED' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeviceReturn?.(device);
                      }}
                      className="flex-1 text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md font-medium"
                    >
                      返却
                    </button>
                  )}
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeviceDelete?.(device);
                    }}
                    className="text-xs text-red-600 hover:text-red-800 px-3 py-2 rounded-md font-medium"
                  >
                    {t('common.delete')}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredDevices.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            {searchTerm || typeFilter || statusFilter || manufacturerFilter
              ? '検索条件に一致する端末が見つかりません'
              : '端末が登録されていません'}
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceList;