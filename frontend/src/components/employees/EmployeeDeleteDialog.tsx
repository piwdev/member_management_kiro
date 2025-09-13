import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Employee } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface EmployeeDeleteDialogProps {
  employee: Employee;
  onConfirm: () => void;
  onCancel: () => void;
}

const EmployeeDeleteDialog: React.FC<EmployeeDeleteDialogProps> = ({
  employee,
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
      
      await apiClient.delete(`/employees/${employee.id}/`);
      onConfirm();
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

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
              社員の削除確認
            </h3>
            
            {/* Content */}
            <div className="mt-4 text-sm text-gray-500">
              <p className="mb-3">
                以下の社員を削除しますか？この操作は取り消せません。
              </p>
              
              <div className="bg-gray-50 p-3 rounded-md text-left">
                <div className="font-medium text-gray-900">{employee.name}</div>
                <div className="text-gray-600">社員ID: {employee.employeeId}</div>
                <div className="text-gray-600">部署: {employee.department}</div>
                <div className="text-gray-600">役職: {employee.position}</div>
              </div>

              <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      <strong>注意:</strong> この社員に割り当てられているリソース（端末・ライセンス）も同時に回収対象となります。
                    </p>
                  </div>
                </div>
              </div>
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
              <button
                type="button"
                onClick={handleDelete}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 flex items-center"
              >
                {loading && <LoadingSpinner size="sm" className="mr-2" />}
                削除する
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeDeleteDialog;