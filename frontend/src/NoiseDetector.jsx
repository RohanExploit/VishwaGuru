import React, { useRef, useState, useEffect } from 'react';
import { Mic, MicOff, AlertCircle, Volume2, AlertTriangle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const NoiseDetector = ({ onBack }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [detections, setDetections] = useState([]);
    const [error, setError] = useState(null);
    const [status, setStatus] = useState('Ready');
    const intervalRef = useRef(null);
    const streamRef = useRef(null);

    useEffect(() => {
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

            recordAndSend();
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
            const response = await fetch(`${API_URL}/api/detect-noise-pollution`, {
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

    const hasPollution = detections.some(d => d.is_pollution);

    return (
        <div className="flex flex-col items-center w-full max-w-md mx-auto p-4 min-h-screen bg-gray-50">
            <h2 className="text-xl font-bold mb-6 text-gray-800 flex items-center gap-2">
                <Volume2 className="text-blue-600" />
                Noise Pollution Monitor
            </h2>

            <div className={`relative w-48 h-48 rounded-full flex items-center justify-center mb-8 transition-all duration-500 ${isRecording ? 'bg-white shadow-xl ring-8 ring-blue-50' : 'bg-gray-100'}`}>
                {isRecording && (
                    <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
                )}
                {isRecording ? <Mic size={64} className="text-blue-500" /> : <MicOff size={64} className="text-gray-400" />}

                {hasPollution && isRecording && (
                     <div className="absolute -top-2 -right-2 bg-red-500 text-white p-2 rounded-full animate-bounce shadow-lg">
                        <AlertTriangle size={24} />
                     </div>
                )}
            </div>

            <div className="w-full bg-white rounded-2xl shadow-sm p-6 mb-6 min-h-[160px]">
                <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest">Live Analysis</h3>

                {detections.length > 0 ? (
                    <div className="space-y-3">
                        {detections.map((det, idx) => (
                            <div key={idx} className={`flex items-center justify-between p-3 rounded-xl ${det.is_pollution ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-600'}`}>
                                <div className="flex items-center gap-3">
                                    {det.is_pollution ? <AlertTriangle size={16} /> : <Volume2 size={16} />}
                                    <span className="font-semibold capitalize">{det.type}</span>
                                </div>
                                <span className="text-sm font-bold opacity-70">{(det.confidence * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-300 py-8">
                        <p>{isRecording ? "Listening..." : "Tap Start to monitor noise levels"}</p>
                    </div>
                )}
            </div>

            {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm mb-4 bg-red-50 p-3 rounded-xl w-full">
                    <AlertCircle size={16} />
                    {error}
                </div>
            )}

            <button
                onClick={() => setIsRecording(!isRecording)}
                className={`w-full py-4 rounded-xl text-white font-bold shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2 ${isRecording ? 'bg-red-500 hover:bg-red-600 shadow-red-200' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'}`}
            >
                {isRecording ? 'Stop Monitoring' : 'Start Monitoring'}
            </button>

             <button
                onClick={onBack}
                className="mt-6 text-gray-500 hover:text-gray-800 text-sm font-medium transition"
            >
                Back to Dashboard
            </button>
        </div>
    );
};

export default NoiseDetector;
