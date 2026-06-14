import React from 'react';

const LoadingSpinner = ({ size = 'md', variant = 'primary' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    xl: 'w-12 h-12',
  };
  const colorClasses = {
    primary: 'border-blue-500',
    white: 'border-white',
  };

  return (
    <div className={`rounded-full border-2 border-transparent border-t-current animate-spin ${sizeClasses[size]} ${colorClasses[variant] === 'border-blue-500' ? 'text-blue-500' : 'text-white'}`}></div>
  );
};

export default LoadingSpinner;
