import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../lib/api';
import { DeviceAssignment, LicenseAssignment } from '../../types';
import ResourceRequestForm from './ResourceRequestForm';
import ReturnRequestForm from './ReturnRequestForm';
import LicenseExpiryAlerts from './LicenseExpiryAlerts';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface EmployeeDashboardData {
  deviceAssignments: DeviceAssignment[];
  licenseAssignments: LicenseAssignment[];
}

const EmployeeDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [showReturnForm, setShowReturnForm] = useState(false);
  const [requestType, setRequestType] = useState<'device' | 'license'>('device');

  const { data, isLoading, error, refetch } = useQuery<EmployeeDashboardData>({
    queryKey: ['employee-dashboard'],
    queryFn: async () => {
      const response = await apiClient.get('/dashboard/employee/');
      return response.data;
    },
  });

  const handleRequestClick = (type: 'device' | 'license') => {
    setRequestType(type);
    setShowRequestForm(true);
  };

  const handleRequestSuccess = () => {
    setShowRequestForm(false);
    refetch();
  };

  const handleReturnSuccess = () => {
    setShowReturnForm(false);
    refetch();
  };

  const getExpiringLicenses = () => {
    if (!data?.licenseAssignments) return [];
    
    const now = new Date();
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(now.getDate() + 30);

    return data.licenseAssignments.filter(assignment => {
      if (assignment.status !== 'ACTIVE') return false;
      
      const expiryDate = new Date(assignment.license?.expiryDate || '');
      return expiryDate <= thirtyDaysFromNow;
    });
  };

  const getDaysUntilExpiry = (expiryDate: string) => {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={t('common.error')} />;

  const deviceAssignments = data?.deviceAssignments || [];
  const licenseAssignments = data?.licenseAssignments || [];
  const expiringLicenses = getExpiringLicenses();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {t('employeeDashboard.title')}
        </h1>
        <p className="text-gray-600">
          {t('employeeDashboard.welcome', { name: user?.firstName || user?.username })}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {t('employeeDashboard.requestNew')}
        </h2>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => handleRequestClick('device')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            {t('employeeDashboard.requestDevice')}
          </button>
          <button
            onClick={() => handleRequestClick('license')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {t('employeeDashboard.requestLicense')}
          </button>
          <button
            onClick={() => setShowReturnForm(true)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            {t('employeeDashboard.returnRequest')}
          </button>
        </div>
      </div>

      {/* Resource Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* My Devices */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t('employeeDashboard.myDevices')}
            </h2>
            <span className="text-sm text-gray-500">
              {t('employeeDashboard.deviceCount', { count: deviceAssignments.length })}
            </span>
          </div>
          
          {deviceAssignments.length === 0 ? (
            <p className="text-gray-500 text-sm">
              {t('employeeDashboard.noAssignedDevices')}
            </p>
          ) : (
            <div className="space-y-3">
              {deviceAssignments.map((assignment) => (
                <div key={assignment.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">
                        {assignment.device?.manufacturer} {assignment.device?.model}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {assignment.device?.type} • {assignment.device?.serialNumber}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {assignment.purpose}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(assignment.assignedDate).toLocaleDateString()}
                      </p>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {assignment.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* My Licenses */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t('employeeDashboard.myLicenses')}
            </h2>
            <span className="text-sm text-gray-500">
              {t('employeeDashboard.licenseCount', { count: licenseAssignments.length })}
            </span>
          </div>
          
          {licenseAssignments.length === 0 ? (
            <p className="text-gray-500 text-sm">
              {t('employeeDashboard.noAssignedLicenses')}
            </p>
          ) : (
            <div className="space-y-3">
              {licenseAssignments.map((assignment) => (
                <div key={assignment.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">
                        {assignment.license?.softwareName}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {assignment.license?.licenseType}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {assignment.purpose}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(assignment.startDate).toLocaleDateString()}
                      </p>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        assignment.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                        assignment.status === 'EXPIRED' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {assignment.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* License Expiry Alerts */}
      <LicenseExpiryAlerts />

      {/* Request Form Modal */}
      {showRequestForm && (
        <ResourceRequestForm
          type={requestType}
          onSuccess={handleRequestSuccess}
          onCancel={() => setShowRequestForm(false)}
        />
      )}

      {/* Return Form Modal */}
      {showReturnForm && (
        <ReturnRequestForm
          deviceAssignments={deviceAssignments}
          licenseAssignments={licenseAssignments}
          onSuccess={handleReturnSuccess}
          onCancel={() => setShowReturnForm(false)}
        />
      )}
    </div>
  );
};

export default EmployeeDashboard;