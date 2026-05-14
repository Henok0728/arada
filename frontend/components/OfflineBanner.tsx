'use client';

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const OfflineBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    // Initial check
    setIsOffline(!navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="bg-amber-600 text-white px-4 py-2 text-center text-sm font-medium animate-in slide-in-from-top duration-300">
      <span className="mr-2">⚠️</span>
      {t('common.offline_mode', 'Offline Mode: Using local verification')}
    </div>
  );
};

export default OfflineBanner;
