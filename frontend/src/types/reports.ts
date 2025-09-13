// Report types
export interface UsageStatistics {
  department_stats: Record<string, DepartmentStats>;
  position_stats: Record<string, PositionStats>;
  device_usage: DeviceUsage;
  license_usage: LicenseUsage;
  period_summary: PeriodSummary;
  generated_at: string;
}

export interface DepartmentStats {
  employee_count: number;
  device_assignments: number;
  license_assignments: number;
  avg_devices_per_employee: number;
  avg_licenses_per_employee: number;
}

export interface PositionStats {
  employee_count: number;
  device_assignments: number;
  license_assignments: number;
  avg_devices_per_employee: number;
  avg_licenses_per_employee: number;
}

export interface DeviceUsage {
  total_devices: number;
  assigned_devices: number;
  available_devices: number;
  utilization_rate: number;
  type_breakdown: DeviceTypeBreakdown[];
}

export interface DeviceTypeBreakdown {
  type: string;
  total: number;
  assigned: number;
  available: number;
  utilization_rate: number;
}

export interface LicenseUsage {
  total_licenses: number;
  used_licenses: number;
  available_licenses: number;
  utilization_rate: number;
  software_breakdown: SoftwareBreakdown[];
}

export interface SoftwareBreakdown {
  software_name: string;
  total_count: number;
  used_count: number;
  available_count: number;
  utilization_rate: number;
}

export interface PeriodSummary {
  start_date: string;
  end_date: string;
  total_assignments: number;
  new_assignments: number;
  returned_assignments: number;
}

export interface InventoryStatus {
  device_inventory: DeviceInventory;
  license_inventory: LicenseInventory;
  utilization_rates: UtilizationRates;
  shortage_predictions: ShortagePredictions;
  generated_at: string;
}

export interface DeviceInventory {
  summary: {
    total_devices: number;
    available_devices: number;
    assigned_devices: number;
    maintenance_devices: number;
    overall_utilization: number;
  };
  type_breakdown: DeviceTypeInventory[];
}

export interface DeviceTypeInventory {
  type: string;
  total: number;
  available: number;
  assigned: number;
  maintenance: number;
  utilization_rate: number;
}

export interface LicenseInventory {
  summary: {
    total_licenses: number;
    used_licenses: number;
    available_licenses: number;
    overall_utilization: number;
  };
  license_details: LicenseDetail[];
}

export interface LicenseDetail {
  software_name: string;
  license_type: string;
  total_count: number;
  used_count: number;
  available_count: number;
  utilization_percentage: number;
  expiry_date: string;
}

export interface UtilizationRates {
  device_utilization: number;
  license_utilization: number;
  department_utilization: Record<string, number>;
}

export interface ShortagePredictions {
  devices_at_risk: DeviceShortage[];
  licenses_at_risk: LicenseShortage[];
}

export interface DeviceShortage {
  type: string;
  current_available: number;
  predicted_demand: number;
  shortage_risk: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface LicenseShortage {
  software_name: string;
  current_available: number;
  predicted_demand: number;
  shortage_risk: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface CostAnalysis {
  department_costs: Record<string, DepartmentCost>;
  software_costs: Record<string, SoftwareCost>;
  cost_trends: CostTrends;
  budget_comparison: BudgetComparison;
  generated_at: string;
}

export interface DepartmentCost {
  employee_count: number;
  license_assignments: number;
  monthly_cost: number;
  yearly_cost: number;
  avg_cost_per_employee: number;
}

export interface SoftwareCost {
  total_licenses: number;
  used_licenses: number;
  utilization_percentage: number;
  pricing_model: 'MONTHLY' | 'YEARLY' | 'PERPETUAL';
  unit_price: number;
  monthly_cost: number;
  yearly_cost: number;
}

export interface CostTrends {
  monthly_trends: MonthlyTrend[];
  yearly_projection: number;
}

export interface MonthlyTrend {
  month: string;
  total_cost: number;
  device_cost: number;
  license_cost: number;
}

export interface BudgetComparison {
  allocated_budget: number;
  current_spending: number;
  projected_spending: number;
  budget_utilization: number;
}

export interface ReportFilters {
  department?: string;
  position?: string;
  start_date?: string;
  end_date?: string;
  device_type?: string;
  software_name?: string;
}

export interface ExportRequest {
  format: 'csv' | 'pdf';
  report_type: 'usage_stats' | 'inventory_status' | 'cost_analysis';
  filters?: ReportFilters;
}