import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Device, DeviceAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface DeviceDetailProps {
  device: Device;
  onEdit: () => void;
  onDelete: () => void;
  onAssign: () => void;
  onReturn: () => void;
  onClose: () => void;
}

const DeviceDetail: React.FC<DeviceDetailProps> = ({
  device,
  onEdit,
  onDelete,
  onAssign,
  onReturn,
  onClose,
}) => {
  const { t } = useTranslation();
  const [assignments, setAssignments] = useState<DeviceAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssignments();
  }, [device.id]);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/devices/${device.id}/assignments/`);
      setAssignments(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
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

  const getAssignmentStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'RETURNED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'LAPTOP':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'DESKTOP':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'TABLET':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'SMARTPHONE':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const isWarrantyExpired = () => {
    const warrantyDate = new Date(device.warrantyExpiry);
    const today = new Date();
    return warrantyDate < today;
  };

  const activeAssignment = assignments.find(assignment => assignment.status === 'ACTIVE');
  const assignmentHistory = assignments.filter(assignment => assignment.status === 'RETURNED');

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-16 w-16 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
              {getDeviceIcon(device.type)}
            </div>
            <div className="ml-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {device.manufacturer} {device.model}
              </h2>
              <p className="text-sm text-gray-500">{getTypeLabel(device.type)}</p>
              <p className="text-sm text-gray-500 font-mono">{device.serialNumber}</p>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(device.status)}`}>
                {getStatusLabel(device.status)}
              </span>
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={onEdit}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              {t('common.edit')}
            </button>
            {device.status === 'AVAILABLE' && (
              <button
                onClick={onAssign}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                貸出
              </button>
            )}
            {device.status === 'ASSIGNED' && (
              <button
                onClick={onReturn}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                返却
              </button>
            )}
            <button
              onClick={onDelete}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              {t('common.delete')}
            </button>
            <button
              onClick={onClose}
              className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
            >
              閉じる
            </button>
          </div>
        </div>

        {/* Device Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">基本情報</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.type')}</dt>
                <dd className="text-sm text-gray-900">{getTypeLabel(device.type)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.manufacturer')}</dt>
                <dd className="text-sm text-gray-900">{device.manufacturer}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.model')}</dt>
                <dd className="text-sm text-gray-900">{device.model}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.serialNumber')}</dt>
                <dd className="text-sm text-gray-900 font-mono">{device.serialNumber}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.purchaseDate')}</dt>
                <dd className="text-sm text-gray-900">{formatDate(device.purchaseDate)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('devices.warrantyExpiry')}</dt>
                <dd className={`text-sm ${isWarrantyExpired() ? 'text-red-600 font-medium' : 'text-gray-900'}`}>
                  {formatDate(device.warrantyExpiry)}
                  {isWarrantyExpired() && ' (期限切れ)'}
                </dd>
              </div>
            </dl>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">ステータス情報</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">現在のステータス</dt>
                <dd className="text-sm text-gray-900">{getStatusLabel(device.status)}</dd>
              </div>
              {activeAssignment && (
                <>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">現在の割当先</dt>
                    <dd className="text-sm text-gray-900">{activeAssignment.employee?.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">貸出日</dt>
                    <dd className="text-sm text-gray-900">{formatDate(activeAssignment.assignedDate)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">使用目的</dt>
                    <dd className="text-sm text-gray-900">{activeAssignment.purpose}</dd>
                  </div>
                </>
              )}
              <div>
                <dt className="text-sm font-medium text-gray-500">登録日</dt>
                <dd className="text-sm text-gray-900">{formatDate(device.createdAt)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">最終更新</dt>
                <dd className="text-sm text-gray-900">{formatDate(device.updatedAt)}</dd>
              </div>
            </dl>
          </div>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchAssignments} />
        ) : (
          <div className="space-y-8">
            {/* Assignment History */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">貸出履歴</h3>
              {assignments.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {assignments.map((assignment) => (
                      <li key={assignment.id} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <span className="text-sm font-medium text-gray-700">
                                  {assignment.employee?.name?.charAt(0)}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {assignment.employee?.name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {assignment.employee?.employeeId} • {assignment.employee?.department}
                              </div>
                              <div className="text-sm text-gray-500">
                                貸出: {formatDate(assignment.assignedDate)}
                                {assignment.returnDate && ` → 返却: ${formatDate(assignment.returnDate)}`}
                              </div>
                              <div className="text-sm text-gray-500">
                                目的: {assignment.purpose}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAssignmentStatusBadgeClass(assignment.status)}`}>
                              {assignment.status === 'ACTIVE' ? '使用中' : '返却済み'}
                            </span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  貸出履歴はありません
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DeviceDetail;