import { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { detectorsApi } from './api/detectors';

const VandalismDetector = () => {
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

  const detectVandalism = async () => {
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
        const data = await detectorsApi.vandalism(formData);

        setDetections(data.detections);
        if (data.detections.length === 0) {
            alert("No vandalism detected.");
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
      <h2 className="text-2xl font-bold mb-4">Graffiti & Vandalism Detector</h2>

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
                  {/* Since CLIP doesn't give boxes, we just show a banner if detected */}
                  {detections.length > 0 && (
                      <div className="absolute top-0 left-0 right-0 bg-red-600 text-white p-2 text-center font-bold opacity-90">
                          DETECTED: {detections.map(d => d.label).join(', ')}
                      </div>
                  )}
              </div>
            )}
          </div>
      )}

      <div className="flex justify-center gap-4">
        {!imgSrc ? (
          <button
            onClick={capture}
            disabled={!!cameraError}
            className={`bg-blue-600 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-blue-700 transition ${cameraError ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Capture Photo
          </button>
        ) : (
          <>
            <button
              onClick={retake}
              className="bg-gray-500 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-gray-600 transition"
            >
              Retake
            </button>
            <button
              onClick={detectVandalism}
              disabled={loading}
              className={`bg-red-600 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-red-700 transition flex items-center ${loading ? 'opacity-70 cursor-wait' : ''}`}
            >
              {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </>
              ) : 'Detect Vandalism'}
            </button>
          </>
        )}
      </div>

      <p className="mt-4 text-sm text-gray-600 text-center">
        Point camera at graffiti or vandalism to detect.
      </p>
    </div>
  );
};

export default VandalismDetector;
