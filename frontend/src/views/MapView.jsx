import React from 'react';

const MapView = ({ responsibilityMap, setView }) => (
  <div className="mt-6 border-t pt-4">
    <h2 className="text-xl font-semibold mb-4 text-center">Responsibility Map</h2>
    <div className="grid gap-4 sm:grid-cols-2">
      {responsibilityMap && Object.entries(responsibilityMap).map(([key, value]) => (
        <div key={key} className="bg-gray-50 p-4 rounded shadow-sm border">
          <h3 className="font-bold text-lg capitalize mb-2">{key.replace('_', ' ')}</h3>
          <p className="font-medium text-gray-800">{value.authority}</p>
          <p className="text-sm text-gray-600 mt-1">{value.description}</p>
        </div>
      ))}
    </div>
    <button onClick={() => setView('home')} className="mt-6 text-blue-600 underline text-center w-full block">Back to Home</button>
  </div>
);

export default MapView;
