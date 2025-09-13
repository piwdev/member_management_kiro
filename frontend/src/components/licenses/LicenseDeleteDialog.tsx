import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { License } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface LicenseDeleteDialogProps {
  license: License;
  onConfirm: () => void;
  onCancel: () => void;
}

const LicenseDeleteDialog: React.FC<LicenseDeleteDialogProps> = ({
  license,
  onConfirm,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    try {
      setLoading(true);
      setError(null);
      
      await apiClient.delete(`/licenses/${license.id}/`);
      onConfirm();
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const hasActiveAssignments = license.availableCount < license.totalCount;
  const canDelete = !hasActiveAssignments;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Icon */}
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>

          {/* Title */}
          <div className="mt-5 text-center">
            <h3 className="text-lg font-medium text-gray-900">
              ライセンスの削除確認
            </h3>
            
            {/* Content */}
            <div className="mt-4 text-sm text-gray-500">
              <p className="mb-3">
                以下のライセンスを削除しますか？この操作は取り消せません。
              </p>
              
              <div className="bg-gray-50 p-3 rounded-md text-left">
                <div className="font-medium text-gray-900">
                  {license.softwareName}
                </div>
                <div className="text-gray-600">種別: {license.licenseType}</div>
                <div className="text-gray-600">課金体系: {getPricingModelLabel(license.pricingModel)}</div>
                <div className="text-gray-600">購入数: {license.totalCount} ライセンス</div>
                <div className="text-gray-600">利用中: {license.totalCount - license.availableCount} ライセンス</div>
                <div className="text-gray-600">単価: {formatCurrency(license.unitPrice)}</div>
                <div className="text-gray-600">有効期限: {formatDate(license.expiryDate)}</div>
              </div>

              {!canDelete && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">
                        <strong>削除できません:</strong> このライセンスは現在 {license.totalCount - license.availableCount} 件が使用中です。削除する前にすべての割当を解除してください。
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {canDelete && (
                <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-700">
                        <strong>注意:</strong> このライセンスの割当履歴も同時に削除されます。
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4">
                <ErrorMessage message={error} />
              </div>
            )}

            {/* Actions */}
            <div className="mt-6 flex justify-center space-x-3">
              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
              {canDelete && (
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 flex items-center"
                >
                  {loading && <LoadingSpinner size="sm" className="mr-2" />}
                  削除する
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LicenseDeleteDialog;