import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Shield, Leaf, Building, RefreshCcw, Info, CheckCircle } from 'lucide-react';
import { detectorsApi } from './api/detectors';

const CivicEyeDetector = ({ onBack }) => {
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

        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        }

        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            if (!blob) {
                setAnalyzing(false);
                return;
            }

            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            try {
                const data = await detectorsApi.civicEye(formData);
                setResult(data);
                stopCamera();
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
                    category: 'infrastructure',
                    description: `[Civic Eye Analysis]\nSafety: ${result.safety?.status} (${(result.safety?.score * 100).toFixed(0)}%)\nCleanliness: ${result.cleanliness?.status} (${(result.cleanliness?.score * 100).toFixed(0)}%)\nInfrastructure: ${result.infrastructure?.status} (${(result.infrastructure?.score * 100).toFixed(0)}%)`
                }
            });
        }
    };

    const resetAnalysis = () => {
        setResult(null);
        startCamera();
    };

    const ScoreCard = ({ icon: Icon, label, status, score, color }) => (
        <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${color}`}>
                    <Icon size={20} />
                </div>
                <div>
                    <p className="text-xs text-gray-500 font-bold uppercase">{label}</p>
                    <p className="text-sm font-semibold capitalize text-gray-800">{status}</p>
                </div>
            </div>
            <div className="text-right">
                <span className="text-lg font-bold text-gray-700">{(score * 100).toFixed(0)}</span>
                <span className="text-xs text-gray-400">%</span>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col h-full bg-gray-50 p-4">
            <div className="flex items-center justify-between mb-4">
                <button onClick={onBack} className="text-gray-600 font-medium">
                    &larr; Back
                </button>
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Eye className="text-blue-600" />
                    Civic Eye
                </h2>
                <div className="w-8"></div>
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

                            <div className="absolute inset-0 border-2 border-white/30 m-8 rounded-lg pointer-events-none"></div>

                            {isStreaming && !analyzing && (
                                <div className="absolute bottom-6 left-0 right-0 flex justify-center">
                                    <button
                                        onClick={captureAndAnalyze}
                                        className="bg-white rounded-full p-4 shadow-lg active:scale-95 transition-transform"
                                    >
                                        <div className="w-16 h-16 rounded-full border-4 border-blue-500 bg-blue-50"></div>
                                    </button>
                                </div>
                            )}

                             {analyzing && (
                                <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center backdrop-blur-sm text-white">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
                                    <p className="font-medium">Analyzing Scene...</p>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="absolute inset-0 bg-gray-50 flex flex-col p-4 overflow-y-auto">
                            <h3 className="text-lg font-bold text-gray-800 mb-4 text-center">Analysis Results</h3>

                            <ScoreCard
                                icon={Shield}
                                label="Safety"
                                status={result.safety?.status}
                                score={result.safety?.score || 0}
                                color="bg-blue-100 text-blue-600"
                            />
                            <ScoreCard
                                icon={Leaf}
                                label="Cleanliness"
                                status={result.cleanliness?.status}
                                score={result.cleanliness?.score || 0}
                                color="bg-green-100 text-green-600"
                            />
                            <ScoreCard
                                icon={Building}
                                label="Infrastructure"
                                status={result.infrastructure?.status}
                                score={result.infrastructure?.score || 0}
                                color="bg-orange-100 text-orange-600"
                            />

                            <div className="mt-4 flex gap-3">
                                <button
                                    onClick={resetAnalysis}
                                    className="flex-1 bg-white border border-gray-300 text-gray-700 py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-gray-50 transition"
                                >
                                    <RefreshCcw size={20} />
                                    Scan Again
                                </button>
                                <button
                                    onClick={handleReport}
                                    className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-blue-700 transition shadow-lg shadow-blue-200"
                                >
                                    <CheckCircle size={20} />
                                    Report
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {!result && (
                    <p className="text-gray-500 text-sm mt-4 text-center px-6">
                        <Info size={14} className="inline mr-1" />
                        Scan the area to assess safety, cleanliness, and infrastructure quality.
                    </p>
                )}
            </div>
        </div>
    );
};

export default CivicEyeDetector;
