import React from 'react';

const LoadingSpinner = ({ size = 'md', variant = 'primary' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const variantClasses = {
    primary: 'border-blue-600',
    secondary: 'border-gray-600',
    white: 'border-white'
  };

  return (
    <div className={`animate-spin rounded-full border-b-2 border-t-2 border-r-2 border-transparent ${sizeClasses[size]} ${variantClasses[variant]}`}></div>
  );
};

export default LoadingSpinner;
