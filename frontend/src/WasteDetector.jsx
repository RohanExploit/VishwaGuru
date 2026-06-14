import React, { useRef, useState, useEffect } from 'react';
import { Camera, RefreshCw, ArrowRight, Info, CheckCircle, Trash2 } from 'lucide-react';
import { detectorsApi } from './api';

const WasteDetector = ({ onBack }) => {
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
            formData.append('image', blob, 'waste.jpg');

            try {
                const data = await detectorsApi.waste(formData);
                setResult(data);
            } catch (err) {
                console.error(err);
                setError("Analysis failed. Please try again.");
            } finally {
                setAnalyzing(false);
            }
        }, 'image/jpeg', 0.8);
    };

    const getDisposalInstruction = (type) => {
        const t = (type || '').toLowerCase();
        if (t.includes('plastic')) return { bin: 'Blue Bin', color: 'bg-blue-100 text-blue-800', icon: '♻️' };
        if (t.includes('paper') || t.includes('cardboard')) return { bin: 'Yellow Bin', color: 'bg-yellow-100 text-yellow-800', icon: '📄' };
        if (t.includes('glass')) return { bin: 'Green Bin', color: 'bg-green-100 text-green-800', icon: '🍾' };
        if (t.includes('organic') || t.includes('food')) return { bin: 'Green/Compost Bin', color: 'bg-green-100 text-green-800', icon: '🍏' };
        if (t.includes('metal') || t.includes('can')) return { bin: 'Red Bin', color: 'bg-red-100 text-red-800', icon: '🥫' };
        if (t.includes('electronic')) return { bin: 'E-Waste Center', color: 'bg-purple-100 text-purple-800', icon: '🔌' };
        return { bin: 'Black/General Bin', color: 'bg-gray-100 text-gray-800', icon: '🗑️' };
    };

    return (
        <div className="flex flex-col items-center w-full max-w-md mx-auto">
            {error && (
                <div className="w-full bg-red-50 text-red-600 p-3 rounded-lg mb-4 flex items-center gap-2">
                    <Info size={18} />
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
                            <span className="font-medium">Identifying waste...</span>
                        </div>
                    </div>
                )}
            </div>

            {result ? (
                <div className="w-full bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-fadeIn">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="bg-green-100 p-2 rounded-full">
                            <CheckCircle className="text-green-600" size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 font-medium">Detected Type</p>
                            <h3 className="text-xl font-bold text-gray-800 capitalize">{result.waste_type}</h3>
                        </div>
                    </div>

                    <div className="border-t border-gray-100 my-4"></div>

                    <div className={`p-4 rounded-xl ${getDisposalInstruction(result.waste_type).color} flex items-center gap-4`}>
                        <span className="text-3xl">{getDisposalInstruction(result.waste_type).icon}</span>
                        <div>
                            <p className="text-xs font-bold uppercase opacity-70 mb-1">Disposal Method</p>
                            <p className="font-bold text-lg">{getDisposalInstruction(result.waste_type).bin}</p>
                        </div>
                    </div>

                    <p className="text-xs text-center text-gray-400 mt-4">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                    </p>

                    <button
                        onClick={() => setResult(null)}
                        className="w-full mt-6 bg-gray-900 text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition flex items-center justify-center gap-2"
                    >
                        <RefreshCw size={18} />
                        Scan Another Item
                    </button>
                </div>
            ) : (
                <div className="w-full">
                    <button
                        onClick={analyze}
                        disabled={analyzing || !!error}
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-bold shadow-lg hover:shadow-xl transition transform active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Camera size={24} />
                        Identify Waste
                    </button>
                    <p className="text-center text-sm text-gray-500 mt-3">
                        Point camera at the item and tap to identify
                    </p>
                </div>
            )}
        </div>
    );
};

export default WasteDetector;
