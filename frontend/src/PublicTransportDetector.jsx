import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const PublicTransportDetector = ({ onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);

    const startCamera = async () => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
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

    const drawDetections = (detections, context) => {
        context.clearRect(0, 0, context.canvas.width, context.canvas.height);
        context.font = 'bold 16px sans-serif';

        detections.forEach((det, index) => {
            const label = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
            const textWidth = context.measureText(label).width;

            const yPos = 60 + (index * 60);

            context.fillStyle = '#FFFFFF';
            context.fillRect(20, yPos - 35, textWidth + 30, 40);

            context.fillStyle = det.label.includes('damage') || det.label.includes('graffiti') ? '#DC2626' : '#2563EB';
            context.fillRect(20, yPos - 35, 6, 40);

            context.fillStyle = '#111827';
            context.fillText(label, 35, yPos - 10);
        });
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
                const response = await fetch(`${API_URL}/api/detect-public-transport`, {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.detections) {
                        drawDetections(data.detections, context);
                    }
                }
            } catch (err) {
                console.error("Detection error:", err);
            }
        }, 'image/jpeg', 0.8);
    };

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

    return (
        <div className="flex flex-col h-full bg-blue-900 text-white">
            <div className="p-4 flex items-center justify-between bg-blue-800 shadow-md z-10">
                <button onClick={onBack} className="text-white/80 font-bold flex items-center text-sm">
                    &larr; Back
                </button>
                <h2 className="text-lg font-bold tracking-tight">Transport Inspector</h2>
                <div className="w-8"></div>
            </div>

            <div className="relative flex-grow flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-blue-900 to-indigo-900">
                {error && <div className="absolute top-4 left-4 right-4 bg-red-500 text-white p-3 rounded z-20 text-center text-sm">{error}</div>}

                <div className="relative w-full h-full max-w-lg md:aspect-video md:h-auto bg-black md:rounded-lg overflow-hidden shadow-2xl">
                     <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover"
                        style={{ opacity: isDetecting ? 1 : 0.5 }}
                    />
                    <canvas
                        ref={canvasRef}
                        className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    />
                    {!isDetecting && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                            <button
                                onClick={() => setIsDetecting(true)}
                                className="px-8 py-3 bg-white text-blue-900 rounded-lg font-black uppercase tracking-wider text-sm shadow-xl transform hover:scale-105 transition-all"
                            >
                                Start Inspection
                            </button>
                        </div>
                    )}
                </div>

                <div className="absolute bottom-8 px-6 text-center max-w-md pointer-events-none">
                     <p className="text-blue-100 text-xs font-medium bg-blue-900/50 backdrop-blur px-4 py-2 rounded-lg inline-block border border-blue-500/30">
                        Check bus stops and facilities for damage or vandalism
                     </p>
                     <div className="pointer-events-auto mt-4">
                        {isDetecting && (
                            <button
                                onClick={() => setIsDetecting(false)}
                                className="px-6 py-2 bg-red-600 text-white rounded-lg text-sm font-bold shadow-md hover:bg-red-700 transition-colors"
                            >
                                Stop
                            </button>
                        )}
                     </div>
                </div>
            </div>
        </div>
    );
};

export default PublicTransportDetector;
