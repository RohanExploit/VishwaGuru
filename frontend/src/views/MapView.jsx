import React from 'react';

const MapView = ({ responsibilityMap, setView }) => (
  <div className="mt-6 border-t pt-8 max-w-4xl mx-auto px-4 text-center">
    <h2 className="text-4xl font-extrabold mb-8 text-center bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Responsibility Map</h2>
    <div className="grid gap-4 sm:grid-cols-2">
      {responsibilityMap && Object.entries(responsibilityMap).map(([key, value]) => (
        <div key={key} className="bg-white p-6 rounded-xl shadow-md border border-gray-100 hover:shadow-lg transition-shadow duration-300">
          <h3 className="font-extrabold text-xl text-blue-800 capitalize mb-3 border-b pb-2">{key.replace('_', ' ')}</h3>
          <p className="font-medium text-gray-800">{value.authority}</p>
          <p className="text-sm text-gray-600 mt-1">{value.description}</p>
        </div>
      ))}
    </div>
    <button onClick={() => setView('home')} className="mt-10 mb-8 inline-block bg-blue-50 text-blue-600 font-semibold px-6 py-3 rounded-full hover:bg-blue-100 transition-colors mx-auto">Back to Home</button>
  </div>
);

export default MapView;
