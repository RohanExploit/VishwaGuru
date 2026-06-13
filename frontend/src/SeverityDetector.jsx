import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle, Info, RefreshCcw } from 'lucide-react';
import { detectorsApi } from './api/detectors';

const SeverityDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, []);

    const startCamera = async () => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setIsStreaming(true);
            }
        } catch (err) {
            setError("Could not access camera: " + err.message);
            setIsStreaming(false);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = videoRef.current.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            videoRef.current.srcObject = null;
            setIsStreaming(false);
        }
    };

    const captureAndAnalyze = async () => {
        if (!videoRef.current || !canvasRef.current) return;

        setAnalyzing(true);
        setError(null);

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        // Match dimensions
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        }

        // Draw frame
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to blob
        canvas.toBlob(async (blob) => {
            if (!blob) {
                setAnalyzing(false);
                return;
            }

            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            try {
                // Call API
                const data = await detectorsApi.severity(formData);
                setResult(data);
                stopCamera(); // Stop camera to freeze the moment or just save resources
            } catch (err) {
                console.error("Analysis failed:", err);
                setError("Failed to analyze image. Please try again.");
            } finally {
                setAnalyzing(false);
            }
        }, 'image/jpeg', 0.85);
    };

    const handleReport = () => {
        if (result) {
            navigate('/report', {
                state: {
                    category: 'infrastructure', // Default fallback
                    description: `[Urgency Analysis: ${result.level}] ${result.raw_label || ''} detected.`
                }
            });
        }
    };

    const resetAnalysis = () => {
        setResult(null);
        startCamera();
    };

    const getUrgencyColor = (level) => {
        switch (level?.toLowerCase()) {
            case 'critical': return 'bg-red-600 text-white';
            case 'high': return 'bg-orange-600 text-white';
            case 'medium': return 'bg-yellow-500 text-white';
            case 'low': return 'bg-green-600 text-white';
            default: return 'bg-gray-600 text-white';
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 p-4">
             <div className="flex items-center justify-between mb-4">
                <button onClick={onBack} className="text-gray-600 font-medium">
                    &larr; Back
                </button>
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <AlertTriangle className="text-orange-500" />
                    Urgency Analysis
                </h2>
                <div className="w-8"></div> {/* Spacer */}
            </div>

            <div className="flex-grow flex flex-col items-center justify-center">
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 w-full max-w-md text-center">
                        {error}
                        <button onClick={startCamera} className="block mt-2 text-sm font-bold underline w-full">Retry Camera</button>
                    </div>
                )}

                <div className="relative w-full max-w-md bg-black rounded-2xl overflow-hidden shadow-xl aspect-[3/4] md:aspect-video mb-6">
                    {!result ? (
                        <>
                            <video
                                ref={videoRef}
                                autoPlay
                                playsInline
                                muted
                                className="w-full h-full object-cover"
                            />
                            <canvas ref={canvasRef} className="hidden" />

                            {/* Overlay Guidelines */}
                            <div className="absolute inset-0 border-2 border-white/30 m-8 rounded-lg pointer-events-none"></div>

                            {isStreaming && !analyzing && (
                                <div className="absolute bottom-6 left-0 right-0 flex justify-center">
                                    <button
                                        onClick={captureAndAnalyze}
                                        className="bg-white rounded-full p-4 shadow-lg active:scale-95 transition-transform"
                                    >
                                        <div className="w-16 h-16 rounded-full border-4 border-orange-500 bg-orange-50"></div>
                                    </button>
                                </div>
                            )}

                             {analyzing && (
                                <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center backdrop-blur-sm text-white">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
                                    <p className="font-medium">Analyzing Severity...</p>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="absolute inset-0 bg-gray-900 flex flex-col items-center justify-center p-6 text-center text-white">
                            <div className={`p-4 rounded-full mb-4 ${getUrgencyColor(result.level)} shadow-lg scale-110`}>
                                <AlertTriangle size={48} />
                            </div>
                            <h3 className="text-3xl font-bold mb-2">{result.level} Urgency</h3>
                            <p className="text-gray-300 mb-6 capitalize">{result.raw_label || "Unknown situation"}</p>

                            <div className="w-full bg-gray-800 rounded-lg p-3 mb-6">
                                <div className="flex justify-between text-sm text-gray-400 mb-1">
                                    <span>AI Confidence</span>
                                    <span>{(result.confidence * 100).toFixed(0)}%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                    <div
                                        className="bg-orange-500 h-2 rounded-full transition-all duration-1000"
                                        style={{ width: `${result.confidence * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {result && (
                    <div className="w-full max-w-md flex gap-3">
                         <button
                            onClick={resetAnalysis}
                            className="flex-1 bg-gray-200 text-gray-800 py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-gray-300 transition"
                        >
                            <RefreshCcw size={20} />
                            Scan Again
                        </button>
                        <button
                            onClick={handleReport}
                            className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-blue-700 transition shadow-lg shadow-blue-200"
                        >
                            <CheckCircle size={20} />
                            Report Now
                        </button>
                    </div>
                )}

                {!result && (
                    <p className="text-gray-500 text-sm mt-4 text-center px-6">
                        <Info size={14} className="inline mr-1" />
                        Capture an image to let AI analyze the urgency level of the situation.
                    </p>
                )}
            </div>
        </div>
    );
};

export default SeverityDetector;
