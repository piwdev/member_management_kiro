import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { License, LicenseAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface LicenseDetailProps {
  license: License;
  onEdit: () => void;
  onDelete: () => void;
  onAssign: () => void;
  onClose: () => void;
}

const LicenseDetail: React.FC<LicenseDetailProps> = ({
  license,
  onEdit,
  onDelete,
  onAssign,
  onClose,
}) => {
  const { t } = useTranslation();
  const [assignments, setAssignments] = useState<LicenseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssignments();
  }, [license.id]);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/licenses/${license.id}/assignments/`);
      setAssignments(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeAssignment = async (assignmentId: string) => {
    try {
      await apiClient.delete(`/licenses/assignments/${assignmentId}/`);
      fetchAssignments(); // Refresh assignments
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
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

  const getAssignmentStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'EXPIRED':
        return 'bg-red-100 text-red-800';
      case 'REVOKED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAssignmentStatusLabel = (status: string) => {
    switch (status) {
      case 'ACTIVE': return '使用中';
      case 'EXPIRED': return '期限切れ';
      case 'REVOKED': return '取り消し';
      default: return status;
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

  const isExpired = (expiryDate: string): boolean => {
    const expiry = new Date(expiryDate);
    const today = new Date();
    return expiry < today;
  };

  const isExpiringSoon = (expiryDate: string): boolean => {
    const expiry = new Date(expiryDate);
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    return expiry <= thirtyDaysFromNow && expiry >= new Date();
  };

  const getUsagePercentage = (): number => {
    const usedCount = license.totalCount - license.availableCount;
    return Math.round((usedCount / license.totalCount) * 100);
  };

  const calculateMonthlyCost = (): number => {
    const usedCount = license.totalCount - license.availableCount;
    switch (license.pricingModel) {
      case 'MONTHLY':
        return usedCount * license.unitPrice;
      case 'YEARLY':
        return (usedCount * license.unitPrice) / 12;
      case 'PERPETUAL':
        return 0; // No recurring cost
      default:
        return 0;
    }
  };

  const calculateTotalCost = (): number => {
    switch (license.pricingModel) {
      case 'MONTHLY':
        return license.totalCount * license.unitPrice * 12; // Annual cost
      case 'YEARLY':
        return license.totalCount * license.unitPrice;
      case 'PERPETUAL':
        return license.totalCount * license.unitPrice;
      default:
        return 0;
    }
  };

  const activeAssignments = assignments.filter(assignment => assignment.status === 'ACTIVE');
  const inactiveAssignments = assignments.filter(assignment => assignment.status !== 'ACTIVE');

  const expired = isExpired(license.expiryDate);
  const expiringSoon = isExpiringSoon(license.expiryDate);

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-16 w-16 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
              <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {license.softwareName}
              </h2>
              <p className="text-sm text-gray-500">{license.licenseType}</p>
              <p className="text-sm text-gray-500">{getPricingModelLabel(license.pricingModel)}</p>
              {(expired || expiringSoon) && (
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full mt-1 ${
                  expired ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {expired ? '期限切れ' : '期限間近'}
                </span>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={onEdit}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              {t('common.edit')}
            </button>
            {license.availableCount > 0 && (
              <button
                onClick={onAssign}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                割当
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

        {/* License Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">基本情報</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('licenses.softwareName')}</dt>
                <dd className="text-sm text-gray-900">{license.softwareName}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('licenses.licenseType')}</dt>
                <dd className="text-sm text-gray-900">{license.licenseType}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('licenses.pricingModel')}</dt>
                <dd className="text-sm text-gray-900">{getPricingModelLabel(license.pricingModel)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('licenses.unitPrice')}</dt>
                <dd className="text-sm text-gray-900">{formatCurrency(license.unitPrice)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('licenses.expiryDate')}</dt>
                <dd className={`text-sm ${expired ? 'text-red-600 font-medium' : expiringSoon ? 'text-yellow-600 font-medium' : 'text-gray-900'}`}>
                  {formatDate(license.expiryDate)}
                  {expired && ' (期限切れ)'}
                  {expiringSoon && !expired && ' (期限間近)'}
                </dd>
              </div>
            </dl>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">利用状況</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">購入数</dt>
                <dd className="text-sm text-gray-900">{license.totalCount} ライセンス</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">利用中</dt>
                <dd className="text-sm text-gray-900">{license.totalCount - license.availableCount} ライセンス</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">利用可能</dt>
                <dd className="text-sm text-gray-900">{license.availableCount} ライセンス</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">利用率</dt>
                <dd className="text-sm text-gray-900">{getUsagePercentage()}%</dd>
              </div>
              {license.pricingModel !== 'PERPETUAL' && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">月額コスト</dt>
                  <dd className="text-sm text-gray-900 font-medium">{formatCurrency(calculateMonthlyCost())}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  {license.pricingModel === 'PERPETUAL' ? '総コスト' : '年間総コスト'}
                </dt>
                <dd className="text-sm text-gray-900 font-medium">{formatCurrency(calculateTotalCost())}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Usage Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>ライセンス利用状況</span>
            <span>{license.totalCount - license.availableCount} / {license.totalCount} 使用中</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${
                getUsagePercentage() >= 90 ? 'bg-red-500' : 
                getUsagePercentage() >= 70 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${getUsagePercentage()}%` }}
            ></div>
          </div>
        </div>

        {/* License Key */}
        {license.licenseKey && (
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">ライセンスキー</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm text-gray-900 whitespace-pre-wrap font-mono">
                {license.licenseKey}
              </pre>
            </div>
          </div>
        )}

        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchAssignments} />
        ) : (
          <div className="space-y-8">
            {/* Active Assignments */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">現在の割当 ({activeAssignments.length})</h3>
              {activeAssignments.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {activeAssignments.map((assignment) => (
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
                                利用開始: {formatDate(assignment.startDate)}
                                {assignment.endDate && ` → 終了予定: ${formatDate(assignment.endDate)}`}
                              </div>
                              <div className="text-sm text-gray-500">
                                目的: {assignment.purpose}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAssignmentStatusBadgeClass(assignment.status)}`}>
                              {getAssignmentStatusLabel(assignment.status)}
                            </span>
                            <button
                              onClick={() => handleRevokeAssignment(assignment.id)}
                              className="text-red-600 hover:text-red-800 text-xs font-medium"
                            >
                              取り消し
                            </button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  現在割当されているライセンスはありません
                </div>
              )}
            </div>

            {/* Assignment History */}
            {inactiveAssignments.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">割当履歴 ({inactiveAssignments.length})</h3>
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {inactiveAssignments.map((assignment) => (
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
                                利用期間: {formatDate(assignment.startDate)} → {assignment.endDate ? formatDate(assignment.endDate) : '未設定'}
                              </div>
                              <div className="text-sm text-gray-500">
                                目的: {assignment.purpose}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAssignmentStatusBadgeClass(assignment.status)}`}>
                              {getAssignmentStatusLabel(assignment.status)}
                            </span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LicenseDetail;