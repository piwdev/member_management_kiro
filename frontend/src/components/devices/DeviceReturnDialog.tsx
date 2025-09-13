import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Device, DeviceAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface DeviceReturnDialogProps {
  device: Device;
  onReturn: () => void;
  onCancel: () => void;
}

const DeviceReturnDialog: React.FC<DeviceReturnDialogProps> = ({
  device,
  onReturn,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [assignment, setAssignment] = useState<DeviceAssignment | null>(null);
  const [loading, setLoading] = useState(false);
  const [assignmentLoading, setAssignmentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchActiveAssignment();
  }, [device.id]);

  const fetchActiveAssignment = async () => {
    try {
      setAssignmentLoading(true);
      const response = await apiClient.get(`/devices/${device.id}/assignments/?status=ACTIVE`);
      const assignments = response.data.results || response.data;
      if (assignments.length > 0) {
        setAssignment(assignments[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setAssignmentLoading(false);
    }
  };

  const handleReturn = async () => {
    if (!assignment) return;

    try {
      setLoading(true);
      setError(null);

      await apiClient.post(`/devices/${device.id}/return/`, {
        assignmentId: assignment.id,
      });
      
      onReturn();
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const calculateDaysUsed = (assignedDate: string): number => {
    const assigned = new Date(assignedDate);
    const today = new Date();
    const diffTime = Math.abs(today.getTime() - assigned.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
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
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mt-2">
              端末返却
            </h3>
          </div>

          {assignmentLoading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchActiveAssignment} />
          ) : assignment ? (
            <div className="space-y-4">
              {/* Device Info */}
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="text-sm font-medium text-gray-900 mb-2">端末情報</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>端末:</span>
                    <span className="font-medium text-gray-900">
                      {device.manufacturer} {device.model}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>種別:</span>
                    <span>{getTypeLabel(device.type)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>シリアル番号:</span>
                    <span className="font-mono text-xs">{device.serialNumber}</span>
                  </div>
                </div>
              </div>

              {/* Assignment Info */}
              <div className="p-4 bg-blue-50 rounded-md">
                <h4 className="text-sm font-medium text-gray-900 mb-2">貸出情報</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>割当先:</span>
                    <span className="font-medium text-gray-900">
                      {assignment.employee?.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>社員ID:</span>
                    <span>{assignment.employee?.employeeId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>部署:</span>
                    <span>{assignment.employee?.department}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>貸出日:</span>
                    <span>{formatDate(assignment.assignedDate)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>使用期間:</span>
                    <span>{calculateDaysUsed(assignment.assignedDate)} 日間</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-xs text-gray-500">使用目的:</span>
                    <p className="text-sm text-gray-900 mt-1">{assignment.purpose}</p>
                  </div>
                </div>
              </div>

              {/* Confirmation Message */}
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      この端末を返却処理しますか？返却後は端末ステータスが「利用可能」に変更され、他の社員に貸出可能になります。
                    </p>
                  </div>
                </div>
              </div>

              {error && <ErrorMessage message={error} />}

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
                  type="button"
                  onClick={handleReturn}
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 flex items-center"
                >
                  {loading && <LoadingSpinner size="sm" className="mr-2" />}
                  返却処理
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-gray-500">アクティブな貸出情報が見つかりません</p>
              <button
                onClick={onCancel}
                className="mt-4 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                閉じる
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeviceReturnDialog;