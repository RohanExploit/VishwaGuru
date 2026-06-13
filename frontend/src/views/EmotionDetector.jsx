import React, { useState, useRef, useCallback } from 'react';
import { Camera, Image as ImageIcon, Loader2, ArrowLeft, RefreshCw, Smile } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Webcam from 'react-webcam';
import { detectorsApi } from '../api';

const EmotionDetector = ({ onBack }) => {
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showWebcam, setShowWebcam] = useState(false);
  const webcamRef = useRef(null);

  const captureWebcam = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    if (imageSrc) {
      fetch(imageSrc)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], "emotion_capture.jpg", { type: "image/jpeg" });
          setImage(file);
          setPreviewUrl(imageSrc);
          setShowWebcam(false);
          setResult(null);
          setError(null);
        });
    }
  }, [webcamRef]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const resetDetector = () => {
    setImage(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  };

  const analyzeEmotion = async () => {
    if (!image) return;

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('image', image);

    try {
      const data = await detectorsApi.emotion(formData);
      if (data && data.emotions) {
        setResult(data);
      } else {
        setError('Could not detect emotions in the image.');
      }
    } catch (err) {
      console.error("Emotion detection failed:", err);
      setError('Failed to analyze the image. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 relative z-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-[2.5rem] p-8 border border-white/20 dark:border-gray-800/50 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-pink-500/10 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[80px] translate-y-1/2 -translate-x-1/2"></div>

        {/* Header */}
        <div className="flex items-center gap-4 mb-8 relative z-10">
          <button
            onClick={onBack}
            className="p-3 bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:scale-105 transition-transform text-gray-600 dark:text-gray-300"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h2 className="text-3xl font-black text-gray-900 dark:text-white flex items-center gap-3">
              <span className="p-2 bg-pink-100 dark:bg-pink-900/30 text-pink-600 rounded-xl">
                <Smile size={28} />
              </span>
              Emotion Detector
            </h2>
            <p className="text-gray-500 dark:text-gray-400 font-medium">Analyze facial expressions to determine current emotional state</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
          {/* Left Column: Image Input */}
          <div className="space-y-6">
            {!previewUrl && !showWebcam ? (
              <div className="grid grid-cols-2 gap-4 h-64">
                <label className="group cursor-pointer bg-gray-50 dark:bg-gray-800/50 rounded-3xl border-2 border-dashed border-gray-200 dark:border-gray-700 p-6 flex flex-col items-center justify-center gap-4 hover:border-pink-500 dark:hover:border-pink-400 transition-all">
                  <div className="p-4 bg-white dark:bg-gray-800 rounded-2xl shadow-sm text-gray-400 group-hover:text-pink-500 group-hover:scale-110 transition-all">
                    <ImageIcon size={32} />
                  </div>
                  <span className="font-bold text-gray-700 dark:text-gray-300">Upload Photo</span>
                  <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
                </label>

                <button
                  onClick={() => setShowWebcam(true)}
                  className="group bg-pink-50 dark:bg-pink-900/20 rounded-3xl border-2 border-dashed border-pink-200 dark:border-pink-800/50 p-6 flex flex-col items-center justify-center gap-4 hover:border-pink-500 transition-all"
                >
                  <div className="p-4 bg-white dark:bg-gray-800 rounded-2xl shadow-sm text-pink-500 group-hover:scale-110 transition-all">
                    <Camera size={32} />
                  </div>
                  <span className="font-bold text-pink-700 dark:text-pink-300">Take Photo</span>
                </button>
              </div>
            ) : showWebcam ? (
              <div className="relative rounded-3xl overflow-hidden shadow-xl border-4 border-white dark:border-gray-800 bg-black aspect-square md:aspect-auto md:h-80 flex flex-col">
                <Webcam
                  audio={false}
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  videoConstraints={{ facingMode: "user" }}
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent flex justify-center gap-4">
                  <button
                    onClick={() => setShowWebcam(false)}
                    className="px-6 py-2 bg-gray-800 text-white rounded-full font-bold hover:bg-gray-700 transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={captureWebcam}
                    className="px-8 py-2 bg-pink-600 text-white rounded-full font-bold hover:bg-pink-500 transition flex items-center gap-2 shadow-lg shadow-pink-600/30"
                  >
                    <Camera size={20} /> Capture
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-3xl overflow-hidden shadow-xl border-4 border-white dark:border-gray-800 aspect-square md:aspect-auto md:h-80 bg-gray-100">
                  {previewUrl && <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />}
                  <button
                    onClick={resetDetector}
                    className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur-sm transition-all"
                    title="Choose different image"
                  >
                    <RefreshCw size={20} />
                  </button>
                </div>
                <button
                  onClick={analyzeEmotion}
                  disabled={isAnalyzing}
                  className="w-full py-4 rounded-2xl bg-gradient-to-r from-pink-600 to-purple-600 text-white font-black text-lg shadow-xl shadow-pink-600/20 hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-3"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 size={24} className="animate-spin" />
                      Analyzing Face...
                    </>
                  ) : (
                    <>
                      <Smile size={24} />
                      Detect Emotion
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-3xl p-6 border border-gray-100 dark:border-gray-700">
            <h3 className="text-xl font-black mb-6 flex items-center gap-2">
              Analysis Results
            </h3>

            <AnimatePresence mode="wait">
              {isAnalyzing ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center h-48 gap-4 text-pink-600"
                >
                  <Loader2 size={40} className="animate-spin" />
                  <p className="font-bold animate-pulse">Running neural network...</p>
                </motion.div>
              ) : error ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-red-50 text-red-700 p-4 rounded-2xl border border-red-200"
                >
                  <p className="font-bold">{error ? error.toString() : ''}</p>
                </motion.div>
              ) : result ? (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-6"
                >
                  {result.emotions && result.emotions.length > 0 ? (
                    <div className="space-y-4">
                      {result.emotions.map((emotion, index) => (
                        <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-black text-gray-800 dark:text-gray-200 uppercase tracking-widest text-sm flex items-center gap-2">
                              {index === 0 && <span className="w-2 h-2 rounded-full bg-pink-500 animate-pulse"></span>}
                              {emotion.label}
                            </span>
                            <span className="font-bold text-pink-600">{(emotion.score * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${emotion.score * 100}%` }}
                              transition={{ duration: 1, delay: index * 0.2 }}
                              className={`h-full ${index === 0 ? 'bg-pink-500' : 'bg-pink-300 dark:bg-pink-700'}`}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center p-8 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
                      <p className="font-bold text-gray-500">No clear emotions detected</p>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                  <Smile size={48} className="mb-4 opacity-50" />
                  <p className="font-medium">Upload or take a photo to see results</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default EmotionDetector;
