import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import LanguageSwitch from './LanguageSwitch';
import NotificationCenter from './NotificationCenter';

const Header: React.FC = () => {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and title */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-semibold text-gray-900">
                Asset License Management
              </h1>
            </div>
          </div>

          {/* Right side - User info and controls */}
          <div className="flex items-center space-x-4">
            <LanguageSwitch />
            
            {user && (
              <>
                <NotificationCenter />
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-700">
                    {user.firstName} {user.lastName}
                  </span>
                  <button
                    onClick={logout}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                  >
                    {t('auth.logout')}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;