import React, { useState } from 'react';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

const GrievanceAnalysis = ({ onBack }) => {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleClassify = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/classify-grievance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error('Classification failed');
      }

      const data = await response.json();
      setResult(data.category);
    } catch (err) {
      setError('Failed to classify grievance. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full p-4">
      <button
        onClick={onBack}
        className="self-start text-blue-600 mb-4 font-semibold flex items-center"
      >
        &larr; Back to Home
      </button>

      <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-100 flex-1">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Grievance Classifier</h2>
        <p className="text-gray-600 mb-6">
          Enter your grievance description below to automatically classify it using our Machine Learning model trained on Indian public grievances.
        </p>

        <textarea
          className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4 h-40 resize-none"
          placeholder="e.g., The street lights in Sector 4 are not working properly..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <button
          onClick={handleClassify}
          disabled={loading || !text.trim()}
          className={`w-full py-3 rounded-lg text-white font-bold text-lg transition duration-200 ${
            loading || !text.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-md'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Classifying...
            </span>
          ) : (
            'Analyze Grievance'
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6 p-6 bg-green-50 rounded-xl border border-green-200 text-center animate-fade-in">
            <h3 className="text-gray-500 font-medium uppercase tracking-wide text-xs mb-2">Predicted Department</h3>
            <div className="text-3xl font-extrabold text-green-700">
              {result}
            </div>
            <p className="text-green-600 text-sm mt-2">
              Based on the content of your complaint.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GrievanceAnalysis;
