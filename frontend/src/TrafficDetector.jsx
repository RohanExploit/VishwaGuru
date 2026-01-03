import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, AlertTriangle, CheckCircle, RotateCcw } from 'lucide-react';

const TrafficDetector = ({ onBack }) => {
  const webcamRef = useRef(null);
  const [image, setImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [detections, setDetections] = useState([]);
  const [error, setError] = useState(null);

  // Get API URL from environment variable
  const API_URL = import.meta.env.VITE_API_URL || '';

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
    detectTrafficViolation(imageSrc);
  }, [webcamRef]);

  const detectTrafficViolation = async (imageSrc) => {
    setAnalyzing(true);
    setError(null);
    setDetections([]);

    try {
      // Convert base64 to blob
      const res = await fetch(imageSrc);
      const blob = await res.blob();
      const file = new File([blob], "traffic_check.jpg", { type: "image/jpeg" });

      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/detect-traffic`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setDetections(data.detections || []);
    } catch (err) {
      console.error("Error detecting traffic violation:", err);
      setError("Failed to analyze image. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const reset = () => {
    setImage(null);
    setDetections([]);
    setError(null);
  };

  const videoConstraints = {
    width: 720,
    height: 720,
    facingMode: "environment"
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center mb-4">
        {onBack && (
          <button onClick={onBack} className="mr-4 text-blue-600 font-medium">
            &larr; Back
          </button>
        )}
        <h2 className="text-xl font-bold text-gray-800">Traffic Violation Detector</h2>
      </div>

      <div className="flex-1 flex flex-col items-center bg-gray-50 rounded-xl p-4 overflow-y-auto">
        {!image ? (
          <div className="relative w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden shadow-lg">
             <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="w-full h-full object-cover"
            />
            <button
              onClick={capture}
              className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-full p-4 shadow-xl border-4 border-blue-500 active:scale-95 transition"
            >
              <Camera size={32} className="text-blue-600" />
            </button>
            <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
              Live Camera
            </div>
          </div>
        ) : (
          <div className="w-full max-w-md">
            <div className="relative rounded-lg overflow-hidden shadow-lg mb-4">
              <img src={image} alt="Captured" className="w-full" />
              {analyzing && (
                <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center text-white">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-2"></div>
                  <p>Analyzing Traffic Scene...</p>
                </div>
              )}
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg flex items-center gap-2 mb-4">
                <AlertTriangle size={18} />
                <span>{error}</span>
              </div>
            )}

            {!analyzing && !error && detections.length === 0 && (
              <div className="bg-green-50 text-green-700 p-4 rounded-lg flex items-center gap-2 mb-4">
                <CheckCircle size={20} />
                <span className="font-medium">No obvious violation detected.</span>
              </div>
            )}

            {!analyzing && detections.length > 0 && (
              <div className="bg-white border border-red-100 rounded-lg p-4 shadow-sm mb-4">
                <h3 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                  <AlertTriangle size={18} />
                  Detected Violations:
                </h3>
                <ul className="space-y-2">
                  {detections.map((det, index) => (
                    <li key={index} className="flex justify-between items-center border-b border-gray-50 last:border-0 pb-1 last:pb-0">
                      <span className="capitalize text-gray-800">{det.label}</span>
                      <span className="text-sm font-bold text-red-600">
                        {Math.round(det.confidence * 100)}%
                      </span>
                    </li>
                  ))}
                </ul>
                 <p className="text-xs text-gray-500 mt-3 italic">
                  * Note: AI detection may not be 100% accurate. Verify before reporting.
                </p>
              </div>
            )}

            <button
              onClick={reset}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition shadow-md"
            >
              <RotateCcw size={20} />
              Check Another
            </button>
          </div>
        )}

        <div className="mt-6 text-sm text-gray-500 text-center max-w-xs">
          <p>Detects: Illegal Parking, Blocked Driveways, Double Parking, Blocked Roads.</p>
        </div>
      </div>
    </div>
  );
};

export default TrafficDetector;
