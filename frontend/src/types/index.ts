// Common types
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// Employee types
export interface Employee extends BaseEntity {
  employeeId: string;
  name: string;
  email: string;
  department: string;
  position: string;
  location: 'TOKYO' | 'OKINAWA' | 'REMOTE';
  hireDate: string;
  status: 'ACTIVE' | 'INACTIVE';
}

// Device types
export interface Device extends BaseEntity {
  type: 'LAPTOP' | 'DESKTOP' | 'TABLET' | 'SMARTPHONE';
  manufacturer: string;
  model: string;
  serialNumber: string;
  purchaseDate: string;
  warrantyExpiry: string;
  status: 'AVAILABLE' | 'ASSIGNED' | 'MAINTENANCE' | 'DISPOSED';
}

// License types
export interface License extends BaseEntity {
  softwareName: string;
  licenseType: string;
  totalCount: number;
  availableCount: number;
  expiryDate: string;
  licenseKey?: string;
  pricingModel: 'MONTHLY' | 'YEARLY' | 'PERPETUAL';
  unitPrice: number;
}

// Assignment types
export interface DeviceAssignment extends BaseEntity {
  deviceId: string;
  employeeId: string;
  assignedDate: string;
  returnDate?: string;
  purpose: string;
  status: 'ACTIVE' | 'RETURNED';
  device?: Device;
  employee?: Employee;
}

export interface LicenseAssignment extends BaseEntity {
  licenseId: string;
  employeeId: string;
  assignedDate: string;
  startDate: string;
  endDate?: string;
  purpose: string;
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED';
  license?: License;
  employee?: Employee;
}

// Permission types
export interface PermissionPolicy extends BaseEntity {
  name: string;
  department?: string;
  position?: string;
  allowedDeviceTypes: string[];
  allowedSoftware: string[];
  restrictedSoftware: string[];
}

// Auth types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  isActive: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// Request types
export interface ResourceRequest extends BaseEntity {
  type: 'device' | 'license';
  employeeId: string;
  deviceType?: string;
  softwareName?: string;
  purpose: string;
  startDate: string;
  endDate?: string;
  businessJustification: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  approvedBy?: string;
  approvedAt?: string;
  rejectionReason?: string;
}

export interface ReturnRequest extends BaseEntity {
  resourceType: 'device' | 'license';
  resourceId: string;
  employeeId: string;
  returnDate: string;
  returnReason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  approvedBy?: string;
  approvedAt?: string;
  rejectionReason?: string;
}

// Notification types
export interface Notification extends BaseEntity {
  userId: string;
  title: string;
  message: string;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  isRead: boolean;
  relatedResourceType?: 'device' | 'license' | 'request';
  relatedResourceId?: string;
}

// Error types
export interface ApiError {
  message: string;
  details?: Record<string, string[]>;
}

// Re-export report types
export * from './reports';