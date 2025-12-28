import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, X, RefreshCw, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const CivicEye = ({ onBack }) => {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setImgSrc(null);
    setResult(null);
    setError(null);
  };

  const analyzeImage = async () => {
    if (!imgSrc) return;

    setAnalyzing(true);
    setError(null);

    try {
      // Convert base64 to blob
      const res = await fetch(imgSrc);
      const blob = await res.blob();
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });

      const formData = new FormData();
      formData.append("image", file);

      const response = await fetch(`${API_URL}/api/analyze-issue`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis service unreachable');
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to analyze image. Please try again or check your internet connection.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack} className="text-gray-600 hover:text-gray-900 flex items-center gap-1">
          <X size={20} /> Close
        </button>
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
           <Camera className="text-blue-500" /> Civic Eye
        </h2>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg mb-4 text-sm text-blue-800">
        Point your camera at a civic issue (e.g., Pothole, Garbage, Broken Light). AI will identify it!
      </div>

      <div className="flex-1 flex flex-col items-center justify-center bg-black rounded-xl overflow-hidden relative min-h-[300px]">
        {imgSrc ? (
          <img src={imgSrc} alt="captured" className="w-full h-full object-contain" />
        ) : (
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            className="w-full h-full object-cover"
            videoConstraints={{ facingMode: "environment" }}
          />
        )}

        {analyzing && (
          <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-2"></div>
            <p>Analyzing Image...</p>
          </div>
        )}
      </div>

      <div className="mt-4 space-y-3">
        {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded flex items-center gap-2">
                <AlertCircle size={18} /> {error}
            </div>
        )}

        {result && (
            <div className="bg-white border rounded-xl p-4 shadow-sm animate-fade-in">
                <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
                    <CheckCircle className="text-green-500" size={20} />
                    {result.label}
                </h3>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                    <div
                        className="bg-green-500 h-2.5 rounded-full"
                        style={{ width: `${Math.round(result.confidence * 100)}%` }}
                    ></div>
                </div>
                <p className="text-xs text-gray-500 mb-3">Confidence: {Math.round(result.confidence * 100)}%</p>

                {result.all_predictions && (
                    <div className="text-xs text-gray-400">
                        Other possibilities: {result.all_predictions.slice(1).map(p => p.label).join(", ")}
                    </div>
                )}
            </div>
        )}

        <div className="flex gap-3">
            {!imgSrc ? (
                <button
                    onClick={capture}
                    className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
                >
                    <Camera size={20} /> Capture
                </button>
            ) : (
                <>
                    <button
                        onClick={retake}
                        className="flex-1 bg-gray-200 text-gray-800 py-3 rounded-xl font-semibold hover:bg-gray-300 transition flex items-center justify-center gap-2"
                    >
                        <RefreshCw size={20} /> Retake
                    </button>
                    {!result && (
                         <button
                            onClick={analyzeImage}
                            disabled={analyzing}
                            className="flex-1 bg-green-600 text-white py-3 rounded-xl font-semibold hover:bg-green-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            <ArrowRight size={20} /> Analyze
                        </button>
                    )}
                </>
            )}
        </div>
      </div>
    </div>
  );
};

export default CivicEye;
