import React, { useRef, useState, useCallback } from 'react';
import Webcam from "react-webcam";
import { Camera, RefreshCw, Eye } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const ZeroShotDetector = ({ onBack }) => {
    const webcamRef = useRef(null);
    const [image, setImage] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImage(imageSrc);
        analyzeImage(imageSrc);
    }, [webcamRef]);

    const retake = () => {
        setImage(null);
        setResults(null);
        setError(null);
    };

    const analyzeImage = async (imageSrc) => {
        setAnalyzing(true);
        setError(null);
        try {
            const res = await fetch(imageSrc);
            const blob = await res.blob();

            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            const response = await fetch(`${API_URL}/api/hf/zero-shot-image`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("Failed to analyze image");
            }

            const data = await response.json();
            setResults(data.predictions || []);
        } catch (err) {
            console.error("Analysis error:", err);
            setError("Could not analyze image. Try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    return (
        <div className="flex flex-col items-center p-4 w-full h-full min-h-screen bg-gray-50">
            <button onClick={onBack} className="self-start text-blue-600 mb-4 font-bold">
                &larr; Back
            </button>

            <h2 className="text-xl font-bold mb-4 text-purple-800 flex items-center gap-2">
                <Eye className="text-purple-600"/> Hugging Face Vision Explorer
            </h2>

            <div className="relative w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden shadow-lg">
                {!image ? (
                    <Webcam
                        audio={false}
                        ref={webcamRef}
                        screenshotFormat="image/jpeg"
                        className="w-full h-full object-cover"
                        videoConstraints={{ facingMode: "environment" }}
                        onUserMediaError={(e) => { console.warn("Camera fallback:", e); }}
                    />
                ) : (
                    <img src={image} alt="Captured" className="w-full h-full object-cover" />
                )}

                {analyzing && (
                    <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-2"></div>
                        <p>Analyzing via Hugging Face...</p>
                    </div>
                )}
            </div>

            <div className="mt-6 flex gap-4 w-full max-w-md">
                {!image ? (
                    <button
                        onClick={capture}
                        className="flex-1 bg-purple-600 text-white py-3 rounded-xl font-bold flex justify-center items-center gap-2 hover:bg-purple-700 active:scale-95 transition-all shadow-md"
                    >
                        <Camera size={20} /> Capture Image
                    </button>
                ) : (
                    <button
                        onClick={retake}
                        disabled={analyzing}
                        className="flex-1 bg-gray-200 text-gray-800 py-3 rounded-xl font-bold flex justify-center items-center gap-2 hover:bg-gray-300 active:scale-95 transition-all shadow-md disabled:opacity-50"
                    >
                        <RefreshCw size={20} /> Retake
                    </button>
                )}
            </div>

            {error && (
                <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg w-full max-w-md text-center text-sm font-medium border border-red-200">
                    {error}
                </div>
            )}

            {results && results.length > 0 && (
                <div className="mt-6 w-full max-w-md bg-white rounded-xl shadow-md p-4 border border-purple-100">
                    <h3 className="font-bold text-gray-800 mb-3 border-b pb-2 flex items-center justify-between">
                        <span>AI Predictions</span>
                        <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded-full">google/vit-base</span>
                    </h3>
                    <div className="space-y-3">
                        {results.slice(0, 5).map((r, i) => (
                            <div key={i}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium text-gray-700 capitalize">{r.label}</span>
                                    <span className="text-gray-500 font-mono">{(r.score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                    <div
                                        className="bg-purple-600 h-2 rounded-full transition-all duration-500 ease-out"
                                        style={{ width: `${r.score * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <p className="mt-6 text-xs text-gray-400 text-center max-w-xs">
                Powered by Hugging Face Inference API. Evaluates images against thousands of classes automatically.
            </p>
        </div>
    );
};

export default ZeroShotDetector;
