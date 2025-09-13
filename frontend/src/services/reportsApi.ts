import { apiClient } from '../lib/api';
import { 
  UsageStatistics, 
  InventoryStatus, 
  CostAnalysis, 
  ReportFilters, 
  ExportRequest 
} from '../types/reports';

export const reportsApi = {
  // Usage statistics
  getUsageStatistics: async (filters?: ReportFilters): Promise<UsageStatistics> => {
    const params = new URLSearchParams();
    if (filters?.department) params.append('department', filters.department);
    if (filters?.position) params.append('position', filters.position);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get(`/reports/usage-statistics/?${params.toString()}`);
    return response.data.data;
  },

  // Department usage
  getDepartmentUsage: async (filters?: Pick<ReportFilters, 'start_date' | 'end_date'>) => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get(`/reports/department-usage/?${params.toString()}`);
    return response.data.data;
  },

  // Position usage
  getPositionUsage: async (filters?: Pick<ReportFilters, 'start_date' | 'end_date'>) => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get(`/reports/position-usage/?${params.toString()}`);
    return response.data.data;
  },

  // Inventory status
  getInventoryStatus: async (filters?: Pick<ReportFilters, 'device_type' | 'software_name'>): Promise<InventoryStatus> => {
    const params = new URLSearchParams();
    if (filters?.device_type) params.append('device_type', filters.device_type);
    if (filters?.software_name) params.append('software_name', filters.software_name);

    const response = await apiClient.get(`/reports/inventory-status/?${params.toString()}`);
    return response.data.data;
  },

  // Cost analysis
  getCostAnalysis: async (filters?: Pick<ReportFilters, 'department' | 'start_date' | 'end_date'>): Promise<CostAnalysis> => {
    const params = new URLSearchParams();
    if (filters?.department) params.append('department', filters.department);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get(`/reports/cost-analysis/?${params.toString()}`);
    return response.data.data;
  },

  // Export report
  exportReport: async (exportRequest: ExportRequest): Promise<Blob> => {
    const response = await apiClient.post('/reports/export/', exportRequest, {
      responseType: 'blob',
    });
    return response.data;
  },
};