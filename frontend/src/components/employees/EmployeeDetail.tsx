import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Employee, DeviceAssignment, LicenseAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface EmployeeDetailProps {
  employee: Employee;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

const EmployeeDetail: React.FC<EmployeeDetailProps> = ({
  employee,
  onEdit,
  onDelete,
  onClose,
}) => {
  const { t } = useTranslation();
  const [deviceAssignments, setDeviceAssignments] = useState<DeviceAssignment[]>([]);
  const [licenseAssignments, setLicenseAssignments] = useState<LicenseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssignments();
  }, [employee.id]);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const [deviceResponse, licenseResponse] = await Promise.all([
        apiClient.get(`/devices/assignments/?employee=${employee.id}`),
        apiClient.get(`/licenses/assignments/?employee=${employee.id}`),
      ]);

      setDeviceAssignments(deviceResponse.data.results || deviceResponse.data);
      setLicenseAssignments(licenseResponse.data.results || licenseResponse.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
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

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'INACTIVE':
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
      case 'EXPIRED':
      case 'REVOKED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const activeDeviceAssignments = deviceAssignments.filter(assignment => assignment.status === 'ACTIVE');
  const activeLicenseAssignments = licenseAssignments.filter(assignment => assignment.status === 'ACTIVE');

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-16 w-16">
              <div className="h-16 w-16 rounded-full bg-gray-300 flex items-center justify-center">
                <span className="text-xl font-medium text-gray-700">
                  {employee.name.charAt(0)}
                </span>
              </div>
            </div>
            <div className="ml-4">
              <h2 className="text-2xl font-bold text-gray-900">{employee.name}</h2>
              <p className="text-sm text-gray-500">{employee.email}</p>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(employee.status)}`}>
                {getStatusLabel(employee.status)}
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

        {/* Employee Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">基本情報</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('employees.employeeId')}</dt>
                <dd className="text-sm text-gray-900">{employee.employeeId}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('employees.department')}</dt>
                <dd className="text-sm text-gray-900">{employee.department}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('employees.position')}</dt>
                <dd className="text-sm text-gray-900">{employee.position}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('employees.location')}</dt>
                <dd className="text-sm text-gray-900">{getLocationLabel(employee.location)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('employees.hireDate')}</dt>
                <dd className="text-sm text-gray-900">{formatDate(employee.hireDate)}</dd>
              </div>
            </dl>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">リソース概要</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">割当端末数</dt>
                <dd className="text-sm text-gray-900">{activeDeviceAssignments.length} 台</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">割当ライセンス数</dt>
                <dd className="text-sm text-gray-900">{activeLicenseAssignments.length} 件</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">登録日</dt>
                <dd className="text-sm text-gray-900">{formatDate(employee.createdAt)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">最終更新</dt>
                <dd className="text-sm text-gray-900">{formatDate(employee.updatedAt)}</dd>
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
            {/* Device Assignments */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">割当端末</h3>
              {activeDeviceAssignments.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {activeDeviceAssignments.map((assignment) => (
                      <li key={assignment.id} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {assignment.device?.manufacturer} {assignment.device?.model}
                              </div>
                              <div className="text-sm text-gray-500">
                                {assignment.device?.serialNumber} • 割当日: {formatDate(assignment.assignedDate)}
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
                  割当されている端末はありません
                </div>
              )}
            </div>

            {/* License Assignments */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">割当ライセンス</h3>
              {activeLicenseAssignments.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {activeLicenseAssignments.map((assignment) => (
                      <li key={assignment.id} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
                                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {assignment.license?.softwareName}
                              </div>
                              <div className="text-sm text-gray-500">
                                割当日: {formatDate(assignment.assignedDate)} • 利用開始: {formatDate(assignment.startDate)}
                              </div>
                              <div className="text-sm text-gray-500">
                                目的: {assignment.purpose}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAssignmentStatusBadgeClass(assignment.status)}`}>
                              {assignment.status === 'ACTIVE' ? '使用中' : 
                               assignment.status === 'EXPIRED' ? '期限切れ' : 
                               assignment.status === 'REVOKED' ? '取り消し' : assignment.status}
                            </span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  割当されているライセンスはありません
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployeeDetail;