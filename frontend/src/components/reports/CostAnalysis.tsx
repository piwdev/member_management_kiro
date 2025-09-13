import React, { useState } from 'react';
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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { reportsApi } from '../../services/reportsApi';
import { ReportFilters, CostAnalysis as CostAnalysisType } from '../../types/reports';
import { LoadingSpinner } from '../common';

interface CostAnalysisProps {
  onExport?: (type: 'csv' | 'pdf', filters: ReportFilters) => void;
}

const CostAnalysis: React.FC<CostAnalysisProps> = ({ onExport }) => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<ReportFilters>({});
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>({});

  const { data: costData, isLoading, error } = useQuery({
    queryKey: ['costAnalysis', appliedFilters],
    queryFn: () => reportsApi.getCostAnalysis(appliedFilters),
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  // Prepare chart data
  const departmentChartData = costData ? Object.entries(costData.department_costs).map(([dept, costs]) => ({
    department: dept,
    monthlyCost: costs.monthly_cost,
    yearlyCost: costs.yearly_cost,
    employeeCount: costs.employee_count,
    avgCostPerEmployee: costs.avg_cost_per_employee,
  })) : [];

  const softwareChartData = costData ? Object.entries(costData.software_costs).map(([software, costs]) => ({
    software: software.length > 15 ? software.substring(0, 15) + '...' : software,
    fullName: software,
    monthlyCost: costs.monthly_cost,
    yearlyCost: costs.yearly_cost,
    utilizationPercentage: costs.utilization_percentage,
    usedLicenses: costs.used_licenses,
    totalLicenses: costs.total_licenses,
  })) : [];

  const monthlyTrendsData = costData ? costData.cost_trends.monthly_trends.map(trend => ({
    month: trend.month,
    totalCost: trend.total_cost,
    deviceCost: trend.device_cost,
    licenseCost: trend.license_cost,
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
          {t('reports.costAnalysis.title')}
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
      {costData ? (
        <div className="space-y-6">
          {/* Generated At */}
          <div className="text-sm text-gray-500">
            {t('reports.generatedAt')}: {new Date(costData.generated_at).toLocaleString()}
          </div>

          {/* Budget Comparison */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.costAnalysis.budgetComparison')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(costData.budget_comparison.allocated_budget)}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.costAnalysis.allocatedBudget')}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(costData.budget_comparison.current_spending)}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.costAnalysis.currentSpending')}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {formatCurrency(costData.budget_comparison.projected_spending)}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.costAnalysis.projectedSpending')}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(costData.budget_comparison.budget_utilization * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.costAnalysis.budgetUtilization')}
                </div>
              </div>
            </div>
          </div>

          {/* Department Costs */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.costAnalysis.departmentCosts')}
            </h3>
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
                      {t('reports.usageStatistics.licenseAssignments')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.monthlyCost')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.yearlyCost')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.avgCostPerEmployee')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(costData.department_costs).map(([dept, costs]) => (
                    <tr key={dept}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {dept}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.employee_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.license_assignments}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.monthly_cost)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.yearly_cost)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.avg_cost_per_employee)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Software Costs */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.costAnalysis.softwareCosts')}
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.softwareName')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.totalLicenses')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.usedLicenses')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.usageStatistics.utilizationRate')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.pricingModel')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.unitPrice')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.monthlyCost')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('reports.costAnalysis.yearlyCost')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(costData.software_costs).map(([software, costs]) => (
                    <tr key={software}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {software}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.total_licenses}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.used_licenses}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.utilization_percentage.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {costs.pricing_model}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.unit_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.monthly_cost)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(costs.yearly_cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Department Cost Charts */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              部署別コスト分析グラフ
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Monthly Cost Bar Chart */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">月額コスト比較</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="department" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`} />
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Legend />
                    <Bar dataKey="monthlyCost" fill="#8884d8" name="月額コスト" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Average Cost per Employee */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">社員あたり平均コスト</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="department" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`} />
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Legend />
                    <Bar dataKey="avgCostPerEmployee" fill="#82ca9d" name="社員あたり平均コスト" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Software Cost Analysis */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              ソフトウェア別コスト分析
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Software Cost Bar Chart */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">ソフトウェア別月額コスト</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={softwareChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="software" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`} />
                    <Tooltip 
                      formatter={(value, name, props) => [
                        formatCurrency(Number(value)), 
                        name,
                        props.payload.fullName
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="monthlyCost" fill="#ffc658" name="月額コスト" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Software Utilization Pie Chart */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">ソフトウェア利用率分布</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={softwareChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry: any) => 
                        `${entry.software}: ${entry.utilizationPercentage.toFixed(1)}%`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="utilizationPercentage"
                    >
                      {softwareChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value, name, props) => [
                        `${Number(value).toFixed(1)}%`,
                        '利用率',
                        props.payload.fullName
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Cost Trends */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('reports.costAnalysis.costTrends')}
            </h3>
            
            {/* Yearly Projection */}
            <div className="mb-6">
              <div className="bg-indigo-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-indigo-600">
                  {formatCurrency(costData.cost_trends.yearly_projection)}
                </div>
                <div className="text-sm text-gray-600">
                  {t('reports.costAnalysis.yearlyProjection')}
                </div>
              </div>
            </div>

            {/* Monthly Trends Chart */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">
                月次コスト推移
              </h4>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={monthlyTrendsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`} />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="totalCost" 
                    stroke="#8884d8" 
                    strokeWidth={3}
                    name="総コスト" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="deviceCost" 
                    stroke="#82ca9d" 
                    strokeWidth={2}
                    name="端末コスト" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="licenseCost" 
                    stroke="#ffc658" 
                    strokeWidth={2}
                    name="ライセンスコスト" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Monthly Trends Table */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                {t('reports.costAnalysis.monthlyTrends')}
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        月
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        総コスト
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.costAnalysis.deviceCost')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('reports.costAnalysis.licenseCost')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costData.cost_trends.monthly_trends.map((trend) => (
                      <tr key={trend.month}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {trend.month}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatCurrency(trend.total_cost)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatCurrency(trend.device_cost)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatCurrency(trend.license_cost)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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

export default CostAnalysis;