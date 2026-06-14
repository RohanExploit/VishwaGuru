import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const AirQualityDetector = ({ onBack }) => {
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
            // Zero-shot detection (no box)
            const label = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
            const textWidth = context.measureText(label).width;

            const yPos = 60 + (index * 60);

            // Draw background pill
            context.fillStyle = 'rgba(255, 255, 255, 0.85)';
            context.beginPath();
            context.roundRect(20, yPos - 35, textWidth + 30, 40, 20);
            context.fill();

            // Draw status indicator dot
            context.fillStyle = det.label.includes('clear') || det.label.includes('safe') ? '#10B981' : '#EF4444';
            context.beginPath();
            context.arc(40, yPos - 15, 6, 0, 2 * Math.PI);
            context.fill();

            // Draw Text
            context.fillStyle = '#1F2937';
            context.fillText(label, 55, yPos - 10);
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
                const response = await fetch(`${API_URL}/api/detect-air-quality`, {
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
        <div className="flex flex-col h-full bg-slate-900 text-white">
            <div className="p-4 flex items-center justify-between bg-slate-800 shadow-md z-10">
                <button onClick={onBack} className="text-blue-400 font-bold flex items-center text-sm">
                    &larr; Back
                </button>
                <h2 className="text-lg font-bold tracking-tight">Air Quality Monitor</h2>
                <div className="w-8"></div>
            </div>

            <div className="relative flex-grow flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-slate-900 to-slate-800">
                {error && <div className="absolute top-4 left-4 right-4 bg-red-500/90 backdrop-blur text-white p-3 rounded-xl z-20 text-center text-sm font-medium">{error}</div>}

                <div className="relative w-full h-full max-w-lg md:aspect-video md:h-auto bg-black md:rounded-2xl overflow-hidden shadow-2xl">
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
                                className="px-8 py-4 bg-blue-600 hover:bg-blue-500 rounded-full font-bold text-lg shadow-lg shadow-blue-600/30 transform hover:scale-105 transition-all flex items-center gap-3"
                            >
                                <span className="relative flex h-3 w-3">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-3 w-3 bg-sky-500"></span>
                                </span>
                                Start Monitoring
                            </button>
                        </div>
                    )}
                </div>

                <div className="absolute bottom-8 px-6 text-center max-w-md pointer-events-none">
                     <p className="text-slate-300 text-xs font-medium bg-black/40 backdrop-blur px-4 py-2 rounded-full inline-block">
                        Detects smog, smoke, and air pollution levels visually
                     </p>
                     <div className="pointer-events-auto mt-4">
                        {isDetecting && (
                            <button
                                onClick={() => setIsDetecting(false)}
                                className="px-6 py-2 bg-red-500/20 text-red-200 border border-red-500/50 rounded-full text-sm font-bold hover:bg-red-500/30 transition-colors"
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

export default AirQualityDetector;
