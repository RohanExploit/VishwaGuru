import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { detectorsApi } from './api/detectors';
import { useNavigate } from 'react-router-dom';

const PlaygroundDetector = ({ onBack }) => {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const navigate = useNavigate();

  const videoConstraints = {
    width: 720,
    height: 720,
    facingMode: "environment"
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setImgSrc(null);
    setDetections([]);
    setCameraError(null);
  };

  const detectDamage = async () => {
    if (!imgSrc) return;
    setLoading(true);
    setDetections([]);

    try {
        // Convert base64 to blob
        const res = await fetch(imgSrc);
        const blob = await res.blob();
        const file = new File([blob], "image.jpg", { type: "image/jpeg" });

        const formData = new FormData();
        formData.append('image', file);

        // Call Backend API
        const data = await detectorsApi.playgroundDamage(formData);

        if (data.detections && data.detections.length > 0) {
            setDetections(data.detections);
        } else {
            alert("No damage detected. Looks safe!");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred during detection.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 p-4">
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack || (() => navigate('/'))} className="text-green-600 font-bold flex items-center">
           &larr; Back
        </button>
        <h2 className="text-xl font-bold text-gray-800">Playground Safety</h2>
        <div className="w-8"></div>
      </div>

      <div className="flex-grow flex flex-col items-center justify-center relative bg-black rounded-3xl overflow-hidden shadow-xl mb-6">
          {cameraError ? (
             <div className="text-white text-center p-6">
                 <p className="text-red-400 font-bold mb-2">Camera Error</p>
                 <p className="text-sm">{cameraError}</p>
                 <button onClick={() => window.location.reload()} className="mt-4 bg-white text-black px-4 py-2 rounded-full text-sm">Retry</button>
             </div>
          ) : !imgSrc ? (
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="absolute inset-0 w-full h-full object-cover"
              onUserMediaError={(err) => setCameraError("Camera access denied. Please check permissions.")}
            />
          ) : (
            <div className="relative w-full h-full">
               <img src={imgSrc} alt="Captured" className="w-full h-full object-cover" />
               {detections.length > 0 && (
                 <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white p-4 backdrop-blur-md">
                    <h3 className="font-bold text-orange-400 mb-2 uppercase tracking-wider text-xs">Issues Detected:</h3>
                    <ul className="space-y-1">
                        {detections.map((d, idx) => (
                            <li key={idx} className="flex justify-between text-sm font-medium">
                                <span>{d.label}</span>
                                <span className="text-gray-400">{(d.confidence * 100).toFixed(0)}%</span>
                            </li>
                        ))}
                    </ul>
                 </div>
               )}
            </div>
          )}
      </div>

      <div className="flex justify-center gap-4 mb-4">
        {!imgSrc ? (
           <button
             onClick={capture}
             className="w-20 h-20 rounded-full bg-white border-4 border-gray-200 shadow-lg flex items-center justify-center active:scale-95 transition-transform"
           >
               <div className="w-16 h-16 rounded-full bg-green-600"></div>
           </button>
        ) : (
           <>
             <button
                onClick={retake}
                className="px-6 py-3 rounded-xl bg-gray-200 text-gray-800 font-bold shadow-sm"
             >
                Retake
             </button>
             <button
                onClick={detectDamage}
                disabled={loading}
                className="px-6 py-3 rounded-xl bg-green-600 text-white font-bold shadow-lg flex items-center gap-2"
             >
                {loading ? 'Scanning...' : 'Scan Equipment'}
             </button>
           </>
        )}
      </div>

      <p className="text-center text-xs text-gray-400">
          Detects: Broken swings, damaged slides, rusty equipment.
      </p>
    </div>
  );
};

export default PlaygroundDetector;
