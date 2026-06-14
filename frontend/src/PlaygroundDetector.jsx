import React, { useRef, useState, useEffect } from 'react';
import { Camera, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { detectorsApi } from './api';

const PlaygroundDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const startCamera = React.useCallback(async () => {
        setError(null);
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (err) {
            setError("Camera access failed: " + err.message);
        }
    }, []);

    const stopCamera = React.useCallback(() => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    }, [stream]);

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, [startCamera, stopCamera]);

    const analyze = async () => {
        if (!videoRef.current || !canvasRef.current) return;

        setAnalyzing(true);
        setResult(null);

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        canvas.toBlob(async (blob) => {
            if (!blob) return;
            const formData = new FormData();
            formData.append('image', blob, 'playground.jpg');

            try {
                const data = await detectorsApi.playground(formData);
                if (data.error) throw new Error(data.error);
                setResult(data.detections);
            } catch (err) {
                console.error(err);
                setError("Analysis failed. Please try again.");
            } finally {
                setAnalyzing(false);
            }
        }, 'image/jpeg', 0.8);
    };

    return (
        <div className="flex flex-col items-center w-full max-w-md mx-auto p-4">
            <div className="w-full flex justify-between items-center mb-4">
                <button onClick={onBack} className="text-orange-600 font-bold">&larr; Back</button>
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <ShieldCheck className="text-orange-600" />
                    Playground Safety
                </h2>
                <div className="w-8"></div>
            </div>

             {error && (
                <div className="w-full bg-red-50 text-red-600 p-3 rounded-lg mb-4 flex items-center gap-2">
                    <AlertTriangle size={18} />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            <div className="relative w-full aspect-[4/3] bg-black rounded-2xl overflow-hidden shadow-lg mb-6">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />
                <canvas ref={canvasRef} className="hidden" />

                {analyzing && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm">
                        <div className="flex flex-col items-center text-white">
                            <RefreshCw className="animate-spin mb-2" size={32} />
                            <span className="font-medium">Checking equipment...</span>
                        </div>
                    </div>
                )}
            </div>

            {result ? (
                <div className="w-full space-y-4 animate-fadeIn">
                    <h3 className="text-lg font-bold text-gray-800">Safety Report</h3>

                    {result.length > 0 ? (
                        <div className="space-y-2">
                            {result.map((det, idx) => (
                                <div key={idx} className="flex justify-between items-center p-3 bg-white rounded-lg border border-gray-100 shadow-sm">
                                    <span className="font-medium text-gray-700 capitalize">{det.label}</span>
                                    <span className={`text-sm font-bold ${det.confidence > 0.7 ? 'text-red-600' : 'text-orange-500'}`}>
                                        {(det.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center p-4 bg-green-50 rounded-lg text-green-700 font-medium">
                            Equipment appears safe.
                        </div>
                    )}

                    <button
                        onClick={() => setResult(null)}
                        className="w-full mt-4 bg-gray-900 text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition"
                    >
                        Check Next Item
                    </button>
                </div>
            ) : (
                <button
                    onClick={analyze}
                    disabled={analyzing || !!error}
                    className="w-full bg-orange-600 text-white py-4 rounded-xl font-bold shadow-lg hover:bg-orange-700 transition transform active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                    <Camera size={24} />
                    Check Safety
                </button>
            )}
        </div>
    );
};

export default PlaygroundDetector;
