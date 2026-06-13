import React, { useRef, useState, useEffect } from 'react';
import { Camera, Eye, Activity, Shield, Sparkles, MapPin, RefreshCw, AlertTriangle } from 'lucide-react';
import { detectorsApi } from './api';

const CivicEyeDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, []);

    const startCamera = async () => {
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
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

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
            formData.append('image', blob, 'civic_eye.jpg');

            try {
                const data = await detectorsApi.civicEye(formData);
                if (data.error) throw new Error(data.error);
                setResult(data);
            } catch (err) {
                console.error(err);
                setError("Analysis failed. Please try again.");
            } finally {
                setAnalyzing(false);
            }
        }, 'image/jpeg', 0.8);
    };

    const ScoreCard = ({ title, status, score, icon, color }) => (
        <div className={`p-4 rounded-xl border ${color} bg-white shadow-sm flex items-center justify-between`}>
            <div className="flex items-center gap-3">
                <div className={`p-2 rounded-full bg-opacity-10 ${color.replace('border', 'bg').replace('text', 'bg')}`}>
                    {icon}
                </div>
                <div>
                    <h4 className="text-xs font-bold uppercase text-gray-500">{title}</h4>
                    <p className="font-bold text-gray-800 capitalize">{status}</p>
                </div>
            </div>
            <div className="text-right">
                <span className="text-lg font-bold">{(score * 10).toFixed(1)}</span>
                <span className="text-xs text-gray-400">/10</span>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col items-center w-full max-w-md mx-auto">
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
                            <Activity className="animate-pulse mb-2" size={32} />
                            <span className="font-medium">Analyzing scene...</span>
                        </div>
                    </div>
                )}
            </div>

            {result ? (
                <div className="w-full space-y-4 animate-fadeIn">
                    <h3 className="text-xl font-bold text-center mb-2">Civic Report Card</h3>

                    <ScoreCard
                        title="Safety"
                        status={result.safety.status}
                        score={result.safety.score}
                        icon={<Shield size={20} className="text-blue-600"/>}
                        color="border-blue-100"
                    />

                    <ScoreCard
                        title="Cleanliness"
                        status={result.cleanliness.status}
                        score={result.cleanliness.score}
                        icon={<Sparkles size={20} className="text-green-600"/>}
                        color="border-green-100"
                    />

                    <ScoreCard
                        title="Infrastructure"
                        status={result.infrastructure.status}
                        score={result.infrastructure.score}
                        icon={<MapPin size={20} className="text-orange-600"/>}
                        color="border-orange-100"
                    />

                    <button
                        onClick={() => setResult(null)}
                        className="w-full mt-6 bg-gray-900 text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition flex items-center justify-center gap-2"
                    >
                        <RefreshCw size={18} />
                        Analyze New Scene
                    </button>
                </div>
            ) : (
                <div className="w-full">
                    <button
                        onClick={analyze}
                        disabled={analyzing || !!error}
                        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-xl font-bold shadow-lg hover:shadow-xl transition transform active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Eye size={24} />
                        Analyze Scene
                    </button>
                    <p className="text-center text-sm text-gray-500 mt-3">
                        Get an instant AI assessment of this location
                    </p>
                </div>
            )}
        </div>
    );
};

export default CivicEyeDetector;
