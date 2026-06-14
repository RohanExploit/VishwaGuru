import React, { useRef, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const GenericDetector = ({ apiEndpoint, title, instructions, onBack }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isDetecting, setIsDetecting] = useState(false);
    const [error, setError] = useState(null);
    const [lastDetections, setLastDetections] = useState([]);

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

    const drawDetections = (detections, context) => {
        context.clearRect(0, 0, context.canvas.width, context.canvas.height);

        if (!detections || detections.length === 0) return;

        // Check if we have boxes
        const hasBoxes = detections.some(d => d.box && d.box.length === 4);

        if (hasBoxes) {
            context.strokeStyle = '#00FF00'; // Green
            context.lineWidth = 4;
            context.font = 'bold 18px Arial';
            context.fillStyle = '#00FF00';

            detections.forEach(det => {
                if (det.box && det.box.length === 4) {
                    const [x1, y1, x2, y2] = det.box;
                    context.strokeRect(x1, y1, x2 - x1, y2 - y1);

                    // Draw label background
                    const label = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
                    const textWidth = context.measureText(label).width;
                    context.fillStyle = 'rgba(0,0,0,0.5)';
                    context.fillRect(x1, y1 > 20 ? y1 - 25 : y1, textWidth + 10, 25);

                    context.fillStyle = '#00FF00';
                    context.fillText(label, x1 + 5, y1 > 20 ? y1 - 7 : y1 + 18);
                }
            });
        } else {
            // If no boxes (e.g., Zero-Shot Classification), display top result as overlay
            // We use state to render this in React instead of Canvas for better styling
            setLastDetections(detections);
        }
    };

    const detectFrame = async () => {
        if (!videoRef.current || !canvasRef.current || !isDetecting) return;

        const video = videoRef.current;

        // Wait until video is ready
        if (video.readyState !== 4) return;

        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        // Set canvas dimensions to match video
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        }

        // 1. Draw clean video frame (optional if we want to process it, but usually we just need the blob)
        // We don't draw the video on canvas because the video element is visible behind it.
        // We draw detections ON TOP of the video.
        // But we DO need to draw the frame to a canvas to get the blob.
        // Let's use a separate offscreen canvas or just draw temporarily?
        // Actually, PotholeDetector draws the video to the canvas, then draws detections.
        // But the video element is also visible?
        // In PotholeDetector:
        // <video ... style={{ opacity: isDetecting ? 1 : 0.5 }} />
        // <canvas ... className="absolute top-0 left-0" />
        // The canvas is transparent overlay.
        // But detectFrame does: context.drawImage(video, 0, 0...)
        // This overwrites the transparent canvas with the video frame!
        // So the user sees the canvas (video + boxes) on top of the video element.
        // This is fine.

        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // 2. Capture this frame for API
        canvas.toBlob(async (blob) => {
            if (!blob) return;

            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                const response = await fetch(`${API_URL}${apiEndpoint}`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    // If detections is wrapped in an object
                    const detections = data.detections || (Array.isArray(data) ? data : []);
                    drawDetections(detections, context);
                    setLastDetections(detections);
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
            interval = setInterval(detectFrame, 2000); // Check every 2 seconds
        } else {
            stopCamera();
            setLastDetections([]);
            if (interval) clearInterval(interval);
            // Clear canvas when stopping
            if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            }
        }
        return () => {
            stopCamera();
            if (interval) clearInterval(interval);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isDetecting, apiEndpoint]);

    return (
        <div className="mt-6 flex flex-col items-center w-full h-full">
            <h2 className="text-xl font-semibold mb-4 text-center">{title}</h2>

            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

            <div className="relative w-full max-w-md bg-black rounded-lg overflow-hidden shadow-lg mb-6 aspect-[4/3]">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover absolute inset-0"
                    style={{ opacity: isDetecting ? 0 : 1 }} // Hide video element when detecting, show canvas instead? Or keep both?
                    // Actually, if we draw video on canvas, we should hide the video element or put canvas on top.
                    // If we hide video, we can't capture from it easily if it's display:none.
                    // Opacity 0 is better.
                />
                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                />

                {/* Overlay for Zero-Shot Classification Results (No Boxes) */}
                {isDetecting && lastDetections.length > 0 && !lastDetections.some(d => d.box && d.box.length === 4) && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-4 text-white">
                        <h3 className="font-bold text-lg mb-2">Detected:</h3>
                        <div className="flex flex-wrap gap-2">
                            {lastDetections.slice(0, 3).map((det, idx) => (
                                <span key={idx} className="bg-blue-600 px-2 py-1 rounded text-sm">
                                    {det.label} ({(det.confidence * 100).toFixed(0)}%)
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {!isDetecting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                        <p className="text-white font-medium bg-black/50 px-4 py-2 rounded backdrop-blur-sm">
                            Camera Paused
                        </p>
                    </div>
                )}
            </div>

            <button
                onClick={() => setIsDetecting(!isDetecting)}
                className={`w-full max-w-md py-3 px-4 rounded-lg text-white font-medium shadow-md transition transform active:scale-95 ${isDetecting ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {isDetecting ? 'Stop Detection' : 'Start Live Detection'}
            </button>

            <p className="text-sm text-gray-500 mt-4 text-center max-w-md px-4">
                {instructions || "Point your camera at the scene. Detections will appear in real-time."}
            </p>

            {onBack && (
                <button
                    onClick={onBack}
                    className="mt-6 text-gray-600 hover:text-gray-900 underline"
                >
                    Back to Home
                </button>
            )}
        </div>
    );
};

export default GenericDetector;
