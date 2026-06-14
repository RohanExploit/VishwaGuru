import React, { useState, useRef } from 'react';
import { Camera, Upload, CheckCircle, XCircle, Loader2, Brush } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

// Safe label mapping to prevent XSS and ensure clean UI text
const getSafeLabel = (rawLabel) => {
    if (!rawLabel) return "Unknown Status";
    const lower = rawLabel.toLowerCase();

    if (lower.includes("clean")) return "Clean Wall";
    if (lower.includes("freshly")) return "Freshly Painted";
    if (lower.includes("graffiti")) return "Graffiti Detected";
    if (lower.includes("vandalism")) return "Vandalism Detected";
    if (lower.includes("dirty")) return "Dirty Wall";

    return "Unknown Status";
};

const GraffitiVerification = ({ onBack }) => {
    const fileInputRef = useRef(null);
    const [image, setImage] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFile = async (file) => {
        if (!file) return;

        // Simple sanitization of filename (though createObjectURL handles blob securely)
        const safeName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_');

        try {
             const url = URL.createObjectURL(file);
             setImage(url);
        } catch (e) {
             console.error("Error creating object URL", e);
             return;
        }

        setResult(null);
        setLoading(true);

        const formData = new FormData();
        formData.append('image', file, safeName);

        try {
            const res = await fetch(`${API_URL}/api/detect-cleanliness`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                if (data.detections && data.detections.length > 0) {
                    const detection = data.detections[0];
                    // Map raw label to safe, hardcoded string
                    const displayLabel = getSafeLabel(detection.label);
                    setResult({ ...detection, label: displayLabel });
                } else {
                    setResult({ label: "Unable to determine", confidence: 0 });
                }
            }
        } catch (e) {
            console.error("Verification failed", e);
        } finally {
            setLoading(false);
        }
    };

    const triggerCamera = () => {
        if (fileInputRef.current) fileInputRef.current.click();
    };

    return (
        <div className="flex flex-col items-center p-4 max-w-md mx-auto w-full min-h-screen bg-gray-50">
            <div className="w-full bg-white rounded-2xl shadow-sm p-6 mb-6 text-center">
                <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600">
                    <Brush size={32} />
                </div>
                <h2 className="text-xl font-bold text-gray-800">Graffiti Removal Verification</h2>
                <p className="text-gray-500 text-sm mt-2">Upload a photo to verify if a wall is clean or still has graffiti.</p>
            </div>

            <div className="w-full aspect-square bg-white rounded-2xl shadow-sm border-2 border-dashed border-gray-200 flex flex-col items-center justify-center relative overflow-hidden group hover:border-blue-400 transition-colors cursor-pointer" onClick={triggerCamera}>
                {image ? (
                    <img src={image} alt="Preview" className="w-full h-full object-cover" />
                ) : (
                    <div className="text-center p-6">
                        <Camera size={48} className="mx-auto text-gray-300 mb-2 group-hover:text-blue-400 transition-colors" />
                        <span className="text-gray-400 font-medium group-hover:text-blue-500">Tap to Take Photo</span>
                    </div>
                )}

                <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    ref={fileInputRef}
                    onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                            handleFile(e.target.files[0]);
                        }
                    }}
                />

                {loading && (
                    <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center backdrop-blur-sm">
                        <Loader2 className="animate-spin text-blue-600 mb-2" size={32} />
                        <span className="text-blue-600 font-medium">Analyzing cleanliness...</span>
                    </div>
                )}
            </div>

            {result && !loading && (
                <div className={`w-full mt-6 p-6 rounded-2xl shadow-sm border-l-8 flex items-start gap-4 ${
                    result.label.includes('Clean') || result.label.includes('Freshly')
                        ? 'bg-green-50 border-green-500 text-green-800'
                        : 'bg-red-50 border-red-500 text-red-800'
                }`}>
                    {result.label.includes('Clean') || result.label.includes('Freshly') ? (
                        <CheckCircle className="shrink-0" size={24} />
                    ) : (
                        <XCircle className="shrink-0" size={24} />
                    )}
                    <div>
                        {/* Label is safe because it comes from getSafeLabel which returns hardcoded strings */}
                        <h3 className="font-bold text-lg capitalize">{result.label}</h3>
                        <p className="opacity-80 text-sm mt-1">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                        <p className="text-xs mt-2 font-medium uppercase tracking-wide opacity-70">
                            {result.label.includes('Clean') || result.label.includes('Freshly') ? 'Verification Passed' : 'Action Required'}
                        </p>
                    </div>
                </div>
            )}

            <button onClick={onBack} className="mt-auto py-6 text-gray-500 font-medium hover:text-gray-800">
                Back to Dashboard
            </button>
        </div>
    );
};

export default GraffitiVerification;
