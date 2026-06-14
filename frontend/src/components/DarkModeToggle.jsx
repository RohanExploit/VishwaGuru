import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Moon, Sun } from 'lucide-react';

/**
 * DarkModeToggle component
 * Provides a button to toggle between light and dark modes
 * Uses Lucide icons for visual feedback
 */
const DarkModeToggle = ({ className = "" }) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative p-2.5 rounded-lg transition-all duration-300
        bg-gray-100 dark:bg-gray-800
        hover:bg-gray-200 dark:hover:bg-gray-700
        text-gray-800 dark:text-gray-200
        border border-gray-300 dark:border-gray-600
        hover:shadow-lg dark:hover:shadow-lg
        focus:outline-none focus:ring-2 focus:ring-offset-2
        focus:ring-orange-500 dark:focus:ring-offset-[#1a1a1a]
        group
        ${className}
      `}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      {/* Sun icon - shown in light mode */}
      <Sun
        size={20}
        className={`
          absolute transition-all duration-300
          ${isDark ? 'opacity-0 rotate-90 scale-0' : 'opacity-100 rotate-0 scale-100'}
        `}
      />
      
      {/* Moon icon - shown in dark mode */}
      <Moon
        size={20}
        className={`
          absolute transition-all duration-300
          ${isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'}
        `}
      />
      
      {/* Placeholder to maintain button size */}
      <div className="w-5 h-5" />
    </button>
  );
};

export default DarkModeToggle;
