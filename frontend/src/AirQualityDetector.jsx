import React, { useRef, useState, useEffect } from 'react';
import { CloudRain, Wind, AlertTriangle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const AirQualityDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const startCamera = async () => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (err) {
            setError("Camera access denied: " + err.message);
            setIsDetecting(false);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            videoRef.current.srcObject.getTracks().forEach(t => t.stop());
            videoRef.current.srcObject = null;
        }
    };

    const captureAndAnalyze = async () => {
        if (!videoRef.current || !isDetecting) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext('2d').drawImage(videoRef.current, 0, 0);

        canvas.toBlob(async (blob) => {
            if (!blob) return;
            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            try {
                const res = await fetch(`${API_URL}/api/detect-air-quality`, {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.detections && data.detections.length > 0) {
                        setResult(data.detections[0]); // Top result
                    } else {
                        setResult({ label: "Analysing...", confidence: 0 });
                    }
                }
            } catch (e) {
                console.error("Air Quality Check failed", e);
            }
        }, 'image/jpeg', 0.8);
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera();
            interval = setInterval(captureAndAnalyze, 3000); // Every 3s
        } else {
            stopCamera();
            setResult(null);
        }
        return () => {
            stopCamera();
            clearInterval(interval);
        };
    }, [isDetecting]);

    return (
        <div className="flex flex-col items-center p-4 max-w-md mx-auto w-full min-h-screen bg-gray-50">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-800">
                <Wind className="text-blue-500" />
                Air Quality Monitor
            </h2>

            <div className="relative w-full aspect-[3/4] bg-black rounded-2xl overflow-hidden shadow-lg mb-6">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`w-full h-full object-cover transition-opacity ${isDetecting ? 'opacity-100' : 'opacity-50'}`}
                />

                {!isDetecting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                        <span className="text-white font-medium">Camera Paused</span>
                    </div>
                )}

                {isDetecting && result && (
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-6 text-center pt-20">
                        <p className="text-white/80 text-xs uppercase tracking-wider mb-1">Current Status</p>
                        <h3 className={`text-2xl font-bold ${
                            result.label.includes('hazardous') || result.label.includes('dense smog') ? 'text-red-400' :
                            result.label.includes('mild') ? 'text-yellow-400' : 'text-green-400'
                        }`}>
                            {result.label.toUpperCase()}
                        </h3>
                        <div className="w-full bg-gray-700 h-1.5 mt-3 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ${
                                    result.label.includes('hazardous') ? 'bg-red-500' : 'bg-blue-500'
                                }`}
                                style={{ width: `${result.confidence * 100}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-lg flex items-center gap-2 mb-4 w-full">
                    <AlertTriangle size={18} />
                    {error}
                </div>
            )}

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full py-4 rounded-xl font-bold text-white shadow-lg transition-all active:scale-95 ${
                    isDetecting ? 'bg-red-500 hover:bg-red-600 shadow-red-200' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'
                }`}
            >
                {isDetecting ? 'Stop Monitoring' : 'Start Monitoring'}
            </button>

            <button onClick={onBack} className="mt-6 text-gray-500 font-medium hover:text-gray-800">
                Back to Dashboard
            </button>
        </div>
    );
};

export default AirQualityDetector;
