import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, RefreshCw, ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BaseDetector = ({ title, apiCall, detectionName, onBack }) => {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) onBack();
    else navigate('/');
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
    setError(null);
  }, [webcamRef]);

  const retake = () => {
    setImgSrc(null);
    setDetections([]);
    setError(null);
  };

  const detect = async () => {
    if (!imgSrc) return;
    setLoading(true);
    setError(null);
    setDetections([]);

    try {
        const res = await fetch(imgSrc);
        const blob = await res.blob();
        const file = new File([blob], "image.jpg", { type: "image/jpeg" });
        const formData = new FormData();
        formData.append('image', file);

        const data = await apiCall(formData);
        // Normalize response: expected { detections: [...] } or direct array or object
        let results = [];
        if (Array.isArray(data)) results = data;
        else if (data && data.detections) results = data.detections;
        else if (data && data.label) results = [data]; // Single result like waste
        else if (data && typeof data === 'object' && Object.keys(data).length > 0) {
             // Maybe it's a dict of results?
             results = [data];
        }

        setDetections(results);
        if (results.length === 0) {
            setError(`No ${detectionName || 'issue'} detected.`);
        }
    } catch (err) {
        console.error("Detection Error:", err);
        setError("Analysis failed. Please try again.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white p-4 shadow-sm flex items-center gap-4 sticky top-0 z-10">
        <button onClick={handleBack} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft size={24} className="text-gray-600" />
        </button>
        <h1 className="text-xl font-bold text-gray-800">{title}</h1>
      </div>

      <div className="flex-1 p-4 flex flex-col items-center max-w-md mx-auto w-full">
        {/* Camera/Image Area */}
        <div className="relative w-full aspect-[3/4] bg-black rounded-2xl overflow-hidden shadow-lg mb-6">
            {!imgSrc ? (
              <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                className="w-full h-full object-cover"
                videoConstraints={{ facingMode: 'environment' }}
                onUserMediaError={(e) => setError("Camera access denied. Please check permissions.")}
              />
            ) : (
              <img src={imgSrc} alt="Captured" className="w-full h-full object-cover" />
            )}

            {loading && (
                <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center backdrop-blur-sm text-white">
                    <RefreshCw size={48} className="animate-spin mb-4" />
                    <p className="font-bold text-lg">Analyzing...</p>
                </div>
            )}
        </div>

        {/* Error Message */}
        {error && (
            <div className="w-full bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                <AlertTriangle size={20} />
                <span className="font-medium">{error}</span>
            </div>
        )}

        {/* Results */}
        {detections.length > 0 && !loading && (
            <div className="w-full space-y-3 mb-6 animate-in fade-in slide-in-from-bottom-4">
                <div className="text-sm font-bold text-gray-500 uppercase tracking-wider ml-1">Detections</div>
                {detections.map((det, idx) => (
                    <div key={idx} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-green-100 p-2 rounded-full text-green-600">
                                <CheckCircle size={20} />
                            </div>
                            <div>
                                <p className="font-bold text-gray-800 capitalize">{det.label || det.waste_type || 'Detected'}</p>
                                <p className="text-xs text-gray-500">Confidence: {((det.confidence || det.score || 0) * 100).toFixed(0)}%</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        )}

        {/* Controls */}
        <div className="w-full mt-auto pb-6 space-y-3">
            {!imgSrc ? (
                <button
                    onClick={capture}
                    className="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold text-lg shadow-xl hover:bg-blue-700 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                    <Camera size={24} />
                    Capture Photo
                </button>
            ) : (
                <div className="grid grid-cols-2 gap-4">
                    <button
                        onClick={retake}
                        className="w-full bg-gray-200 text-gray-800 py-4 rounded-2xl font-bold hover:bg-gray-300 transition-colors"
                    >
                        Retake
                    </button>
                    <button
                        onClick={detect}
                        className="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                    >
                        Analyze
                    </button>
                </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default BaseDetector;
