import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, AlertTriangle, ArrowLeft } from 'lucide-react';

const NoiseDetector = ({ onBack }) => {
  const [isListening, setIsListening] = useState(false);
  const [decibels, setDecibels] = useState(0);
  const [error, setError] = useState(null);
  const [maxDecibels, setMaxDecibels] = useState(0);

  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const microphoneRef = useRef(null);
  const javascriptNodeRef = useRef(null);

  const startListening = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      javascriptNodeRef.current = audioContextRef.current.createScriptProcessor(2048, 1, 1);

      analyserRef.current.smoothingTimeConstant = 0.8;
      analyserRef.current.fftSize = 1024;

      microphoneRef.current.connect(analyserRef.current);
      analyserRef.current.connect(javascriptNodeRef.current);
      javascriptNodeRef.current.connect(audioContextRef.current.destination);

      javascriptNodeRef.current.onaudioprocess = () => {
        const array = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(array);
        let values = 0;
        const length = array.length;
        for (let i = 0; i < length; i++) {
          values += (array[i]);
        }
        const average = values / length;
        // Approximate dB calculation (this is relative, not calibrated absolute dB)
        // Standard Web Audio API values are 0-255.
        // 0 is silent, 255 is loud.
        // Let's map it roughly to dB range 30-100 for display purposes.
        const approximateDb = Math.round((average / 255) * 100);

        setDecibels(approximateDb);
        if (approximateDb > maxDecibels) {
            setMaxDecibels(approximateDb);
        }
      };

      setIsListening(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setError("Could not access microphone. Please allow permissions.");
    }
  };

  const stopListening = () => {
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    setIsListening(false);
    setDecibels(0);
  };

  useEffect(() => {
    return () => {
      stopListening();
    };
  }, []);

  const getNoiseLevelDescription = (db) => {
    if (db < 40) return { text: "Quiet", color: "text-green-600", bg: "bg-green-100" };
    if (db < 60) return { text: "Moderate", color: "text-blue-600", bg: "bg-blue-100" };
    if (db < 80) return { text: "Loud", color: "text-orange-600", bg: "bg-orange-100" };
    return { text: "Dangerous", color: "text-red-600", bg: "bg-red-100" };
  };

  const level = getNoiseLevelDescription(decibels);

  return (
    <div className="p-4">
      <button
        onClick={onBack}
        className="mb-4 flex items-center text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={20} className="mr-1" /> Back
      </button>

      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 flex flex-col items-center">
        <h2 className="text-2xl font-bold mb-4 text-gray-800 flex items-center gap-2">
          <Volume2 className="text-blue-600" /> Noise Detector
        </h2>

        <p className="text-center text-gray-600 mb-6">
          Measure noise pollution levels in your area. High noise levels can be reported to authorities.
        </p>

        <div className={`w-48 h-48 rounded-full flex flex-col items-center justify-center mb-6 transition-all duration-300 ${isListening ? level.bg : 'bg-gray-100'}`}>
          {isListening ? (
            <>
              <span className={`text-5xl font-bold ${level.color}`}>{decibels}</span>
              <span className="text-gray-500 text-sm mt-1">Relative dB</span>
              <span className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold ${level.bg} ${level.color}`}>
                {level.text}
              </span>
            </>
          ) : (
             <VolumeX size={48} className="text-gray-400" />
          )}
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center mb-4 w-full">
            {error}
          </div>
        )}

        <div className="w-full flex justify-center">
            {!isListening ? (
            <button
                onClick={startListening}
                className="bg-blue-600 text-white px-8 py-3 rounded-full hover:bg-blue-700 transition font-semibold shadow-lg flex items-center gap-2"
            >
                <Volume2 size={20} /> Start Measuring
            </button>
            ) : (
            <button
                onClick={stopListening}
                className="bg-red-500 text-white px-8 py-3 rounded-full hover:bg-red-600 transition font-semibold shadow-lg flex items-center gap-2"
            >
                <VolumeX size={20} /> Stop
            </button>
            )}
        </div>

        {isListening && decibels > 80 && (
             <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4 w-full">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="text-red-500 shrink-0" />
                    <div>
                        <h3 className="font-bold text-red-800">High Noise Level Detected!</h3>
                        <p className="text-sm text-red-700 mt-1">
                            Noise levels above 80dB can be harmful. In residential areas, this might be a violation.
                        </p>
                        <button className="mt-2 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">
                            Report Noise Pollution
                        </button>
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
  );
};

export default NoiseDetector;
