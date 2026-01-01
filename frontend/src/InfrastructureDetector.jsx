import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, RefreshCw, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

const InfrastructureDetector = ({ onBack }) => {
  const webcamRef = useRef(null);
  const [imageSrc, setImageSrc] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState(false);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImageSrc(imageSrc);
    detectInfrastructure(imageSrc);
  }, [webcamRef]);

  const detectInfrastructure = async (base64Image) => {
    setLoading(true);
    try {
      // Convert base64 to blob
      const res = await fetch(base64Image);
      const blob = await res.blob();
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });

      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/detect-infrastructure`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Detection failed');

      const data = await response.json();
      if (data.error) {
          throw new Error(data.error);
      }
      setDetections(data.detections);
    } catch (error) {
      console.error("Error detecting infrastructure issues:", error);
      alert(`Failed to analyze image: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setImageSrc(null);
    setDetections([]);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <button onClick={onBack} className="text-blue-600 flex items-center gap-1">
          &larr; Back
        </button>
        <h2 className="text-xl font-bold text-gray-800">Infra Damage Detector</h2>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center bg-black rounded-xl overflow-hidden relative min-h-[300px]">
        {imageSrc ? (
          <img src={imageSrc} alt="Captured" className="w-full h-full object-contain" />
        ) : (
          !cameraError ? (
             <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="w-full h-full object-cover"
              videoConstraints={{ facingMode: "environment" }}
              onUserMediaError={() => setCameraError(true)}
            />
          ) : (
            <div className="text-white text-center p-4">
               <p className="mb-2">Camera access failed.</p>
               <p className="text-sm text-gray-400">Please check permissions.</p>
            </div>
          )
        )}

        {loading && (
          <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-2"></div>
            <p>Analyzing Infrastructure...</p>
          </div>
        )}
      </div>

      <div className="mt-4 space-y-3">
        {!imageSrc ? (
          <button
            onClick={capture}
            disabled={cameraError}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold shadow-lg hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Camera size={20} />
            Capture & Analyze
          </button>
        ) : (
          <button
            onClick={reset}
            className="w-full py-3 bg-gray-600 text-white rounded-xl font-semibold shadow-lg hover:bg-gray-700 transition flex items-center justify-center gap-2"
          >
            <RefreshCw size={20} />
            Retake
          </button>
        )}

        {detections.length > 0 ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <h3 className="text-red-800 font-bold mb-2 flex items-center gap-2">
              <AlertTriangle size={18} />
              Damage Detected!
            </h3>
            <ul className="space-y-1">
              {detections.map((det, idx) => (
                <li key={idx} className="text-red-700 flex justify-between">
                  <span className="capitalize">{det.label}</span>
                  <span className="text-sm opacity-75">{(det.confidence * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
             <p className="text-xs text-red-600 mt-2">
               Please report this issue using the Report Issue form for immediate action.
            </p>
          </div>
        ) : (
          imageSrc && !loading && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
              <CheckCircle className="text-green-600" size={24} />
              <div>
                 <h3 className="text-green-800 font-bold">No Damage Detected</h3>
                 <p className="text-green-700 text-sm">Infrastructure appears normal.</p>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default InfrastructureDetector;
