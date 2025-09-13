import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../lib/api';
import { LicenseAssignment } from '../../types';

interface ExpiringLicense extends LicenseAssignment {
  daysUntilExpiry: number;
}

const LicenseExpiryAlerts: React.FC = () => {
  const { t } = useTranslation();

  const { data: expiringLicenses = [], isLoading } = useQuery<ExpiringLicense[]>({
    queryKey: ['expiring-licenses'],
    queryFn: async () => {
      const response = await apiClient.get('/dashboard/expiring-licenses/');
      return response.data;
    },
    refetchInterval: 60 * 60 * 1000, // Refetch every hour
  });

  const getAlertLevel = (daysUntilExpiry: number) => {
    if (daysUntilExpiry <= 0) return 'expired';
    if (daysUntilExpiry <= 7) return 'critical';
    if (daysUntilExpiry <= 30) return 'warning';
    return 'info';
  };

  const getAlertStyles = (level: string) => {
    switch (level) {
      case 'expired':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'expired':
        return (
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'critical':
      case 'warning':
        return (
          <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const formatExpiryMessage = (license: ExpiringLicense) => {
    const { daysUntilExpiry } = license;
    
    if (daysUntilExpiry <= 0) {
      return '期限切れです';
    } else if (daysUntilExpiry === 1) {
      return '明日期限切れです';
    } else if (daysUntilExpiry <= 7) {
      return `あと${daysUntilExpiry}日で期限切れです`;
    } else if (daysUntilExpiry <= 30) {
      return `あと${daysUntilExpiry}日で期限切れです`;
    } else {
      return `あと${daysUntilExpiry}日で期限切れです`;
    }
  };

  const getActionMessage = (daysUntilExpiry: number) => {
    if (daysUntilExpiry <= 0) {
      return 'ライセンスが期限切れです。管理者にお問い合わせください。';
    } else if (daysUntilExpiry <= 7) {
      return '至急、管理者にライセンス更新をお問い合わせください。';
    } else if (daysUntilExpiry <= 30) {
      return 'ライセンス更新について管理者にお問い合わせください。';
    } else {
      return 'ライセンス更新の準備をお願いします。';
    }
  };

  if (isLoading || expiringLicenses.length === 0) {
    return null;
  }

  // Group licenses by alert level
  const groupedLicenses = expiringLicenses.reduce((acc, license) => {
    const level = getAlertLevel(license.daysUntilExpiry);
    if (!acc[level]) acc[level] = [];
    acc[level].push(license);
    return acc;
  }, {} as Record<string, ExpiringLicense[]>);

  // Sort levels by priority
  const levelOrder = ['expired', 'critical', 'warning', 'info'];
  const sortedLevels = levelOrder.filter(level => groupedLicenses[level]);

  return (
    <div className="space-y-4">
      {sortedLevels.map(level => (
        <div key={level} className={`border rounded-lg p-4 ${getAlertStyles(level)}`}>
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {getAlertIcon(level)}
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium">
                {level === 'expired' && 'ライセンス期限切れ'}
                {level === 'critical' && 'ライセンス期限切れ間近（緊急）'}
                {level === 'warning' && 'ライセンス期限切れ間近'}
                {level === 'info' && 'ライセンス期限切れ予告'}
              </h3>
              <div className="mt-2 space-y-3">
                {groupedLicenses[level].map(license => (
                  <div key={license.id} className="bg-white bg-opacity-50 rounded p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {license.license?.softwareName}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {license.license?.licenseType}
                        </p>
                        <p className="text-sm font-medium mt-1">
                          {formatExpiryMessage(license)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">
                          期限: {new Date(license.license?.expiryDate || '').toLocaleDateString()}
                        </p>
                        {license.daysUntilExpiry <= 7 && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mt-1">
                            {license.daysUntilExpiry <= 0 ? '期限切れ' : '緊急'}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="mt-2">
                      <p className="text-sm">
                        {getActionMessage(license.daysUntilExpiry)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default LicenseExpiryAlerts;