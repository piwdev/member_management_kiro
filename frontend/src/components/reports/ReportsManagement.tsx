import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { reportsApi } from '../../services/reportsApi';
import { ReportFilters, ExportRequest } from '../../types/reports';
import UsageReport from './UsageReport';
import CostAnalysis from './CostAnalysis';
import InventoryReport from './InventoryReport';

type ReportType = 'usage' | 'cost' | 'inventory';

const ReportsManagement: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ReportType>('usage');

  const exportMutation = useMutation({
    mutationFn: (request: ExportRequest) => reportsApi.exportReport(request),
    onSuccess: (blob, variables) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `${variables.report_type}_${timestamp}.${variables.format}`;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
    onError: (error) => {
      console.error('Export failed:', error);
      // You could show a toast notification here
    },
  });

  const handleExport = (format: 'csv' | 'pdf', filters: ReportFilters) => {
    let reportType: ExportRequest['report_type'];
    
    switch (activeTab) {
      case 'usage':
        reportType = 'usage_stats';
        break;
      case 'cost':
        reportType = 'cost_analysis';
        break;
      case 'inventory':
        reportType = 'inventory_status';
        break;
      default:
        reportType = 'usage_stats';
    }

    exportMutation.mutate({
      format,
      report_type: reportType,
      filters,
    });
  };

  const tabs = [
    {
      id: 'usage' as ReportType,
      name: t('reports.usageReport'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: 'cost' as ReportType,
      name: t('reports.costAnalysis'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'inventory' as ReportType,
      name: t('reports.inventoryReport'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('reports.title')}</h1>
          <p className="mt-2 text-gray-600">
            システムの利用状況、コスト分析、在庫状況を確認できます
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.icon}
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Export Status */}
        {exportMutation.isPending && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-blue-800">エクスポート中...</span>
            </div>
          </div>
        )}

        {exportMutation.isError && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              エクスポートに失敗しました: {exportMutation.error instanceof Error ? exportMutation.error.message : 'Unknown error'}
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm">
          {activeTab === 'usage' && <UsageReport onExport={handleExport} />}
          {activeTab === 'cost' && <CostAnalysis onExport={handleExport} />}
          {activeTab === 'inventory' && <InventoryReport onExport={handleExport} />}
        </div>
      </div>
    </div>
  );
};

export default ReportsManagement;