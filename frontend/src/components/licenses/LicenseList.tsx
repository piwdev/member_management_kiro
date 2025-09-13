import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { License, LicenseAssignment } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface LicenseListProps {
  onLicenseSelect?: (license: License) => void;
  onLicenseEdit?: (license: License) => void;
  onLicenseDelete?: (license: License) => void;
  onLicenseAssign?: (license: License) => void;
}

const LicenseList: React.FC<LicenseListProps> = ({
  onLicenseSelect,
  onLicenseEdit,
  onLicenseDelete,
  onLicenseAssign,
}) => {
  const { t } = useTranslation();
  const [licenses, setLicenses] = useState<License[]>([]);
  const [assignments, setAssignments] = useState<LicenseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [pricingModelFilter, setPricingModelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchLicenses();
    fetchAssignments();
  }, []);

  const fetchLicenses = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/licenses/');
      setLicenses(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignments = async () => {
    try {
      const response = await apiClient.get('/licenses/assignments/');
      setAssignments(response.data.results || response.data);
    } catch (err: any) {
      console.error('Failed to fetch assignments:', err);
    }
  };

  const getActiveAssignments = (licenseId: string): LicenseAssignment[] => {
    return assignments.filter(assignment => 
      assignment.licenseId === licenseId && assignment.status === 'ACTIVE'
    );
  };

  const filteredLicenses = licenses.filter(license => {
    const matchesSearch = license.softwareName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         license.licenseType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPricingModel = !pricingModelFilter || license.pricingModel === pricingModelFilter;
    
    // Status filter based on availability
    let matchesStatus = true;
    if (statusFilter === 'AVAILABLE') {
      matchesStatus = license.availableCount > 0;
    } else if (statusFilter === 'FULL') {
      matchesStatus = license.availableCount === 0;
    } else if (statusFilter === 'EXPIRING') {
      const expiryDate = new Date(license.expiryDate);
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
      matchesStatus = expiryDate <= thirtyDaysFromNow;
    }

    return matchesSearch && matchesPricingModel && matchesStatus;
  });

  const getPricingModelLabel = (model: string) => {
    switch (model) {
      case 'MONTHLY': return '月額';
      case 'YEARLY': return '年額';
      case 'PERPETUAL': return '買い切り';
      default: return model;
    }
  };

  const getUsagePercentage = (license: License): number => {
    const usedCount = license.totalCount - license.availableCount;
    return Math.round((usedCount / license.totalCount) * 100);
  };

  const getUsageBarColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const isExpiringSoon = (expiryDate: string): boolean => {
    const expiry = new Date(expiryDate);
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    return expiry <= thirtyDaysFromNow;
  };

  const isExpired = (expiryDate: string): boolean => {
    const expiry = new Date(expiryDate);
    const today = new Date();
    return expiry < today;
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

  const calculateMonthlyCost = (license: License): number => {
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

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={fetchLicenses} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">{t('licenses.title')}</h1>
        <button
          onClick={() => window.location.href = '/licenses/new'}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          {t('common.add')} {t('licenses.title')}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('common.search')}
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="ソフトウェア名、ライセンス種別"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Pricing Model Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('licenses.pricingModel')}
            </label>
            <select
              value={pricingModelFilter}
              onChange={(e) => setPricingModelFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              <option value="MONTHLY">月額</option>
              <option value="YEARLY">年額</option>
              <option value="PERPETUAL">買い切り</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ステータス
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              <option value="AVAILABLE">利用可能</option>
              <option value="FULL">満杯</option>
              <option value="EXPIRING">期限切れ間近</option>
            </select>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {filteredLicenses.length} 件のライセンスが見つかりました
          </span>
          <button
            onClick={() => {
              fetchLicenses();
              fetchAssignments();
            }}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* License Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredLicenses.map((license) => {
          const usagePercentage = getUsagePercentage(license);
          const activeAssignments = getActiveAssignments(license.id);
          const monthlyCost = calculateMonthlyCost(license);
          const expired = isExpired(license.expiryDate);
          const expiringSoon = isExpiringSoon(license.expiryDate);

          return (
            <div
              key={license.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onLicenseSelect?.(license)}
            >
              <div className="p-6">
                {/* License Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="ml-3 flex-1">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {license.softwareName}
                      </h3>
                      <p className="text-sm text-gray-500">{license.licenseType}</p>
                    </div>
                  </div>
                  {(expired || expiringSoon) && (
                    <div className="flex-shrink-0">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        expired ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {expired ? '期限切れ' : '期限間近'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Usage Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>利用状況</span>
                    <span>{license.totalCount - license.availableCount} / {license.totalCount}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getUsageBarColor(usagePercentage)}`}
                      style={{ width: `${usagePercentage}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    利用率: {usagePercentage}%
                  </div>
                </div>

                {/* License Details */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">課金体系:</span>
                    <span className="text-gray-900">{getPricingModelLabel(license.pricingModel)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">単価:</span>
                    <span className="text-gray-900">{formatCurrency(license.unitPrice)}</span>
                  </div>
                  {monthlyCost > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">月額コスト:</span>
                      <span className="text-gray-900 font-medium">{formatCurrency(monthlyCost)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">有効期限:</span>
                    <span className={`${expired ? 'text-red-600 font-medium' : expiringSoon ? 'text-yellow-600 font-medium' : 'text-gray-900'}`}>
                      {formatDate(license.expiryDate)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onLicenseEdit?.(license);
                    }}
                    className="flex-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md font-medium"
                  >
                    {t('common.edit')}
                  </button>
                  
                  {license.availableCount > 0 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onLicenseAssign?.(license);
                      }}
                      className="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md font-medium"
                    >
                      割当
                    </button>
                  )}
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onLicenseDelete?.(license);
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

      {filteredLicenses.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            {searchTerm || pricingModelFilter || statusFilter
              ? '検索条件に一致するライセンスが見つかりません'
              : 'ライセンスが登録されていません'}
          </div>
        </div>
      )}
    </div>
  );
};

export default LicenseList;