import React from 'react';
import { useTranslation } from 'react-i18next';

const AppHeader = () => {
  const { t } = useTranslation();
  return (
    <header className="bg-white shadow-sm p-4 sticky top-0 z-50 flex justify-between items-center backdrop-blur-md bg-white/80">
      <h1 className="text-2xl font-black tracking-tight text-gray-900">
        Vishwa<span className="text-blue-600">Guru</span>
      </h1>
      <div className="flex items-center gap-2">
          {/* Add language selector or profile here if needed */}
      </div>
    </header>
  );
};

export default AppHeader;
