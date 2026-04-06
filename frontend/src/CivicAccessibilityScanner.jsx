import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const CivicAccessibilityScanner = ({ onBack }) => {
    const [image, setImage] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleImageChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setImage(e.target.files[0]);
            setResult(null);
        }
    };

    const analyzeImage = async () => {
        if (!image) return;
        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('image', image);

        try {
            const response = await fetch(`${API_URL}/api/detect-accessibility`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                setResult(data);
            } else {
                setError("Failed to analyze image.");
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center min-h-screen bg-gray-50 p-6">
            <h1 className="text-3xl font-extrabold text-blue-800 mb-6 drop-shadow-sm text-center">
                Civic Accessibility Scanner
            </h1>
            <p className="text-gray-600 mb-6 text-center max-w-md">
                Upload an image to detect accessibility issues like blocked wheelchair ramps or missing infrastructure.
            </p>

            <div className="w-full max-w-md bg-white p-6 rounded-xl shadow-md flex flex-col items-center">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="mb-4 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />

                {image && (
                    <img src={URL.createObjectURL(image)} alt="Preview" className="w-full h-48 object-cover rounded-lg mb-4 shadow-sm" />
                )}

                <button
                    onClick={analyzeImage}
                    disabled={!image || loading}
                    className="w-full py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Analyzing...' : 'Analyze Accessibility'}
                </button>

                {error && <p className="text-red-500 mt-4 text-sm font-medium">{error}</p>}

                {result && result.detections && (
                    <div className="mt-6 w-full text-left">
                        <h3 className="text-lg font-bold text-gray-800 border-b pb-2 mb-3">Analysis Results</h3>
                        {result.detections.length > 0 ? (
                            <ul className="space-y-2">
                                {result.detections.map((d, i) => (
                                    <li key={i} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-100">
                                        <span className="font-medium text-gray-700 capitalize">{d.label}</span>
                                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded font-bold">{(d.confidence * 100).toFixed(1)}%</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-green-600 font-medium">No accessibility issues detected.</p>
                        )}
                    </div>
                )}
            </div>

            <button onClick={onBack} className="mt-8 text-blue-600 hover:underline font-medium">
                &larr; Back to Home
            </button>
        </div>
    );
};

export default CivicAccessibilityScanner;
