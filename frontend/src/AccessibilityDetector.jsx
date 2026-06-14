import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const AccessibilityDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let interval;
        if (isDetecting) {
            startCamera();
            interval = setInterval(detectFrame, 2000);
        } else {
            stopCamera();
            if (interval) clearInterval(interval);
            if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            }
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
        if (!videoRef.current || !canvasRef.current || !isDetecting) return;

        const video = videoRef.current;
        if (video.readyState !== 4) return;

        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        }

        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            if (!blob) return;

            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                const response = await fetch(`${API_URL}/api/detect-accessibility`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    drawDetections(data.detections, context);
                }
            } catch (err) {
                console.error("Detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

    const drawDetections = (detections, context) => {
        context.clearRect(0, 0, context.canvas.width, context.canvas.height);

        detections.forEach((det, index) => {
             // Zero-shot detection (no box)
             context.font = 'bold 20px Arial';
             context.fillStyle = 'rgba(138, 43, 226, 0.8)'; // BlueViolet
             const label = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
             const textWidth = context.measureText(label).width;

             const yPos = 40 + (index * 50);
             context.fillRect(10, yPos - 30, textWidth + 20, 40);
             context.fillStyle = '#FFFFFF';
             context.fillText(label, 20, yPos - 4);
        });
    };

    return (
        <div className="mt-6 flex flex-col items-center w-full">
            <h2 className="text-xl font-semibold mb-4 text-center">Accessibility Barrier Detector</h2>

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
                        className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    />
                    {!isDetecting && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <p className="text-white font-medium bg-black bg-opacity-50 px-4 py-2 rounded">
                                Camera Paused
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {isDetecting ? 'Stop Detection' : 'Start Live Detection'}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
                Detects blocked ramps and accessibility issues.
            </p>

            <button onClick={onBack} className="mt-6 text-gray-600 hover:text-gray-900 underline">
                Back to Home
            </button>
        </div>
    );
};

export default AccessibilityDetector;
