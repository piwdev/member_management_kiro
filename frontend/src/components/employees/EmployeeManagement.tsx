import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Employee } from '../../types';
import EmployeeList from './EmployeeList';
import EmployeeForm from './EmployeeForm';
import EmployeeDetail from './EmployeeDetail';
import EmployeeDeleteDialog from './EmployeeDeleteDialog';

type ViewMode = 'list' | 'form' | 'detail' | 'delete';

const EmployeeManagement: React.FC = () => {
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleEmployeeSelect = (employee: Employee) => {
    setSelectedEmployee(employee);
    setViewMode('detail');
  };

  const handleEmployeeEdit = (employee: Employee) => {
    setSelectedEmployee(employee);
    setViewMode('form');
  };

  const handleEmployeeDelete = (employee: Employee) => {
    setSelectedEmployee(employee);
    setViewMode('delete');
  };

  const handleNewEmployee = () => {
    setSelectedEmployee(null);
    setViewMode('form');
  };

  const handleFormSave = (employee: Employee) => {
    setViewMode('list');
    setSelectedEmployee(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setViewMode('list');
    setSelectedEmployee(null);
  };

  const handleDetailEdit = () => {
    setViewMode('form');
  };

  const handleDetailDelete = () => {
    setViewMode('delete');
  };

  const handleDetailClose = () => {
    setViewMode('list');
    setSelectedEmployee(null);
  };

  const handleDeleteConfirm = () => {
    setViewMode('list');
    setSelectedEmployee(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDeleteCancel = () => {
    setViewMode('detail');
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'form':
        return (
          <EmployeeForm
            employee={selectedEmployee || undefined}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        );
      case 'detail':
        return selectedEmployee ? (
          <EmployeeDetail
            employee={selectedEmployee}
            onEdit={handleDetailEdit}
            onDelete={handleDetailDelete}
            onClose={handleDetailClose}
          />
        ) : null;
      case 'delete':
        return selectedEmployee ? (
          <EmployeeDeleteDialog
            employee={selectedEmployee}
            onConfirm={handleDeleteConfirm}
            onCancel={handleDeleteCancel}
          />
        ) : null;
      case 'list':
      default:
        return (
          <EmployeeList
            key={refreshTrigger} // Force re-render when refreshTrigger changes
            onEmployeeSelect={handleEmployeeSelect}
            onEmployeeEdit={handleEmployeeEdit}
            onEmployeeDelete={handleEmployeeDelete}
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
                {t('employees.title')}
              </h1>
              <button
                onClick={handleNewEmployee}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                {t('common.add')} {t('employees.title')}
              </button>
            </div>
            <EmployeeList
              key={refreshTrigger}
              onEmployeeSelect={handleEmployeeSelect}
              onEmployeeEdit={handleEmployeeEdit}
              onEmployeeDelete={handleEmployeeDelete}
            />
          </div>
        </div>
      )}
      
      {viewMode === 'form' && (
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
            <EmployeeForm
              employee={selectedEmployee || undefined}
              onSave={handleFormSave}
              onCancel={handleFormCancel}
            />
          </div>
        </div>
      )}

      {viewMode === 'detail' && selectedEmployee && (
        <EmployeeDetail
          employee={selectedEmployee}
          onEdit={handleDetailEdit}
          onDelete={handleDetailDelete}
          onClose={handleDetailClose}
        />
      )}

      {viewMode === 'delete' && selectedEmployee && (
        <EmployeeDeleteDialog
          employee={selectedEmployee}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
        />
      )}
    </div>
  );
};

export default EmployeeManagement;