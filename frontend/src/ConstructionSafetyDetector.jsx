import { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { detectorsApi } from './api/detectors';

const ConstructionSafetyDetector = () => {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setImgSrc(null);
    setDetections([]);
  };

  const detectSafety = async () => {
    if (!imgSrc) return;
    setLoading(true);
    setDetections([]);

    try {
        const res = await fetch(imgSrc);
        const blob = await res.blob();
        const file = new File([blob], "image.jpg", { type: "image/jpeg" });
        const formData = new FormData();
        formData.append('image', file);

        const data = await detectorsApi.constructionSafety(formData);

        setDetections(data.detections);
        if (!data.detections || data.detections.length === 0) {
            alert("No safety violations detected.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred during detection.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">Construction Safety</h2>
      {cameraError ? (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              <strong className="font-bold">Camera Error:</strong>
              <span className="block sm:inline"> {cameraError}</span>
          </div>
      ) : (
          <div className="mb-4 rounded-lg overflow-hidden shadow-lg border-2 border-gray-300 bg-gray-100 min-h-[300px] relative">
            {!imgSrc ? (
              <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                className="w-full h-full object-cover"
                onUserMediaError={() => setCameraError("Could not access camera. Please check permissions.")}
              />
            ) : (
              <div className="relative">
                  <img src={imgSrc} alt="Captured" className="w-full" />
                  {detections.length > 0 && (
                      <div className="absolute top-0 left-0 right-0 bg-yellow-600 text-white p-2 text-center font-bold opacity-90">
                          DETECTED: {detections.map(d => `${d.label} (${Math.round(d.score * 100)}%)`).join(', ')}
                      </div>
                  )}
              </div>
            )}
          </div>
      )}
      <div className="flex justify-center gap-4">
        {!imgSrc ? (
          <button onClick={capture} disabled={!!cameraError} className="bg-yellow-600 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-yellow-700 transition">Capture Photo</button>
        ) : (
          <>
            <button onClick={retake} className="bg-gray-500 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-gray-600 transition">Retake</button>
            <button onClick={detectSafety} disabled={loading} className="bg-yellow-600 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-yellow-700 transition flex items-center">{loading ? 'Analyzing...' : 'Check Safety'}</button>
          </>
        )}
      </div>
      <p className="mt-4 text-sm text-gray-600 text-center">Detect unsafe scaffolding, missing barriers, etc.</p>
    </div>
  );
};

export default ConstructionSafetyDetector;
