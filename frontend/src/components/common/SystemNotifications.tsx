import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../lib/api';

interface SystemNotification {
  id: string;
  title: string;
  message: string;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  isActive: boolean;
  startDate: string;
  endDate?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  dismissible: boolean;
}

const SystemNotifications: React.FC = () => {
  const { t } = useTranslation();
  const [dismissedNotifications, setDismissedNotifications] = useState<string[]>(() => {
    const stored = localStorage.getItem('dismissedSystemNotifications');
    return stored ? JSON.parse(stored) : [];
  });

  const { data: notifications = [] } = useQuery<SystemNotification[]>({
    queryKey: ['system-notifications'],
    queryFn: async () => {
      const response = await apiClient.get('/system-notifications/');
      return response.data.results || response.data;
    },
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  useEffect(() => {
    localStorage.setItem('dismissedSystemNotifications', JSON.stringify(dismissedNotifications));
  }, [dismissedNotifications]);

  const handleDismiss = (notificationId: string) => {
    setDismissedNotifications(prev => [...prev, notificationId]);
  };

  const getNotificationStyles = (type: string, priority: string) => {
    const baseStyles = "border-l-4 p-4 mb-4";
    
    let typeStyles = "";
    switch (type) {
      case 'ERROR':
        typeStyles = "bg-red-50 border-red-400 text-red-700";
        break;
      case 'WARNING':
        typeStyles = "bg-yellow-50 border-yellow-400 text-yellow-700";
        break;
      case 'SUCCESS':
        typeStyles = "bg-green-50 border-green-400 text-green-700";
        break;
      default:
        typeStyles = "bg-blue-50 border-blue-400 text-blue-700";
    }

    const priorityStyles = priority === 'HIGH' ? "shadow-lg" : "";
    
    return `${baseStyles} ${typeStyles} ${priorityStyles}`;
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'ERROR':
        return (
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'WARNING':
        return (
          <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'SUCCESS':
        return (
          <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const activeNotifications = notifications.filter(notification => {
    // Check if notification is active
    if (!notification.isActive) return false;
    
    // Check if notification is within date range
    const now = new Date();
    const startDate = new Date(notification.startDate);
    const endDate = notification.endDate ? new Date(notification.endDate) : null;
    
    if (now < startDate) return false;
    if (endDate && now > endDate) return false;
    
    // Check if notification has been dismissed
    if (notification.dismissible && dismissedNotifications.includes(notification.id)) {
      return false;
    }
    
    return true;
  });

  // Sort by priority (HIGH first) and then by creation date
  const sortedNotifications = activeNotifications.sort((a, b) => {
    const priorityOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;
    
    return new Date(b.startDate).getTime() - new Date(a.startDate).getTime();
  });

  if (sortedNotifications.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4 mb-6">
      {sortedNotifications.map((notification) => (
        <div
          key={notification.id}
          className={getNotificationStyles(notification.type, notification.priority)}
          role="alert"
        >
          <div className="flex">
            <div className="flex-shrink-0">
              {getIcon(notification.type)}
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium">
                {notification.title}
                {notification.priority === 'HIGH' && (
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    重要
                  </span>
                )}
              </h3>
              <div className="mt-2 text-sm">
                <p>{notification.message}</p>
              </div>
            </div>
            {notification.dismissible && (
              <div className="ml-auto pl-3">
                <div className="-mx-1.5 -my-1.5">
                  <button
                    onClick={() => handleDismiss(notification.id)}
                    className="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 hover:bg-gray-100"
                  >
                    <span className="sr-only">閉じる</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default SystemNotifications;