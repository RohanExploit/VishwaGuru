import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const EmotionDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);
    const [emotions, setEmotions] = useState([]);

    const startCamera = async () => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user', // Front camera for emotions
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                // Important to ensure the video actually plays when stream is attached
                videoRef.current.play().catch(e => console.error("Video play error:", e));
            }
        } catch (err) {
            setError("Could not access camera. Please ensure permissions are granted. Details: " + err.message);
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

    const detectEmotions = async () => {
        if (!videoRef.current || videoRef.current.readyState !== 4) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            if (!blob) return;
            const formData = new FormData();
            formData.append('image', blob, 'emotion.jpg');

            try {
                const response = await fetch(`${API_URL}/api/detect-emotion`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.emotions && data.emotions.length > 0) {
                        setEmotions(data.emotions);
                    } else {
                        setEmotions([]);
                    }
                }
            } catch (err) {
                console.error("Emotion detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera().then(() => {
                interval = setInterval(detectEmotions, 2000); // 2 seconds
            });
        } else {
            stopCamera();
            setEmotions([]);
        }

        return () => {
            if (interval) clearInterval(interval);
            stopCamera();
        };
    }, [isDetecting]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
            <h1 className="text-3xl font-extrabold text-blue-800 mb-6 drop-shadow-sm text-center">
                Live Emotion Detection
            </h1>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4 w-full max-w-md">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            <div className="relative w-full max-w-md aspect-video bg-black rounded-xl overflow-hidden shadow-2xl mb-6 border-4 border-transparent transition-all duration-300">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }} // Mirror the camera for better UX
                />

                {isDetecting && (
                    <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10 z-10">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"></div>
                        <span className="text-white text-xs font-bold tracking-wider uppercase">Live Feed</span>
                    </div>
                )}

                {!isDetecting && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/90 backdrop-blur-sm z-10 transition-all duration-300">
                        <div className="w-16 h-16 mb-4 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700 shadow-inner">
                            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                        </div>
                        <p className="text-white font-bold tracking-widest uppercase text-sm">
                            Camera Offline
                        </p>
                        <p className="text-gray-400 text-xs mt-2 max-w-[200px] text-center">
                            Press start to begin emotional analysis
                        </p>
                    </div>
                )}
            </div>

            {emotions.length > 0 && (
                <div className="w-full max-w-md bg-white p-4 rounded-xl shadow-md mb-6">
                    <h3 className="text-lg font-bold mb-3 text-gray-800 border-b pb-2">Detected Emotions</h3>
                    <div className="space-y-3">
                        {emotions.map((emotion, idx) => (
                            <div key={idx}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium text-gray-700 capitalize">{emotion.label}</span>
                                    <span className="text-gray-500">{(emotion.score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${emotion.score * 100}%` }}
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
                {isDetecting ? 'Stop Detection' : 'Start Detection'}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
                Enable camera to analyze facial expressions and emotions in real-time.
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

export default EmotionDetector;
