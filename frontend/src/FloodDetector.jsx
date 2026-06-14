import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, X, AlertTriangle, CheckCircle, Droplets } from 'lucide-react';
import { detectorsApi } from './api/detectors';

const FloodDetector = () => {
  const webcamRef = useRef(null);
  const [image, setImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
    analyzeImage(imageSrc);
  }, [webcamRef]);

  const analyzeImage = async (base64Image) => {
    setAnalyzing(true);
    setResult(null);
    setError(null);

    try {
      // Convert base64 to blob
      const res = await fetch(base64Image);
      const blob = await res.blob();
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });

      const formData = new FormData();
      formData.append('image', file);

      const data = await detectorsApi.flooding(formData);
      setResult(data.detections);
    } catch (err) {
      console.error(err);
      setError('Failed to analyze image. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const reset = () => {
    setImage(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="flex flex-col items-center p-4 w-full h-full">
      <h2 className="text-xl font-bold mb-4 text-cyan-800 flex items-center gap-2">
        <Droplets className="text-cyan-600"/> Flooding Detector
      </h2>

      <div className="relative w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden shadow-lg">
        {!image ? (
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            className="w-full h-full object-cover"
            videoConstraints={{ facingMode: "environment" }}
          />
        ) : (
          <img src={image} alt="Captured" className="w-full h-full object-cover" />
        )}

        {analyzing && (
          <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-2"></div>
            <p>Scanning for waterlogging...</p>
          </div>
        )}
      </div>

      <div className="mt-6 w-full max-w-md">
        {!image ? (
          <button
            onClick={capture}
            className="w-full bg-cyan-600 text-white py-3 rounded-xl font-semibold hover:bg-cyan-700 transition flex items-center justify-center gap-2"
          >
            <Camera size={20} />
            Capture Photo
          </button>
        ) : (
          <button
            onClick={reset}
            className="w-full bg-gray-200 text-gray-800 py-3 rounded-xl font-semibold hover:bg-gray-300 transition flex items-center justify-center gap-2"
          >
            <X size={20} />
            Retake
          </button>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="mt-6 w-full max-w-md bg-white p-4 rounded-xl shadow border border-cyan-100">
            {result.length > 0 ? (
                <div>
                     <div className="flex items-center gap-2 text-red-600 font-bold mb-2">
                        <AlertTriangle size={20} />
                        <h3>Waterlogging Detected!</h3>
                     </div>
                     <ul className="space-y-2">
                        {result.map((item, idx) => (
                            <li key={idx} className="bg-red-50 p-2 rounded text-sm flex justify-between">
                                <span className="capitalize font-medium text-red-800">{item.label}</span>
                                <span className="text-red-600">{Math.round(item.confidence * 100)}% Confidence</span>
                            </li>
                        ))}
                     </ul>
                     <p className="text-xs text-gray-500 mt-3">This has been flagged for municipal drainage review.</p>
                </div>
            ) : (
                <div className="flex items-center gap-2 text-green-600 font-bold">
                    <CheckCircle size={20} />
                    <h3>No significant flooding detected.</h3>
                </div>
            )}
        </div>
      )}

      {error && (
        <div className="mt-4 text-red-600 bg-red-50 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
};

export default FloodDetector;
