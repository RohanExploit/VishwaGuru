import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const ContentModerator = ({ onBack }) => {
    const videoRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);
    const [detections, setDetections] = useState([]);

    const startCamera = async () => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment', // Back camera typically for analyzing content
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (err) {
            console.warn("Strict camera access failed, trying fallback:", err);
            try {
                // Fallback to any available video camera
                const fallbackStream = await navigator.mediaDevices.getUserMedia({
                    video: true
                });
                if (videoRef.current) {
                    videoRef.current.srcObject = fallbackStream;
                }
            } catch (fallbackErr) {
                setError("Could not access camera: " + fallbackErr.message);
                setIsDetecting(false);
            }
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

    const detectContent = async () => {
        if (!videoRef.current || videoRef.current.readyState !== 4) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            if (!blob) return;
            const formData = new FormData();
            formData.append('image', blob, 'content.jpg');

            try {
                const response = await fetch(`${API_URL}/api/detect-nsfw`, {
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
                console.error("Content moderation detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera().then(() => {
                interval = setInterval(detectContent, 2500); // 2.5 seconds
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
            <h1 className="text-3xl font-extrabold text-blue-800 mb-6 drop-shadow-sm text-center">
                Content Moderation Checker
            </h1>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4 w-full max-w-md">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            <div className="relative w-full max-w-md aspect-video bg-black rounded-xl overflow-hidden shadow-2xl mb-6">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />

                {!isDetecting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40">
                        <p className="text-white font-medium bg-black bg-opacity-50 px-4 py-2 rounded">
                            Camera Paused
                        </p>
                    </div>
                )}
            </div>

            {detections.length > 0 && (
                <div className="w-full max-w-md bg-white p-4 rounded-xl shadow-md mb-6">
                    <h3 className="text-lg font-bold mb-3 text-gray-800 border-b pb-2">Analysis Results</h3>
                    <div className="space-y-3">
                        {detections.map((detection, idx) => (
                            <div key={idx}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium text-gray-700 capitalize">{detection.label}</span>
                                    <span className="text-gray-500">{(detection.score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className={`${detection.label === 'nsfw' ? 'bg-red-600' : 'bg-emerald-500'} h-2 rounded-full transition-all duration-300`}
                                        style={{ width: `${detection.score * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {isDetecting ? 'Stop Camera' : 'Start Camera Check'}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
                Enable camera to analyze visual content against moderation policies in real-time.
            </p>

            <button
                onClick={onBack}
                className="mt-6 text-gray-600 hover:text-gray-900 underline font-semibold"
            >
                Back to Home
            </button>
        </div>
    );
};

export default ContentModerator;
