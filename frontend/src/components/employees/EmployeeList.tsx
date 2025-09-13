import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Employee } from '../../types';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface EmployeeListProps {
  onEmployeeSelect?: (employee: Employee) => void;
  onEmployeeEdit?: (employee: Employee) => void;
  onEmployeeDelete?: (employee: Employee) => void;
}

const EmployeeList: React.FC<EmployeeListProps> = ({
  onEmployeeSelect,
  onEmployeeEdit,
  onEmployeeDelete,
}) => {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Get unique departments and locations for filters
  const departments = Array.from(new Set(employees.map(emp => emp.department)));
  const locations = ['TOKYO', 'OKINAWA', 'REMOTE'];

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/employees/');
      setEmployees(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const filteredEmployees = employees.filter(employee => {
    const matchesSearch = employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         employee.employeeId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         employee.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDepartment = !departmentFilter || employee.department === departmentFilter;
    const matchesLocation = !locationFilter || employee.location === locationFilter;
    const matchesStatus = !statusFilter || employee.status === statusFilter;

    return matchesSearch && matchesDepartment && matchesLocation && matchesStatus;
  });

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

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={fetchEmployees} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">{t('employees.title')}</h1>
        <button
          onClick={() => window.location.href = '/employees/new'}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          {t('common.add')} {t('employees.title')}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('common.search')}
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="名前、社員ID、メールアドレス"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Department Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('employees.department')}
            </label>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          {/* Location Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('employees.location')}
            </label>
            <select
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {locations.map(location => (
                <option key={location} value={location}>{getLocationLabel(location)}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('employees.status')}
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              <option value="ACTIVE">アクティブ</option>
              <option value="INACTIVE">非アクティブ</option>
            </select>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {filteredEmployees.length} 件の社員が見つかりました
          </span>
          <button
            onClick={fetchEmployees}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Employee Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.name')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.employeeId')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.department')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.position')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.location')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('employees.status')}
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEmployees.map((employee) => (
                <tr
                  key={employee.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onEmployeeSelect?.(employee)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {employee.name.charAt(0)}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {employee.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {employee.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.employeeId}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.department}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {getLocationLabel(employee.location)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(employee.status)}`}>
                      {getStatusLabel(employee.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEmployeeEdit?.(employee);
                        }}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        {t('common.edit')}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEmployeeDelete?.(employee);
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        {t('common.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredEmployees.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              {searchTerm || departmentFilter || locationFilter || statusFilter
                ? '検索条件に一致する社員が見つかりません'
                : '社員が登録されていません'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployeeList;