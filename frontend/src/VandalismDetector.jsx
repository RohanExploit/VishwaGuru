import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const VandalismDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera();
            // Since this API might be slower (External HF API), we poll less frequently
            interval = setInterval(detectFrame, 3000);
        } else {
            stopCamera();
            if (interval) clearInterval(interval);
        }
        return () => {
            stopCamera();
            if (interval) clearInterval(interval);
        };
    }, [isDetecting]);

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

    const detectFrame = async () => {
        if (!videoRef.current || !isDetecting) return;

        const video = videoRef.current;
        if (video.readyState !== 4) return;

        // Create canvas to capture image
        const captureCanvas = document.createElement('canvas');
        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
        const captureCtx = captureCanvas.getContext('2d');
        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        captureCanvas.toBlob(async (blob) => {
            if (!blob) return;

            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                const response = await fetch(`${API_URL}/api/detect-vandalism`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.classification && Array.isArray(data.classification)) {
                         // Get top result
                         const topResult = data.classification[0];
                         setResult(topResult);
                    }
                }
            } catch (err) {
                console.error("Detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

    return (
        <div className="mt-6 flex flex-col items-center w-full">
            <h2 className="text-xl font-semibold mb-4 text-center">Vandalism & Graffiti Scanner</h2>

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

                    {!isDetecting && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <p className="text-white font-medium bg-black bg-opacity-50 px-4 py-2 rounded">
                                Camera Paused
                            </p>
                        </div>
                    )}

                    {isDetecting && result && (
                        <div className="absolute bottom-4 left-4 right-4">
                            <div className="bg-white bg-opacity-90 rounded p-3 shadow">
                                <p className="font-bold text-lg text-gray-800 capitalize">
                                    {result.label}
                                </p>
                                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1">
                                    <div
                                        className={`h-2.5 rounded-full ${result.score > 0.7 ? 'bg-red-600' : 'bg-yellow-500'}`}
                                        style={{ width: `${result.score * 100}%` }}
                                    ></div>
                                </div>
                                <p className="text-xs text-gray-600 mt-1 text-right">
                                    {(result.score * 100).toFixed(1)}% Confidence
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-indigo-600 hover:bg-indigo-700'}`}
            >
                {isDetecting ? 'Stop Scanning' : 'Start Scanning'}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
                Point at walls or public property to detect graffiti or vandalism.
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

export default VandalismDetector;
