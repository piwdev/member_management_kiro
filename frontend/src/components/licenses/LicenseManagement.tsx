import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { License } from '../../types';
import LicenseList from './LicenseList';
import LicenseForm from './LicenseForm';
import LicenseDetail from './LicenseDetail';
import LicenseAssignmentDialog from './LicenseAssignmentDialog';
import LicenseDeleteDialog from './LicenseDeleteDialog';

type ViewMode = 'list' | 'form' | 'detail' | 'assign' | 'delete';

const LicenseManagement: React.FC = () => {
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedLicense, setSelectedLicense] = useState<License | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleLicenseSelect = (license: License) => {
    setSelectedLicense(license);
    setViewMode('detail');
  };

  const handleLicenseEdit = (license: License) => {
    setSelectedLicense(license);
    setViewMode('form');
  };

  const handleLicenseDelete = (license: License) => {
    setSelectedLicense(license);
    setViewMode('delete');
  };

  const handleLicenseAssign = (license: License) => {
    setSelectedLicense(license);
    setViewMode('assign');
  };

  const handleNewLicense = () => {
    setSelectedLicense(null);
    setViewMode('form');
  };

  const handleFormSave = (license: License) => {
    setViewMode('list');
    setSelectedLicense(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setViewMode('list');
    setSelectedLicense(null);
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

  const handleDetailClose = () => {
    setViewMode('list');
    setSelectedLicense(null);
  };

  const handleAssignSuccess = () => {
    setViewMode('list');
    setSelectedLicense(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleAssignCancel = () => {
    setViewMode('detail');
  };

  const handleDeleteConfirm = () => {
    setViewMode('list');
    setSelectedLicense(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDeleteCancel = () => {
    setViewMode('detail');
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'form':
        return (
          <LicenseForm
            license={selectedLicense || undefined}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        );
      case 'detail':
        return selectedLicense ? (
          <LicenseDetail
            license={selectedLicense}
            onEdit={handleDetailEdit}
            onDelete={handleDetailDelete}
            onAssign={handleDetailAssign}
            onClose={handleDetailClose}
          />
        ) : null;
      case 'assign':
        return selectedLicense ? (
          <LicenseAssignmentDialog
            license={selectedLicense}
            onAssign={handleAssignSuccess}
            onCancel={handleAssignCancel}
          />
        ) : null;
      case 'delete':
        return selectedLicense ? (
          <LicenseDeleteDialog
            license={selectedLicense}
            onConfirm={handleDeleteConfirm}
            onCancel={handleDeleteCancel}
          />
        ) : null;
      case 'list':
      default:
        return (
          <LicenseList
            key={refreshTrigger}
            onLicenseSelect={handleLicenseSelect}
            onLicenseEdit={handleLicenseEdit}
            onLicenseDelete={handleLicenseDelete}
            onLicenseAssign={handleLicenseAssign}
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
                {t('licenses.title')}
              </h1>
              <button
                onClick={handleNewLicense}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                {t('common.add')} {t('licenses.title')}
              </button>
            </div>
            <LicenseList
              key={refreshTrigger}
              onLicenseSelect={handleLicenseSelect}
              onLicenseEdit={handleLicenseEdit}
              onLicenseDelete={handleLicenseDelete}
              onLicenseAssign={handleLicenseAssign}
            />
          </div>
        </div>
      )}
      
      {viewMode === 'form' && (
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
            <LicenseForm
              license={selectedLicense || undefined}
              onSave={handleFormSave}
              onCancel={handleFormCancel}
            />
          </div>
        </div>
      )}

      {viewMode === 'detail' && selectedLicense && (
        <LicenseDetail
          license={selectedLicense}
          onEdit={handleDetailEdit}
          onDelete={handleDetailDelete}
          onAssign={handleDetailAssign}
          onClose={handleDetailClose}
        />
      )}

      {viewMode === 'assign' && selectedLicense && (
        <LicenseAssignmentDialog
          license={selectedLicense}
          onAssign={handleAssignSuccess}
          onCancel={handleAssignCancel}
        />
      )}

      {viewMode === 'delete' && selectedLicense && (
        <LicenseDeleteDialog
          license={selectedLicense}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
        />
      )}
    </div>
  );
};

export default LicenseManagement;