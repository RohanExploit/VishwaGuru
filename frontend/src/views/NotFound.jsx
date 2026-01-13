import React from 'react';
import { Link } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center space-y-6 py-8">
      <div className="bg-red-50 border-2 border-red-100 p-8 rounded-xl text-center">
        <div className="flex justify-center mb-4">
          <div className="bg-red-500 text-white p-4 rounded-full">
            <AlertCircle size={48} />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-red-800 mb-2">404</h2>
        <p className="text-xl font-semibold text-red-700 mb-2">Page Not Found</p>
        <p className="text-gray-600 mb-6">
          Oops! The page you are looking for does not exist or has been moved.
        </p>
      </div>
      
      <Link
        to="/"
        className="flex items-center justify-center bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition shadow-md"
      >
        <Home size={20} className="mr-2" />
        <span className="font-semibold">Back to Home</span>
      </Link>
    </div>
  );
};

export default NotFound;
