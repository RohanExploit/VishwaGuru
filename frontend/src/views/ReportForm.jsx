import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fakeActionPlan } from '../fakeData';
import { Camera, Image as ImageIcon, CheckCircle2, AlertTriangle, Loader2, Layers } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { saveReportOffline, registerBackgroundSync } from '../offlineQueue';
import VoiceInput from '../components/VoiceInput';
import { detectorsApi } from '../api';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

const ReportForm = ({ setView, setLoading, setError, setActionPlan, loading }) => {
  const { t, i18n } = useTranslation();
  const locationState = useLocation().state || {};
  const [formData, setFormData] = useState({
    description: locationState.description || '',
    category: locationState.category || 'road',
    image: null,
    latitude: null,
    longitude: null,
    location: ''
  });
  const [gettingLocation, setGettingLocation] = useState(false);
  const [severity, setSeverity] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [describing, setDescribing] = useState(false);
  const [urgencyAnalysis, setUrgencyAnalysis] = useState(null);
  const [analyzingUrgency, setAnalyzingUrgency] = useState(false);
  const [depthMap, setDepthMap] = useState(null);
  const [analyzingDepth, setAnalyzingDepth] = useState(false);
  const [smartCategory, setSmartCategory] = useState(null);
  const [analyzingSmartScan, setAnalyzingSmartScan] = useState(false);
  const [submitStatus, setSubmitStatus] = useState({ state: 'idle', message: '' });
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [uploading, setUploading] = useState(false);
  const [analysisErrors, setAnalysisErrors] = useState({});

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const analyzeUrgency = async () => {
      if (!formData.description || formData.description.length < 5) return;
      setAnalyzingUrgency(true);
      try {
          const response = await fetch(`${API_URL}/api/analyze-urgency`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ description: formData.description }),
          });
          if (response.ok) {
              const data = await response.json();
              setUrgencyAnalysis(data);
          }
      } catch (e) {
          console.error("Urgency analysis failed", e);
      } finally {
          setAnalyzingUrgency(false);
      }
  };

  const autoDescribe = async () => {
      if (!formData.image) return;
      setDescribing(true);

      const uploadData = new FormData();
      uploadData.append('image', formData.image);

      try {
          const response = await fetch(`${API_URL}/api/generate-description`, {
              method: 'POST',
              body: uploadData
          });
          if (response.ok) {
              const data = await response.json();
              if (data.description) {
                  setFormData(prev => ({...prev, description: data.description}));
              }
          }
      } catch (e) {
          console.error("Auto description failed", e);
      } finally {
          setDescribing(false);
      }
  };

  const analyzeImage = async (file) => {
    if (!file) return;
    setAnalyzing(true);
    setSeverity(null);
    setAnalysisErrors(prev => ({ ...prev, severity: null }));

    const uploadData = new FormData();
    uploadData.append('image', file);

    try {
        const response = await fetch(`${API_URL}/api/detect-severity`, {
            method: 'POST',
            body: uploadData
        });
        if (response.ok) {
            const data = await response.json();
            setSeverity(data);
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            setAnalysisErrors(prev => ({ ...prev, severity: errorData.detail || 'Analysis failed' }));
        }
    } catch (e) {
        console.error("Severity analysis failed", e);
        setAnalysisErrors(prev => ({ ...prev, severity: 'Network error - please try again' }));
    } finally {
        setAnalyzing(false);
    }
  };

  const analyzeDepth = async () => {
      if (!formData.image) return;
      setAnalyzingDepth(true);
      setDepthMap(null);

      const uploadData = new FormData();
      uploadData.append('image', formData.image);

      try {
          const data = await detectorsApi.depth(uploadData);
          if (data && data.depth_map) {
              setDepthMap(data.depth_map);
          }
      } catch (e) {
          console.error("Depth analysis failed", e);
      } finally {
          setAnalyzingDepth(false);
      }
  };

  const mapSmartScanToCategory = (label) => {
      const map = {
          'pothole': 'road',
          'garbage': 'garbage',
          'flooded street': 'water',
          'fire accident': 'road',
          'fallen tree': 'road',
          'stray animal': 'road',
          'blocked road': 'road',
          'broken streetlight': 'streetlight',
          'illegal parking': 'road',
          'graffiti vandalism': 'college_infra',
          'normal street': 'road'
      };
      return map[label] || 'road';
  };

  const analyzeSmartScan = async (file) => {
      if (!file) return;
      setAnalyzingSmartScan(true);
      setSmartCategory(null);
      setAnalysisErrors(prev => ({ ...prev, smartScan: null }));

      const uploadData = new FormData();
      uploadData.append('image', file);

      try {
          const data = await detectorsApi.smartScan(uploadData);
          if (data && data.category && data.category !== 'unknown') {
              const mappedCategory = mapSmartScanToCategory(data.category);
              setSmartCategory({
                  original: data.category,
                  mapped: mappedCategory,
                  confidence: data.confidence
              });
          }
      } catch (e) {
          console.error("Smart scan failed", e);
          setAnalysisErrors(prev => ({ ...prev, smartScan: 'Smart scan failed - continuing with manual selection' }));
      } finally {
          setAnalyzingSmartScan(false);
      }
  };

  const compressImage = (file, maxWidth = 1024, maxHeight = 1024, quality = 0.8) => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img;

        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }

        canvas.width = width;
        canvas.height = height;

        // Draw and compress
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(resolve, 'image/jpeg', quality);
      };

      img.src = URL.createObjectURL(file);
    });
  };

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploading(true);
      try {
        // Compress image if it's large
        let processedFile = file;
        if (file.size > 1024 * 1024) { // 1MB
          const compressedBlob = await compressImage(file);
          processedFile = new File([compressedBlob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now(),
          });
        }

        setFormData({...formData, image: processedFile});

        // Analyze in parallel but with error handling
        await Promise.allSettled([
          analyzeImage(processedFile),
          analyzeSmartScan(processedFile)
        ]);
      } catch (error) {
        console.error('Image processing failed:', error);
        // Fallback to original file
        setFormData({...formData, image: file});
        await Promise.allSettled([
          analyzeImage(file),
          analyzeSmartScan(file)
        ]);
      } finally {
        setUploading(false);
      }
    }
  };

  const getLocation = () => {
    setGettingLocation(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData(prev => ({
            ...prev,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            location: `Lat: ${position.coords.latitude.toFixed(4)}, Long: ${position.coords.longitude.toFixed(4)}`
          }));
          setGettingLocation(false);
        },
        (err) => {
          console.error("Error getting location: ", err);
          setError("Failed to get location. Please enable GPS.");
          setGettingLocation(false);
        }
      );
    } else {
      setError("Geolocation is not supported by this browser.");
      setGettingLocation(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSubmitStatus({ state: 'pending', message: 'Submitting your issue…' });

    const isOnline = navigator.onLine;

    if (!isOnline) {
      // Save offline
      try {
        const reportData = {
          category: formData.category,
          description: formData.description,
          latitude: formData.latitude,
          longitude: formData.longitude,
          location: formData.location,
          imageBlob: formData.image,
          severity_level: severity?.level,
          severity_score: severity?.confidence
        };
        await saveReportOffline(reportData);
        registerBackgroundSync();
        setSubmitStatus({ state: 'success', message: 'Report saved offline. Will sync when online.' });
        setActionPlan(fakeActionPlan); // Show fallback plan
        setView('action');
      } catch (err) {
        setSubmitStatus({ state: 'error', message: 'Failed to save offline.' });
        setError('Failed to save report offline.');
      } finally {
        setLoading(false);
      }
      return;
    }

    const payload = new FormData();
    payload.append('description', formData.description);
    payload.append('category', formData.category);
    payload.append('language', i18n.language);
    if (formData.latitude) payload.append('latitude', formData.latitude);
    if (formData.longitude) payload.append('longitude', formData.longitude);
    if (formData.location) payload.append('location', formData.location);
    if (formData.image) {
      payload.append('image', formData.image);
    }
    // Append severity info if available
    if (severity) {
        payload.append('severity_level', severity.level);
        payload.append('severity_score', severity.confidence);
    }

    try {
      const response = await fetch(`${API_URL}/api/issues`, {
        method: 'POST',
        body: payload,
      });

      if (!response.ok) throw new Error('Failed to submit issue');

      const data = await response.json();
      if (data.action_plan) {
        setActionPlan(data.action_plan);
      } else {
        setActionPlan({ id: data.id, status: 'generating' });
      }
      setSubmitStatus({ state: 'success', message: 'Issue submitted. Preparing your action plan…' });
      setView('action');
    } catch (err) {
      console.error("Submission failed, using fake action plan", err);
      // Fallback to fake action plan on failure
      setActionPlan(fakeActionPlan);
      setView('action');
      setSubmitStatus({ state: 'error', message: 'Submission failed. We generated a fallback plan—please retry when convenient.' });
      setError('Unable to submit right now. Your plan is a fallback; please retry later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6">
       <h2 className="text-xl font-semibold mb-4 text-center">Report an Issue</h2>
       <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Category</label>
            <select
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
            >
              <option value="road">Road / Potholes</option>
              <option value="water">Water Supply</option>
              <option value="garbage">Garbage / Sanitation</option>
              <option value="streetlight">Streetlight</option>
              <option value="college_infra">College Infrastructure</option>
              <option value="women_safety">Women Safety</option>
            </select>
            {analyzingSmartScan && (
                <div className="text-xs text-blue-600 mt-1 animate-pulse flex items-center gap-1">
                    <Loader2 size={12} className="animate-spin"/>
                    AI is analyzing image for category...
                </div>
            )}
            {analysisErrors.smartScan && (
                <div className="text-xs text-orange-600 mt-1 flex items-center gap-1">
                    <AlertTriangle size={12} />
                    {analysisErrors.smartScan}
                </div>
            )}
            {smartCategory && (
                <div
                    onClick={() => setFormData({...formData, category: smartCategory.mapped})}
                    className="mt-2 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-100 p-2 rounded-lg cursor-pointer hover:bg-purple-100 transition flex items-center justify-between group"
                >
                    <div className="flex items-center gap-2">
                        <span className="text-lg">✨</span>
                        <div>
                            <p className="text-xs text-purple-800 font-bold uppercase tracking-wide">AI Suggestion</p>
                            <p className="text-sm font-medium text-purple-900 capitalize">{smartCategory.original}</p>
                        </div>
                    </div>
                    <div className="bg-white text-purple-600 px-3 py-1 rounded text-xs font-bold shadow-sm group-hover:shadow transition">
                        Apply
                    </div>
                </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Language</label>
            <select
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              value={i18n.language}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="mr">मराठी (Marathi)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <div className="relative">
              <textarea
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border pr-12"
                rows="3"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                onBlur={analyzeUrgency}
                placeholder="Describe the issue..."
              />
              <div className="absolute top-2 right-2">
                <VoiceInput
                  onTranscript={(transcript) => setFormData(prev => ({...prev, description: prev.description + ' ' + transcript}))}
                  language={i18n.language}
                />
              </div>
            </div>
            {analyzingUrgency && (
               <div className="mt-1 text-xs text-blue-600 animate-pulse">
                   Checking urgency...
               </div>
            )}
            {urgencyAnalysis && !analyzingUrgency && (
                <div className={`mt-2 p-2 rounded text-sm flex items-center justify-between ${
                    urgencyAnalysis.urgency === 'High' ? 'bg-red-50 text-red-800 border border-red-200' :
                    urgencyAnalysis.urgency === 'Medium' ? 'bg-orange-50 text-orange-800 border border-orange-200' :
                    'bg-green-50 text-green-800 border border-green-200'
                }`}>
                    <span className="font-semibold">Urgency: {urgencyAnalysis.urgency}</span>
                    <span className="text-xs opacity-75">Sentiment: {urgencyAnalysis.sentiment}</span>
                </div>
            )}
            {formData.image && (
                <button
                    type="button"
                    onClick={autoDescribe}
                    disabled={describing}
                    className="mt-2 text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded hover:bg-purple-200 transition flex items-center gap-1 font-medium"
                >
                    {describing ? 'Generating description...' : '✨ Auto-fill description from image'}
                </button>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Location (Optional)</label>
             <div className="flex gap-2 mt-1">
                <input
                    type="text"
                    readOnly
                    placeholder="Location not set"
                    className="block w-full rounded-md border-gray-300 shadow-sm p-2 border bg-gray-50"
                    value={formData.location || ''}
                />
                <button
                    type="button"
                    onClick={getLocation}
                    disabled={gettingLocation}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded inline-flex items-center"
                >
                    {gettingLocation ? '...' : '📍'}
                </button>
             </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Photo Evidence</label>

            <div className="flex gap-3 mb-2">
                <label className="flex-1 cursor-pointer bg-white hover:bg-gray-50 text-gray-700 font-medium py-3 px-4 rounded-lg text-center border border-gray-300 shadow-sm flex items-center justify-center gap-2 transition">
                    <ImageIcon size={20} />
                    <span>Upload</span>
                    <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleImageChange}
                    />
                </label>
                <label className="flex-1 cursor-pointer bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium py-3 px-4 rounded-lg text-center border border-blue-200 shadow-sm flex items-center justify-center gap-2 transition">
                    <Camera size={20} />
                    <span>Camera</span>
                    <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        className="hidden"
                        onChange={handleImageChange}
                    />
                </label>
            </div>

            {formData.image && (
                <div className="text-sm text-green-600 mb-2 text-center flex items-center justify-center gap-2">
                    {uploading ? (
                        <>
                            <Loader2 size={16} className="animate-spin" />
                            Processing image...
                        </>
                    ) : (
                        <>Selected: {formData.image.name}</>
                    )}
                </div>
            )}

            {formData.image && !depthMap && (
                <button
                    type="button"
                    onClick={analyzeDepth}
                    disabled={analyzingDepth}
                    className="w-full text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-2 rounded-lg hover:bg-indigo-100 transition flex items-center justify-center gap-2 font-medium mb-2"
                >
                    {analyzingDepth ? (
                        <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                        <Layers size={14} />
                    )}
                    {analyzingDepth ? 'Generating 3D Map...' : 'Analyze Severity (3D)'}
                </button>
            )}

            {depthMap && (
                <div className="mb-2 border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-2 py-1 text-xs text-gray-500 font-medium border-b border-gray-200">
                        3D Depth Analysis Map
                    </div>
                    <img
                        src={`data:image/jpeg;base64,${depthMap}`}
                        alt="Depth Map"
                        className="w-full h-auto object-cover"
                    />
                </div>
            )}

            {analyzing && (
                <div className="flex items-center justify-center gap-2 text-blue-600 bg-blue-50 p-3 rounded-lg border border-blue-100 animate-pulse">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm font-medium">Analyzing severity...</span>
                </div>
            )}

            {analysisErrors.severity && (
                <div className="flex items-center justify-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
                    <AlertTriangle size={16} />
                    <span className="text-sm font-medium">Severity analysis: {analysisErrors.severity}</span>
                </div>
            )}

            {severity && (
                <div className={`p-3 rounded-lg border ${
                    severity.level === 'Critical' ? 'bg-red-50 border-red-200 text-red-800' :
                    severity.level === 'High' ? 'bg-orange-50 border-orange-200 text-orange-800' :
                    severity.level === 'Medium' ? 'bg-yellow-50 border-yellow-200 text-yellow-800' :
                    'bg-green-50 border-green-200 text-green-800'
                }`}>
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-bold uppercase tracking-wider">AI Severity Analysis</span>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                             severity.level === 'Critical' ? 'bg-red-200 text-red-900' :
                             severity.level === 'High' ? 'bg-orange-200 text-orange-900' :
                             severity.level === 'Medium' ? 'bg-yellow-200 text-yellow-900' :
                             'bg-green-200 text-green-900'
                        }`}>{severity.level}</span>
                    </div>
                    <p className="text-sm">
                        Detected <b>{severity.raw_label}</b> with {(severity.confidence * 100).toFixed(0)}% confidence.
                    </p>
                </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 font-bold shadow-md"
          >
            {loading ? 'Processing…' : isOnline ? 'Generate Action Plan' : 'Save Offline'}
          </button>

          <div className={`mt-2 text-center text-sm ${isOnline ? 'text-green-600' : 'text-orange-600'}`}>
            {isOnline ? '🟢 Online - Report will be submitted immediately' : '🟠 Offline - Report will be saved and synced later'}
          </div>

          {submitStatus.state !== 'idle' && (
            <div
              className={`mt-3 flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium shadow-sm ${
                submitStatus.state === 'success'
                  ? 'bg-green-50 border-green-200 text-green-800'
                  : submitStatus.state === 'pending'
                  ? 'bg-blue-50 border-blue-200 text-blue-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              {submitStatus.state === 'success' && <CheckCircle2 size={18} />}
              {submitStatus.state === 'pending' && <Loader2 size={18} className="animate-spin" />}
              {submitStatus.state === 'error' && <AlertTriangle size={18} />}
              <span>{submitStatus.message}</span>
            </div>
          )}
          <button type="button" onClick={() => setView('home')} className="mt-2 text-gray-500 hover:text-gray-700 underline text-center w-full block text-sm">Cancel</button>
       </form>
    </div>
  );
};

export default ReportForm;
