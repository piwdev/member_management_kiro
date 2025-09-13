import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { reportsApi } from '../../services/reportsApi';
import { ReportFilters, UsageStatistics } from '../../types/reports';
import { LoadingSpinner } from '../common';

interface UsageReportProps {
  onExport?: (type: 'csv' | 'pdf', filters: ReportFilters) => void;
}

const UsageReport: React.FC<UsageReportProps> = ({ onExport }) => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<ReportFilters>({});
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>({});

  const { data: usageData, isLoading, error, refetch } = useQuery({
    queryKey: ['usageStatistics', appliedFilters],
    queryFn: () => reportsApi.getUsageStatistics(appliedFilters),
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

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  // Prepare chart data
  const departmentChartData = usageData ? Object.entries(usageData.department_stats).map(([dept, stats]) => ({
    department: dept,
    employeeCount: stats.employee_count,
    deviceAssignments: stats.device_assignments,
    licenseAssignments: stats.license_assignments,
    avgDevicesPerEmployee: stats.avg_devices_per_employee,
    avgLicensesPerEmployee: stats.avg_licenses_per_employee,
  })) : [];

  const positionChartData = usageData ? Object.entries(usageData.position_stats).map(([position, stats]) => ({
    position: position.length > 10 ? position.substring(0, 10) + '...' : position,
    fullPosition: position,
    employeeCount: stats.employee_count,
    deviceAssignments: stats.device_assignments,
    licenseAssignments: stats.license_assignments,
    avgDevicesPerEmployee: stats.avg_devices_per_employee,
    avgLicensesPerEmployee: stats.avg_licenses_per_employee,
  })) : [];

  const deviceTypeData = usageData ? usageData.device_usage.type_breakdown.map(type => ({
    type: type.type,
    total: type.total,
    assigned: type.assigned,
    available: type.available,
    utilizationRate: type.utilization_rate * 100,
  })) : [];

  const softwareData = usageData ? usageData.license_usage.software_breakdown.map(software => ({
    software: software.software_name.length > 15 ? software.software_name.substring(0, 15) + '...' : software.software_name,
    fullName: software.software_name,
    totalCount: software.total_count,
    usedCount: software.used_count,
    availableCount: software.available_count,
    utilizationRate: software.utilization_rate * 100,
  })) : [];

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
          {t('reports.usageStatistics.title')}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.startDate')}
            </label>
            <input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.endDate')}
            </label>
            <input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.department')}
            </label>
            <input
              type="text"
              value={filters.department || ''}
              onChange={(e) => handleFilterChange('department', e.target.value)}
              placeholder={t('reports.department')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reports.position')}
            </label>
            <input
              type="text"
              value={filters.position || ''}
              onChange={(e) => handleFilterChange('position', e.target.value)}
              placeholder={t('reports.position')}
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
      {usageData ? (
        <div className="space-y-6">
          {/* Generated At */}
          <div className="text-sm text-gray-500">
            {t('reports.generatedAt')}: {new Date(usageData.generated_at).toLocaleString()}
          </div>

          {/* Department Statistics Charts */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.usageStatistics.departmentStats')}
            </h3>
            
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Department Resource Assignments */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">部署別リソース割当数</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="department" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="deviceAssignments" fill="#8884d8" name="端末割当数" />
                    <Bar dataKey="licenseAssignments" fill="#82ca9d" name="ライセンス割当数" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Average Resources per Employee */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">社員あたり平均リソース数</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="department" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="avgDevicesPerEmployee" fill="#ffc658" name="平均端末数" />
                    <Bar dataKey="avgLicensesPerEmployee" fill="#ff7300" name="平均ライセンス数" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.department')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.employeeCount')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.deviceAssignments')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.licenseAssignments')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.avgDevicesPerEmployee')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.avgLicensesPerEmployee')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(usageData.department_stats).map(([dept, stats]) => (
                    <tr key={dept}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {dept}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.employee_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.device_assignments}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.license_assignments}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.avg_devices_per_employee.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.avg_licenses_per_employee.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Position Statistics */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.usageStatistics.positionStats')}
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.position')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.employeeCount')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.deviceAssignments')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.licenseAssignments')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.avgDevicesPerEmployee')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.avgLicensesPerEmployee')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(usageData.position_stats).map(([position, stats]) => (
                    <tr key={position}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {position}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.employee_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.device_assignments}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.license_assignments}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.avg_devices_per_employee.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {stats.avg_licenses_per_employee.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Device Usage Summary */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.usageStatistics.deviceUsage')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {usageData.device_usage.total_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.totalDevices')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {usageData.device_usage.assigned_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.assignedDevices')}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {usageData.device_usage.available_devices}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.availableDevices')}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(usageData.device_usage.utilization_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.utilizationRate')}
                </div>
              </div>
            </div>

            {/* Device Type Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Device Type Distribution */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">端末種別分布</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={deviceTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry: any) => `${entry.type}: ${entry.total}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="total"
                    >
                      {deviceTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Device Utilization Rates */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">端末種別利用率</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={deviceTypeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
                    <Legend />
                    <Bar dataKey="utilizationRate" fill="#8884d8" name="利用率 (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Device Type Breakdown Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.deviceType')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.totalDevices')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.assignedDevices')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.availableDevices')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.utilizationRate')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {usageData.device_usage.type_breakdown.map((typeData) => (
                    <tr key={typeData.type}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {typeData.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeData.total}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeData.assigned}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeData.available}
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

          {/* License Usage Summary */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.usageStatistics.licenseUsage')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {usageData.license_usage.total_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.totalLicenses')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {usageData.license_usage.used_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.usedLicenses')}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {usageData.license_usage.available_licenses}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.availableLicenses')}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(usageData.license_usage.utilization_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.utilizationRate')}
                </div>
              </div>
            </div>

            {/* Software Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Software License Usage */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">ソフトウェア別ライセンス使用状況</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={softwareData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="software" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name, props) => [
                        value,
                        name,
                        props.payload.fullName
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="usedCount" fill="#82ca9d" name="使用中" />
                    <Bar dataKey="availableCount" fill="#8884d8" name="利用可能" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Software Utilization Rates */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">ソフトウェア利用率</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={softwareData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="software" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name, props) => [
                        `${Number(value).toFixed(1)}%`,
                        name,
                        props.payload.fullName
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="utilizationRate" fill="#ffc658" name="利用率 (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Software Breakdown Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.softwareName')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.totalLicenses')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.usedLicenses')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.availableLicenses')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.utilizationRate')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {usageData.license_usage.software_breakdown.map((softwareData) => (
                    <tr key={softwareData.software_name}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {softwareData.software_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {softwareData.total_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {softwareData.used_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {softwareData.available_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {(softwareData.utilization_rate * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Period Summary */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.usageStatistics.periodSummary')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {usageData.period_summary.total_assignments}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.totalAssignments')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {usageData.period_summary.new_assignments}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.newAssignments')}
                </div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {usageData.period_summary.returned_assignments}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.usageStatistics.returnedAssignments')}
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {t('reports.dateRange')}: {usageData.period_summary.start_date} - {usageData.period_summary.end_date}
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

export default UsageReport;