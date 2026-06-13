import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { detectorsApi } from './api';
import { Loader2, Camera, AlertTriangle, Zap } from 'lucide-react';

const SmartScanner = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [detection, setDetection] = useState(null);
    const [error, setError] = useState(null);
    const [previousFrame, setPreviousFrame] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const lastSentRef = useRef(0);
    const navigate = useNavigate();

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
            }
        } catch (err) {
            setError("Could not access camera: " + err.message);
            setIsDetecting(false);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = videoRef.current.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            videoRef.current.srcObject = null;
        }
    };

    const calculateFrameDifference = (currentData, previousData) => {
        if (!previousData) return 1; // First frame, consider as change
        let diff = 0;
        // Sample pixels to improve performance (check every 4th pixel)
        for (let i = 0; i < currentData.length; i += 16) {
            diff += Math.abs(currentData[i] - previousData[i]) + // R
                    Math.abs(currentData[i + 1] - previousData[i + 1]) + // G
                    Math.abs(currentData[i + 2] - previousData[i + 2]); // B
        }
        return diff / (currentData.length / 16) / 255;
    };

    const detectFrame = async () => {
        if (!videoRef.current || !canvasRef.current || !isDetecting) return;

        const video = videoRef.current;
        if (video.readyState !== 4) return;

        // Check cooldown (prevent spamming API)
        const now = Date.now();
        if (now - lastSentRef.current < 3000 || isAnalyzing) {
            return;
        }

        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        }

        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Get current frame data for difference calculation
        const currentImageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const currentData = currentImageData.data;

        // Calculate frame difference
        const frameDiff = calculateFrameDifference(currentData, previousFrame);
        setPreviousFrame(currentData.slice()); // Store for next comparison

        // If no significant change, skip processing
        if (frameDiff < 0.1) { // Increased threshold for stability
            return;
        }

        // Trigger Cloud Analysis
        lastSentRef.current = now;
        setIsAnalyzing(true);

        canvas.toBlob(async (blob) => {
            if (!blob) {
                setIsAnalyzing(false);
                return;
            }

            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                // Use the shared API client which handles FormData correctly
                const data = await detectorsApi.smartScan(formData);

                if (data && data.category && data.confidence > 0.4) {
                    setDetection({
                        label: data.category,
                        score: data.confidence,
                        mapped: mapLabelToCategory(data.category)
                    });
                }
            } catch (err) {
                console.error("Detection error:", err);
                // Don't show error to user for transient API failures, just log
            } finally {
                setIsAnalyzing(false);
            }
        }, 'image/jpeg', 0.7); // Compress to 0.7 quality
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera();
            interval = setInterval(detectFrame, 500); // Check for motion every 500ms
        } else {
            stopCamera();
            if (interval) clearInterval(interval);
        }
        return () => {
            stopCamera();
            if (interval) clearInterval(interval);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isDetecting]);

    const handleReport = () => {
        if (detection && detection.label) {
            navigate('/report', {
                state: {
                    category: detection.mapped,
                    description: `Detected ${detection.label} with ${(detection.score * 100).toFixed(0)}% confidence using AI Smart Scanner.`
                }
            });
        }
    };

    const mapLabelToCategory = (label) => {
        const map = {
            'pothole': 'road',
            'garbage': 'garbage',
            'garbage pile': 'garbage',
            'graffiti': 'vandalism',
            'graffiti vandalism': 'vandalism',
            'broken streetlight': 'streetlight',
            'illegal parking': 'parking',
            'fallen tree': 'road',
            'stray animal': 'animal',
            'fire': 'fire',
            'fire accident': 'fire',
            'flooded street': 'flood',
            'water leak': 'water',
            'blocked road': 'blocked'
        };
        return map[label] || 'road';
    };

    return (
        <div className="flex flex-col items-center w-full h-full relative">
            {/* Header Overlay */}
            <div className="absolute top-0 left-0 w-full p-4 z-10 flex justify-between items-center bg-gradient-to-b from-black/70 to-transparent">
                <button onClick={onBack} className="text-white font-bold flex items-center gap-2 bg-black/30 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20">
                    &larr; Back
                </button>
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/80 backdrop-blur-md rounded-full border border-blue-400/30">
                    <Zap size={14} className="text-yellow-300 fill-yellow-300" />
                    <span className="text-white text-xs font-black uppercase tracking-wider">AI Active</span>
                </div>
            </div>

            {error && (
                <div className="absolute top-20 z-20 mx-4 bg-red-100/90 backdrop-blur-md border border-red-400 text-red-700 px-4 py-3 rounded-2xl flex items-center gap-3">
                    <AlertTriangle size={20} />
                    <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            <div className="relative w-full h-screen bg-black overflow-hidden flex items-center justify-center">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="absolute inset-0 w-full h-full object-cover"
                />
                <canvas
                    ref={canvasRef}
                    className="hidden"
                />

                {/* Scanner Overlay UI */}
                {isDetecting && (
                    <>
                        <div className="absolute inset-0 pointer-events-none border-[30px] border-black/30"></div>
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="w-64 h-64 border-2 border-white/50 rounded-3xl relative">
                                <div className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-blue-500 -mt-1 -ml-1 rounded-tl-lg"></div>
                                <div className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-blue-500 -mt-1 -mr-1 rounded-tr-lg"></div>
                                <div className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-blue-500 -mb-1 -ml-1 rounded-bl-lg"></div>
                                <div className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-blue-500 -mb-1 -mr-1 rounded-br-lg"></div>

                                {isAnalyzing && (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-full h-0.5 bg-blue-500/80 shadow-[0_0_15px_rgba(59,130,246,0.8)] animate-scan-y"></div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                )}

                {/* Detection Result Card */}
                {detection && detection.label !== 'safe' && detection.label !== 'unknown' && (
                    <div className="absolute bottom-32 left-4 right-4 bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl p-5 rounded-3xl shadow-2xl border border-white/20 animate-slide-up">
                        <div className="flex justify-between items-center">
                            <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-500 mb-1">Detected Issue</p>
                                <h3 className="text-xl font-black text-gray-900 dark:text-white capitalize">{detection.label}</h3>
                                <p className="text-sm font-bold text-blue-600">{(detection.score * 100).toFixed(0)}% Confidence</p>
                            </div>
                            <button
                                onClick={handleReport}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-2xl font-black text-sm shadow-lg shadow-blue-600/30 transform transition active:scale-95"
                            >
                                Report This
                            </button>
                        </div>
                    </div>
                )}

                {/* Controls */}
                <div className="absolute bottom-8 left-0 w-full flex justify-center z-20">
                    <button
                        onClick={() => setIsDetecting(!isDetecting)}
                        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all transform active:scale-90 ${
                            isDetecting
                            ? 'bg-red-500 border-4 border-white'
                            : 'bg-white border-4 border-gray-200'
                        }`}
                    >
                        {isDetecting ? (
                            <div className="w-6 h-6 bg-white rounded-md"></div>
                        ) : (
                            <div className="w-6 h-6 bg-red-500 rounded-full"></div>
                        )}
                    </button>
                </div>

                {/* Status Text */}
                <div className="absolute bottom-24 text-center w-full pointer-events-none">
                    <p className="text-white/80 font-medium text-sm bg-black/30 backdrop-blur-sm inline-block px-4 py-1 rounded-full">
                        {isDetecting
                            ? isAnalyzing ? "Analyzing scene..." : "Scanning for issues..."
                            : "Tap button to start scanner"}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SmartScanner;
