import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../../services/reportsApi';
import { ReportFilters, InventoryStatus } from '../../types/reports';
import { LoadingSpinner } from '../common';

interface InventoryReportProps {
  onExport?: (type: 'csv' | 'pdf', filters: ReportFilters) => void;
}

const InventoryReport: React.FC<InventoryReportProps> = ({ onExport }) => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<ReportFilters>({});
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>({});

  const { data: inventoryData, isLoading, error } = useQuery({
    queryKey: ['inventoryStatus', appliedFilters],
    queryFn: () => reportsApi.getInventoryStatus(appliedFilters),
    enabled: true,
  });

  const handleFilterChange = (key: keyof ReportFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const applyFilters = () => {
    setAppliedFilters(filters);
  };

  const clearFilters = () => {
    setFilters({});
    setAppliedFilters({});
  };

  const handleExport = (format: 'csv' | 'pdf') => {
    if (onExport) {
      onExport(format, appliedFilters);
    }
  };

  const getRiskBadgeColor = (risk: 'LOW' | 'MEDIUM' | 'HIGH') => {
    switch (risk) {
      case 'LOW':
        return 'bg-green-100 text-green-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'HIGH':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
        <span className="ml-2">{t('reports.loading')}</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">
          {t('common.error')}: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          {t('reports.inventoryStatus.title')}
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            {t('reports.exportCsv')}
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            {t('reports.exportPdf')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">{t('reports.filters')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.deviceType')}
            </label>
            <input
              type="text"
              value={filters.device_type || ''}
              onChange={(e) => handleFilterChange('device_type', e.target.value)}
              placeholder={t('reports.deviceType')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.softwareName')}
            </label>
            <input
              type="text"
              value={filters.software_name || ''}
              onChange={(e) => handleFilterChange('software_name', e.target.value)}
              placeholder={t('reports.softwareName')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex space-x-2 mt-4">
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            {t('reports.applyFilters')}
          </button>
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            {t('reports.clearFilters')}
          </button>
        </div>
      </div>

      {/* Report Content */}
      {inventoryData ? (
        <div className="space-y-6">
          {/* Generated At */}
          <div className="text-sm text-gray-500">
            {t('reports.generatedAt')}: {new Date(inventoryData.generated_at).toLocaleString()}
          </div>

          {/* Device Inventory Summary */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.inventoryStatus.deviceInventory')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {inventoryData.device_inventory.summary.total_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.totalDevices')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {inventoryData.device_inventory.summary.available_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.availableDevices')}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {inventoryData.device_inventory.summary.assigned_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.assignedDevices')}
                </div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {inventoryData.device_inventory.summary.maintenance_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.inventoryStatus.maintenanceDevices')}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(inventoryData.device_inventory.summary.overall_utilization * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.inventoryStatus.overallUtilization')}
                </div>
              </div>
            </div>

            {/* Device Type Breakdown */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                {t('reports.inventoryStatus.typeBreakdown')}
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.deviceType')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        総数
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        利用可能
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        割当済み
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        修理中
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.usageStatistics.utilizationRate')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inventoryData.device_inventory.type_breakdown.map((typeData) => (
                      <tr key={typeData.type}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {typeData.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {typeData.total}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {typeData.available}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {typeData.assigned}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {typeData.maintenance}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {(typeData.utilization_rate * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* License Inventory */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.inventoryStatus.licenseInventory')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {inventoryData.license_inventory.summary.total_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.totalLicenses')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {inventoryData.license_inventory.summary.available_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.availableLicenses')}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {inventoryData.license_inventory.summary.used_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.usedLicenses')}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(inventoryData.license_inventory.summary.overall_utilization * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.inventoryStatus.overallUtilization')}
                </div>
              </div>
            </div>

            {/* License Details */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                {t('reports.inventoryStatus.licenseDetails')}
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.softwareName')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ライセンス種別
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        総数
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        使用中
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        利用可能
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.inventoryStatus.utilizationPercentage')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.inventoryStatus.expiryDate')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inventoryData.license_inventory.license_details.map((license, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {license.software_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {license.license_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {license.total_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {license.used_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {license.available_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {license.utilization_percentage.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(license.expiry_date).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Shortage Predictions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.inventoryStatus.shortagePredictions')}
            </h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Devices at Risk */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">
                  {t('reports.inventoryStatus.devicesAtRisk')}
                </h4>
                {inventoryData.shortage_predictions.devices_at_risk.length > 0 ? (
                  <div className="space-y-3">
                    {inventoryData.shortage_predictions.devices_at_risk.map((device, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium text-gray-900">{device.type}</div>
                            <div className="text-sm text-gray-500">
                              {t('reports.inventoryStatus.currentAvailable')}: {device.current_available}
                            </div>
                            <div className="text-sm text-gray-500">
                              {t('reports.inventoryStatus.predictedDemand')}: {device.predicted_demand}
                            </div>
                          </div>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskBadgeColor(device.shortage_risk)}`}>
                            {t(`reports.inventoryStatus.riskLevels.${device.shortage_risk}`)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-4">
                    不足リスクのある端末はありません
                  </div>
                )}
              </div>

              {/* Licenses at Risk */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">
                  {t('reports.inventoryStatus.licensesAtRisk')}
                </h4>
                {inventoryData.shortage_predictions.licenses_at_risk.length > 0 ? (
                  <div className="space-y-3">
                    {inventoryData.shortage_predictions.licenses_at_risk.map((license, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium text-gray-900">{license.software_name}</div>
                            <div className="text-sm text-gray-500">
                              {t('reports.inventoryStatus.currentAvailable')}: {license.current_available}
                            </div>
                            <div className="text-sm text-gray-500">
                              {t('reports.inventoryStatus.predictedDemand')}: {license.predicted_demand}
                            </div>
                          </div>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskBadgeColor(license.shortage_risk)}`}>
                            {t(`reports.inventoryStatus.riskLevels.${license.shortage_risk}`)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-4">
                    不足リスクのあるライセンスはありません
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Utilization Rates */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.inventoryStatus.utilizationRates')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {(inventoryData.utilization_rates.device_utilization * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  端末全体利用率
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {(inventoryData.utilization_rates.license_utilization * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  ライセンス全体利用率
                </div>
              </div>
            </div>

            {/* Department Utilization */}
            <div className="mt-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">
                部署別利用率
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(inventoryData.utilization_rates.department_utilization).map(([dept, rate]) => (
                  <div key={dept} className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-lg font-semibold text-gray-900">
                      {(rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">{dept}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-8 text-center">
          <div className="text-gray-500">{t('reports.noData')}</div>
        </div>
      )}
    </div>
  );
};

export default InventoryReport;