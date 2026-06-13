import React, { useRef, useState, useEffect } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const NoiseDetector = ({ onBack }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [detections, setDetections] = useState([]);
    const [error, setError] = useState(null);
    const [status, setStatus] = useState('Ready');
    const intervalRef = useRef(null);
    const streamRef = useRef(null);

    useEffect(() => {
        // Cleanup on unmount
        return () => {
            stopRecording();
        };
    }, []);

    useEffect(() => {
        if (isRecording) {
            startLoop();
        } else {
            stopLoop();
        }
    }, [isRecording]);

    const startLoop = async () => {
        setError(null);
        setStatus('Initializing...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const recordAndSend = () => {
                if (!streamRef.current) return;

                try {
                    const recorder = new MediaRecorder(streamRef.current);
                    const chunks = [];

                    recorder.ondataavailable = e => {
                        if (e.data.size > 0) chunks.push(e.data);
                    };

                    recorder.onstop = () => {
                        if (chunks.length > 0) {
                            const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
                            sendAudio(blob);
                        }
                    };

                    recorder.start();
                    setStatus('Listening...');

                    // Record for 4 seconds
                    setTimeout(() => {
                        if (recorder.state === 'recording') {
                            recorder.stop();
                        }
                    }, 4000);

                } catch (e) {
                    console.error("Recorder error:", e);
                    setError("Error creating media recorder");
                    setIsRecording(false);
                }
            };

            // Start first immediately
            recordAndSend();
            // Then interval every 5 seconds
            intervalRef.current = setInterval(recordAndSend, 5000);

        } catch (e) {
            console.error("Mic access error:", e);
            setError("Microphone access denied. Please allow microphone permissions.");
            setIsRecording(false);
        }
    };

    const stopLoop = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setStatus('Ready');
    };

    const stopRecording = () => {
        setIsRecording(false);
        stopLoop();
    };

    const sendAudio = async (blob) => {
        setStatus('Analyzing...');
        const formData = new FormData();
        formData.append('file', blob, 'recording.webm');

        try {
            const response = await fetch(`${API_URL}/api/detect-audio`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.detections) {
                     setDetections(data.detections);
                }
                setStatus('Listening...');
            } else {
                console.error("Audio API error");
            }
        } catch (err) {
            console.error("Audio network error", err);
        }
    };

    return (
        <div className="flex flex-col items-center w-full max-w-md mx-auto p-4">
            <h2 className="text-xl font-bold mb-6 text-gray-800">Noise Detector</h2>

            <div className={`w-40 h-40 rounded-full flex items-center justify-center mb-8 transition-all duration-500 ${isRecording ? 'bg-red-50 ring-4 ring-red-100 animate-pulse' : 'bg-gray-50'}`}>
                {isRecording ? <Mic size={64} className="text-red-500" /> : <MicOff size={64} className="text-gray-400" />}
            </div>

            <div className="w-full bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6 min-h-[160px]">
                <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wider">Detected Sounds</h3>

                {detections.length > 0 ? (
                    <div className="space-y-3">
                        {detections.slice(0, 3).map((det, idx) => (
                            <div key={idx} className="flex items-center justify-between">
                                <span className="font-medium text-gray-800 capitalize">{det.label}</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${det.score > 0.7 ? 'bg-red-500' : 'bg-blue-500'}`}
                                            style={{ width: `${det.score * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-mono w-8 text-right">{(det.score * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 text-sm">
                        <p>{isRecording ? "Listening for sounds..." : "Start recording to detect sounds"}</p>
                    </div>
                )}
            </div>

            {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm mb-4 bg-red-50 p-3 rounded-lg w-full">
                    <AlertCircle size={16} />
                    {error}
                </div>
            )}

            <p className="text-center text-sm font-medium text-blue-600 mb-6 h-6">{status}</p>

            <button
                onClick={() => setIsRecording(!isRecording)}
                className={`w-full py-3.5 px-6 rounded-xl text-white font-bold shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2 ${isRecording ? 'bg-red-500 hover:bg-red-600 shadow-red-200' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'}`}
            >
                {isRecording ? 'Stop Monitoring' : 'Start Monitoring'}
            </button>

             <button
                onClick={onBack}
                className="mt-6 text-gray-500 hover:text-gray-800 text-sm font-medium transition"
            >
                Back to Home
            </button>
        </div>
    );
};

export default NoiseDetector;
