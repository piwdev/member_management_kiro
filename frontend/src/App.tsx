import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { queryClient } from './lib/queryClient';
import { AuthProvider } from './contexts/AuthContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/common/Layout';
import { ToastProvider } from './components/common/ToastContainer';
import LoginForm from './components/auth/LoginForm';
import Dashboard from './components/dashboard/Dashboard';
import { ReportsManagement } from './components/reports';
import './i18n';

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <ToastProvider>
              <Routes>
              <Route path="/login" element={<LoginForm />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/employees" element={<div>Employees Page (Coming Soon)</div>} />
                        <Route path="/devices" element={<div>Devices Page (Coming Soon)</div>} />
                        <Route path="/licenses" element={<div>Licenses Page (Coming Soon)</div>} />
                        <Route path="/permissions" element={<div>Permissions Page (Coming Soon)</div>} />
                        <Route path="/reports" element={<ReportsManagement />} />
                      </Routes>
                    </Layout>
                  </ProtectedRoute>
                }
              />
              </Routes>
            </ToastProvider>
          </AuthProvider>
        </BrowserRouter>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
