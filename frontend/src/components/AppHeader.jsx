import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, User, LogOut, Sun, Moon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import LanguageSelector from './LanguageSelector';

const AppHeader = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, logout } = useAuth(); // useAuth returns user, not currentUser
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out', error);
    }
  };

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm sticky top-0 z-40 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center cursor-pointer" onClick={() => navigate('/')}>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-orange-500 via-orange-400 to-green-500 drop-shadow-sm">
              {t('home.title').split(' - ')[0]}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <LanguageSelector />

            {/* Dark Mode Toggle Button */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? (
                <Sun size={20} className="text-yellow-400" />
              ) : (
                <Moon size={20} className="text-gray-700" />
              )}
            </button>

            {user ? (
              <div className="relative">
                <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 focus:outline-none transition-colors duration-200">
                  <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-full">
                    <User size={20} className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <span className="hidden sm:inline font-medium text-sm">{user.email}</span>
                </button>

                {isMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 z-50">
                    <Link to="/my-reports" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200" onClick={() => setIsMenuOpen(false)}>{t('home.issues.myReports')}</Link>
                    <button onClick={handleLogout} className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors duration-200">
                      <LogOut size={14} /> {t('common.cancel').toLowerCase() === 'cancel' ? 'Logout' : t('common.back')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link to="/login" className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 px-4 py-2 rounded-full hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors duration-200">Login</Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;
