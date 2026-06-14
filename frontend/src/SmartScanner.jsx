import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as tf from '@tensorflow/tfjs';
import * as mobilenet from '@tensorflow-models/mobilenet';

const API_URL = import.meta.env.VITE_API_URL || '';

const SmartScanner = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [detection, setDetection] = useState(null);
    const [error, setError] = useState(null);
    const [model, setModel] = useState(null);
    const [previousFrame, setPreviousFrame] = useState(null);
    const lastSentRef = useRef(0);
    const navigate = useNavigate();

    // Define functions before useEffect to avoid hoisting issues
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
        for (let i = 0; i < currentData.length; i += 4) {
            diff += Math.abs(currentData[i] - previousData[i]) + // R
                    Math.abs(currentData[i + 1] - previousData[i + 1]) + // G
                    Math.abs(currentData[i + 2] - previousData[i + 2]); // B
        }
        return diff / (currentData.length / 4) / 255; // Average difference normalized
    };

    const detectFrame = async () => {
        if (!videoRef.current || !canvasRef.current || !isDetecting || !model) return;

        const video = videoRef.current;
        if (video.readyState !== 4) return;

        // Check cooldown
        const now = Date.now();
        if (now - lastSentRef.current < 2000) {
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
        if (frameDiff < 0.05) { // Threshold for change detection
            return;
        }

        // Run local inference
        const predictions = await model.classify(canvas);
        const topPrediction = predictions[0];

        // If frame changed and local model has high confidence, send to backend
        if (topPrediction.probability > 0.5) {
            lastSentRef.current = now; // Update timestamp
            // Proceed to backend detection
            canvas.toBlob(async (blob) => {
                if (!blob) return;

                const formData = new FormData();
                formData.append('image', blob, 'frame.jpg');

                try {
                    const response = await fetch(`${API_URL}/api/detect-smart-scan`, {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        const data = await response.json();
                        setDetection({ label: data.category, score: data.confidence });
                    }
                } catch (err) {
                    console.error("Detection error:", err);
                }
            }, 'image/jpeg', 0.8);
        } else {
            // Local detection: low confidence, consider safe
            setDetection({ label: 'Safe', score: topPrediction.probability });
        }
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera();
            interval = setInterval(detectFrame, 2000);
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
        if (detection && detection.label && detection.label !== 'Safe' && detection.label !== 'unknown') {
            navigate('/report', {
                state: {
                    category: mapLabelToCategory(detection.label),
                    description: `Detected ${detection.label} using Smart Scanner.`
                }
            });
        }
    };

    const mapLabelToCategory = (label) => {
        // Map CLIP labels to ReportForm categories
        const map = {
            'pothole': 'road',
            'garbage pile': 'garbage',
            'graffiti': 'vandalism',
            'broken streetlight': 'streetlight',
            'illegal parking': 'road',
            'fallen tree': 'road',
            'stray animal': 'road',
            'fire': 'road',
            'flooded street': 'water'
        };
        return map[label] || 'road';
    };

    return (
        <div className="mt-6 flex flex-col items-center w-full">
            <h2 className="text-xl font-semibold mb-4 text-center">Smart City Scanner</h2>

            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

            <div className="relative w-full max-w-md bg-black rounded-lg overflow-hidden shadow-lg mb-6">
                <div className="relative">
                     <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-auto block"
                        style={{ opacity: isDetecting ? 1 : 0.5 }}
                    />
                    <canvas
                        ref={canvasRef}
                        className="absolute top-0 left-0 w-full h-full pointer-events-none hidden"
                    />

                    {/* Overlay */}
                    {isDetecting && detection && (
                        <div className="absolute bottom-0 left-0 w-full bg-black bg-opacity-70 p-3 text-white">
                            <div className="flex justify-between items-center">
                                <div>
                                    <p className="font-bold text-lg capitalize">{detection.label}</p>
                                    <p className="text-sm text-gray-300">{(detection.score * 100).toFixed(0)}% Confidence</p>
                                </div>
                                {detection.label !== 'Safe' && detection.label !== 'unknown' && detection.label !== 'uncertain' && (
                                    <button
                                        onClick={handleReport}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-bold"
                                    >
                                        Report
                                    </button>
                                )}
                            </div>
                        </div>
                    )}

                    {!isDetecting && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <p className="text-white font-medium bg-black bg-opacity-50 px-4 py-2 rounded">
                                Scanner Paused
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {isDetecting ? 'Stop Scanning' : 'Start Live Scan'}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
                Point at civic issues. The AI will identify them automatically.
            </p>

            <button
                onClick={onBack}
                className="mt-6 text-gray-600 hover:text-gray-900 underline"
            >
                Back to Home
            </button>
        </div>
    );
};

export default SmartScanner;
