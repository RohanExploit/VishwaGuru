import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const TrafficSignDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);
    const [detections, setDetections] = useState([]);

    const startCamera = async () => {
        setError(null);
        try {
            let stream;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: {
                    facingMode: 'environment',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                } });
            } catch (fallbackErr) {
                console.warn("Primary camera access failed, trying fallback:", fallbackErr);
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
            }
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
            const stream = videoRef.current.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            videoRef.current.srcObject = null;
        }
    };

    const detectSigns = async () => {
        if (!videoRef.current || videoRef.current.readyState !== 4) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            if (!blob) return;
            const formData = new FormData();
            formData.append('image', blob, 'traffic_sign.jpg');

            try {
                const response = await fetch(`${API_URL}/api/detect-traffic-sign`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.detections && data.detections.length > 0) {
                        setDetections(data.detections);
                    } else {
                        setDetections([]);
                    }
                }
            } catch (err) {
                console.error("Traffic sign detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera().then(() => {
                interval = setInterval(detectSigns, 2500); // 2.5 seconds
            });
        } else {
            stopCamera();
            setDetections([]);
        }

        return () => {
            if (interval) clearInterval(interval);
            stopCamera();
        };
    }, [isDetecting]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
            <h1 className="text-3xl font-extrabold text-amber-600 mb-6 drop-shadow-sm text-center">
                Traffic Sign Monitor
            </h1>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4 w-full max-w-md">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            <div className="relative w-full max-w-md aspect-video bg-black rounded-xl overflow-hidden shadow-2xl mb-6 border-4 border-amber-500">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />

                {!isDetecting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-60">
                        <p className="text-white font-bold bg-amber-600 px-6 py-3 rounded-full uppercase tracking-wider">
                            Camera Offline
                        </p>
                    </div>
                )}
            </div>

            {detections.length > 0 && (
                <div className="w-full max-w-md bg-white p-4 rounded-xl shadow-md mb-6 border-t-4 border-amber-500">
                    <h3 className="text-lg font-bold mb-3 text-gray-800 border-b pb-2">Detected Signs</h3>
                    <div className="space-y-3">
                        {detections.map((detection, idx) => (
                            <div key={idx} className="bg-amber-50 p-3 rounded-lg border border-amber-100">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-bold text-amber-900 capitalize">{(detection.class || detection.label || 'Traffic Sign').replace('_', ' ')}</span>
                                    <span className="text-amber-700 font-mono">{((detection.confidence ?? detection.score) * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-4 px-6 rounded-xl text-white font-black uppercase tracking-widest shadow-lg transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-500 hover:bg-amber-600'}`}
            >
                {isDetecting ? 'Stop Monitoring' : 'Start Scanning'}
            </button>

            <p className="text-sm text-gray-500 mt-4 text-center max-w-md font-medium">
                Point your camera at traffic signs to detect damage or visibility issues.
            </p>

            <button
                onClick={onBack}
                className="mt-6 text-gray-500 hover:text-gray-800 underline font-bold uppercase tracking-wider text-xs"
            >
                Return to Dashboard
            </button>
        </div>
    );
};

export default TrafficSignDetector;
