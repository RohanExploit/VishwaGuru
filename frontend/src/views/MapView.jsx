import React from 'react';

const MapView = ({ responsibilityMap, setView }) => (
  <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
    <h2 className="text-xl font-semibold mb-4 text-center text-gray-900 dark:text-white">Responsibility Map</h2>
    <div className="grid gap-4 sm:grid-cols-2">
      {responsibilityMap && Object.entries(responsibilityMap).map(([key, value]) => (
        <div key={key} className="bg-gray-50 dark:bg-gray-800 p-4 rounded shadow-sm dark:shadow-md border border-gray-200 dark:border-gray-700">
          <h3 className="font-bold text-lg capitalize mb-2 text-gray-900 dark:text-white">{key.replace('_', ' ')}</h3>
          <p className="font-medium text-gray-800 dark:text-gray-300">{value.authority}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{value.description}</p>
        </div>
      ))}
    </div>
    <button onClick={() => setView('home')} className="mt-6 text-blue-600 dark:text-blue-400 underline hover:text-blue-700 dark:hover:text-blue-300 text-center w-full block transition">Back to Home</button>
  </div>
);

export default MapView;
