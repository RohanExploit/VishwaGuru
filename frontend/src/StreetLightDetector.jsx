import { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

const StreetLightDetector = ({ onBack }) => {
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

  const detectLight = async () => {
    if (!imgSrc) return;
    setLoading(true);
    setDetections([]);

    try {
        const res = await fetch(imgSrc);
        const blob = await res.blob();
        const file = new File([blob], "image.jpg", { type: "image/jpeg" });

        const formData = new FormData();
        formData.append('image', file);

        const response = await fetch('/api/detect-street-light', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            setDetections(data.detections);
            if (data.detections.length === 0) {
                alert("No broken street lights detected.");
            }
        } else {
            console.error("Detection failed");
            alert("Detection failed. Please try again.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred during detection.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <button onClick={onBack} className="self-start text-blue-600 mb-2">
        &larr; Back
      </button>
      <div className="p-4 max-w-md mx-auto w-full">
        <h2 className="text-2xl font-bold mb-4">Broken Street Light Detector</h2>

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
                onClick={detectLight}
                disabled={loading}
                className={`bg-red-600 text-white px-6 py-2 rounded-full font-semibold shadow-md hover:bg-red-700 transition flex items-center ${loading ? 'opacity-70 cursor-wait' : ''}`}
              >
                {loading ? 'Analyzing...' : 'Detect'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StreetLightDetector;
