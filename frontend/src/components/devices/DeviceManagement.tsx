import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Device } from '../../types';
import DeviceList from './DeviceList';
import DeviceForm from './DeviceForm';
import DeviceDetail from './DeviceDetail';
import DeviceAssignmentDialog from './DeviceAssignmentDialog';
import DeviceReturnDialog from './DeviceReturnDialog';
import DeviceDeleteDialog from './DeviceDeleteDialog';

type ViewMode = 'list' | 'form' | 'detail' | 'assign' | 'return' | 'delete';

const DeviceManagement: React.FC = () => {
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleDeviceSelect = (device: Device) => {
    setSelectedDevice(device);
    setViewMode('detail');
  };

  const handleDeviceEdit = (device: Device) => {
    setSelectedDevice(device);
    setViewMode('form');
  };

  const handleDeviceDelete = (device: Device) => {
    setSelectedDevice(device);
    setViewMode('delete');
  };

  const handleDeviceAssign = (device: Device) => {
    setSelectedDevice(device);
    setViewMode('assign');
  };

  const handleDeviceReturn = (device: Device) => {
    setSelectedDevice(device);
    setViewMode('return');
  };

  const handleNewDevice = () => {
    setSelectedDevice(null);
    setViewMode('form');
  };

  const handleFormSave = (device: Device) => {
    setViewMode('list');
    setSelectedDevice(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setViewMode('list');
    setSelectedDevice(null);
  };

  const handleDetailEdit = () => {
    setViewMode('form');
  };

  const handleDetailDelete = () => {
    setViewMode('delete');
  };

  const handleDetailAssign = () => {
    setViewMode('assign');
  };

  const handleDetailReturn = () => {
    setViewMode('return');
  };

  const handleDetailClose = () => {
    setViewMode('list');
    setSelectedDevice(null);
  };

  const handleAssignSuccess = () => {
    setViewMode('list');
    setSelectedDevice(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleAssignCancel = () => {
    setViewMode('detail');
  };

  const handleReturnSuccess = () => {
    setViewMode('list');
    setSelectedDevice(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleReturnCancel = () => {
    setViewMode('detail');
  };

  const handleDeleteConfirm = () => {
    setViewMode('list');
    setSelectedDevice(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDeleteCancel = () => {
    setViewMode('detail');
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'form':
        return (
          <DeviceForm
            device={selectedDevice || undefined}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        );
      case 'detail':
        return selectedDevice ? (
          <DeviceDetail
            device={selectedDevice}
            onEdit={handleDetailEdit}
            onDelete={handleDetailDelete}
            onAssign={handleDetailAssign}
            onReturn={handleDetailReturn}
            onClose={handleDetailClose}
          />
        ) : null;
      case 'assign':
        return selectedDevice ? (
          <DeviceAssignmentDialog
            device={selectedDevice}
            onAssign={handleAssignSuccess}
            onCancel={handleAssignCancel}
          />
        ) : null;
      case 'return':
        return selectedDevice ? (
          <DeviceReturnDialog
            device={selectedDevice}
            onReturn={handleReturnSuccess}
            onCancel={handleReturnCancel}
          />
        ) : null;
      case 'delete':
        return selectedDevice ? (
          <DeviceDeleteDialog
            device={selectedDevice}
            onConfirm={handleDeleteConfirm}
            onCancel={handleDeleteCancel}
          />
        ) : null;
      case 'list':
      default:
        return (
          <DeviceList
            key={refreshTrigger}
            onDeviceSelect={handleDeviceSelect}
            onDeviceEdit={handleDeviceEdit}
            onDeviceDelete={handleDeviceDelete}
            onDeviceAssign={handleDeviceAssign}
            onDeviceReturn={handleDeviceReturn}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {viewMode === 'list' && (
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-2xl font-semibold text-gray-900">
                {t('devices.title')}
              </h1>
              <button
                onClick={handleNewDevice}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                {t('common.add')} {t('devices.title')}
              </button>
            </div>
            <DeviceList
              key={refreshTrigger}
              onDeviceSelect={handleDeviceSelect}
              onDeviceEdit={handleDeviceEdit}
              onDeviceDelete={handleDeviceDelete}
              onDeviceAssign={handleDeviceAssign}
              onDeviceReturn={handleDeviceReturn}
            />
          </div>
        </div>
      )}
      
      {viewMode === 'form' && (
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
            <DeviceForm
              device={selectedDevice || undefined}
              onSave={handleFormSave}
              onCancel={handleFormCancel}
            />
          </div>
        </div>
      )}

      {viewMode === 'detail' && selectedDevice && (
        <DeviceDetail
          device={selectedDevice}
          onEdit={handleDetailEdit}
          onDelete={handleDetailDelete}
          onAssign={handleDetailAssign}
          onReturn={handleDetailReturn}
          onClose={handleDetailClose}
        />
      )}

      {viewMode === 'assign' && selectedDevice && (
        <DeviceAssignmentDialog
          device={selectedDevice}
          onAssign={handleAssignSuccess}
          onCancel={handleAssignCancel}
        />
      )}

      {viewMode === 'return' && selectedDevice && (
        <DeviceReturnDialog
          device={selectedDevice}
          onReturn={handleReturnSuccess}
          onCancel={handleReturnCancel}
        />
      )}

      {viewMode === 'delete' && selectedDevice && (
        <DeviceDeleteDialog
          device={selectedDevice}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
        />
      )}
    </div>
  );
};

export default DeviceManagement;