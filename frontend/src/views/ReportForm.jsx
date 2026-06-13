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
    email: localStorage.getItem('user_email') || '',
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
  const [nearbyIssues, setNearbyIssues] = useState([]);
  const [checkingNearby, setCheckingNearby] = useState(false);
  const [showNearbyModal, setShowNearbyModal] = useState(false);

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
          setFormData(prev => ({ ...prev, description: data.description }));
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

        setFormData({ ...formData, image: processedFile });

        // Analyze in parallel but with error handling
        await Promise.allSettled([
          analyzeImage(processedFile),
          analyzeSmartScan(processedFile)
        ]);
      } catch (error) {
        console.error('Image processing failed:', error);
        // Fallback to original file
        setFormData({ ...formData, image: file });
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

  const checkNearbyIssues = async () => {
    if (!formData.latitude || !formData.longitude) {
      getLocation(); // Try to get location first
      return;
    }
    setCheckingNearby(true);
    try {
      const response = await fetch(`${API_URL}/api/issues/nearby?latitude=${formData.latitude}&longitude=${formData.longitude}&radius=50`);
      if (response.ok) {
        const data = await response.json();
        setNearbyIssues(data);
        setShowNearbyModal(true);
      }
    } catch (e) {
      console.error("Failed to check nearby issues", e);
    } finally {
      setCheckingNearby(false);
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
      } catch (error) {
        console.error("Offline save failed", error);
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

      if (data.deduplication_info && data.deduplication_info.has_nearby_issues && !data.id) {
        setSubmitStatus({ state: 'success', message: 'Report linked to existing issue!' });
        alert("We found a similar issue nearby reported recently. Your report has been linked to it to increase its priority!");
        setView('home');
        return;
      }

      // Always set status to generating initially, merging any immediate data (like RAG rules)
      setActionPlan({ ...(data.action_plan || {}), id: data.id, status: 'generating' });
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
    <div className="mt-12 max-w-2xl mx-auto pb-20">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        {/* Decorative background glow */}
        <div className="absolute -top-20 -left-20 w-64 h-64 bg-blue-500/10 rounded-full blur-[100px] -z-10"></div>
        <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-purple-500/10 rounded-full blur-[100px] -z-10"></div>

        <div className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-3xl rounded-[2.5rem] border border-white/20 dark:border-gray-800/50 shadow-2xl overflow-hidden p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-10 space-y-3">
            <h2 className="text-3xl md:text-4xl font-black text-gray-900 dark:text-white tracking-tight">
              {t('home.landing.cta') || 'Report Civic Issue'}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 font-medium">
              Join thousands of citizens making their city better.
            </p>
            <div className="h-1.5 w-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mx-auto"></div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Category Section */}
            <div className="space-y-3">
              <label className="text-sm font-black text-gray-700 dark:text-gray-300 uppercase tracking-widest ml-1 flex items-center gap-2">
                <Layers size={14} className="text-blue-600" />
                {t('home.landing.features.civicIssues')}
              </label>
              <div className="relative group">
                <select
                  className="w-full bg-white/50 dark:bg-gray-800/50 rounded-2xl border-2 border-gray-100 dark:border-gray-800 p-4 pl-5 appearance-none focus:outline-none focus:border-blue-600 dark:focus:border-blue-400 font-bold text-gray-900 dark:text-white transition-all transition-colors cursor-pointer group-hover:bg-white dark:group-hover:bg-gray-800"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="road">{t('home.issues.pothole')}</option>
                  <option value="water">{t('home.issues.waterLeak')}</option>
                  <option value="garbage">{t('home.issues.garbage')}</option>
                  <option value="streetlight">{t('home.issues.darkStreet')}</option>
                  <option value="college_infra">{t('home.issues.brokenInfra')}</option>
                  <option value="women_safety">{t('home.issues.civicEye')}</option>
                </select>
                <div className="absolute inset-y-0 right-5 flex items-center pointer-events-none text-gray-400">
                  <ChevronRight size={20} className="rotate-90" />
                </div>
              </div>

              {/* AI Category Suggestion Widget */}
              <AnimatePresence>
                {analyzingSmartScan && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-3 p-4 bg-blue-50/50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/50"
                  >
                    <Loader2 size={18} className="animate-spin text-blue-600" />
                    <span className="text-sm font-bold text-blue-800 dark:text-blue-300">AI identifying category...</span>
                  </motion.div>
                )}

                {smartCategory && !analyzingSmartScan && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={() => setFormData({ ...formData, category: smartCategory.mapped })}
                    className="group relative bg-gradient-to-br from-indigo-600/5 to-purple-600/5 dark:from-indigo-400/10 dark:to-purple-400/10 border border-indigo-100 dark:border-indigo-800/50 p-5 rounded-2xl cursor-pointer hover:shadow-lg transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="p-2.5 bg-white dark:bg-gray-800 rounded-xl shadow-sm text-indigo-600">
                          <Zap size={20} />
                        </div>
                        <div>
                          <p className="text-[10px] text-indigo-500 font-black uppercase tracking-widest">AI SUGGESTION</p>
                          <p className="text-base font-black text-gray-900 dark:text-white capitalize">{smartCategory.original}</p>
                        </div>
                      </div>
                      <button type="button" className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-black shadow-lg shadow-indigo-600/20 group-hover:scale-105 transition-transform">
                        Apply
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Email Field */}
            <div className="space-y-3">
              <label className="text-sm font-black text-gray-700 dark:text-gray-300 uppercase tracking-widest ml-1 flex items-center gap-2">
                <CheckCircle2 size={14} className="text-gray-400" />
                Email (Optional)
              </label>
              <div className="relative group">
                <input
                  type="email"
                  className="w-full bg-white/50 dark:bg-gray-800/50 rounded-2xl border-2 border-gray-100 dark:border-gray-800 p-4 appearance-none focus:outline-none focus:border-blue-600 dark:focus:border-blue-400 font-bold text-gray-900 dark:text-white transition-all group-hover:bg-white dark:group-hover:bg-gray-800"
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            {/* Description Section */}
            <div className="space-y-3">
              <label className="text-sm font-black text-gray-700 dark:text-gray-300 uppercase tracking-widest ml-1 flex items-center gap-2">
                <FileText size={14} className="text-indigo-600" />
                Description
              </label>
              <div className="relative group">
                <textarea
                  required
                  className="w-full bg-white/50 dark:bg-gray-800/50 rounded-2xl border-2 border-gray-100 dark:border-gray-800 p-5 appearance-none focus:outline-none focus:border-blue-600 dark:focus:border-blue-400 font-bold text-gray-900 dark:text-white transition-all group-hover:bg-white dark:group-hover:bg-gray-800 min-h-[140px]"
                  rows="4"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  onBlur={analyzeUrgency}
                  placeholder="High priority potholes near main signal..."
                />
                <div className="absolute bottom-4 right-4 z-10">
                  <VoiceInput
                    onTranscript={(transcript) => setFormData(prev => ({ ...prev, description: (prev.description + ' ' + transcript).trim() }))}
                    language={i18n.language}
                  />
                </div>
              </div>

              {/* AI Indicators */}
              <div className="flex flex-wrap gap-3">
                {analyzingUrgency && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-black rounded-lg border border-blue-100 dark:border-blue-800/50">
                    <Loader2 size={12} className="animate-spin" />
                    Checking Priority...
                  </div>
                )}
                {urgencyAnalysis && !analyzingUrgency && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`px-4 py-2 rounded-xl text-xs font-black border flex items-center gap-2 shadow-sm ${urgencyAnalysis.urgency === 'High' ? 'bg-rose-50 border-rose-100 text-rose-700 dark:bg-rose-900/20 dark:border-rose-900/50 dark:text-rose-400' :
                      urgencyAnalysis.urgency === 'Medium' ? 'bg-amber-50 border-amber-100 text-amber-700 dark:bg-amber-900/20 dark:border-amber-900/50 dark:text-amber-400' :
                        'bg-emerald-50 border-emerald-100 text-emerald-700 dark:bg-emerald-900/20 dark:border-emerald-900/50 dark:text-emerald-400'
                      }`}
                  >
                    <div className={`w-2 h-2 rounded-full animate-pulse ${urgencyAnalysis.urgency === 'High' ? 'bg-rose-500' : urgencyAnalysis.urgency === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>
                    {urgencyAnalysis.urgency} Priority Detected
                  </motion.div>
                )}
                {formData.image && (
                  <button
                    type="button"
                    onClick={autoDescribe}
                    disabled={describing}
                    className="text-xs bg-purple-600 text-white px-4 py-2 rounded-xl shadow-lg shadow-purple-600/20 hover:scale-105 transition-transform flex items-center gap-2 font-black disabled:opacity-50"
                  >
                    {describing ? <Loader2 size={12} className="animate-spin" /> : '✨'}
                    {describing ? 'Describing...' : 'Auto-fill Description'}
                  </button>
                )}
              </div>
            </div>

            {/* Location Section */}
            <div className="space-y-3">
              <label className="text-sm font-black text-gray-700 dark:text-gray-300 uppercase tracking-widest ml-1 flex items-center gap-2">
                <MapPin size={14} className="text-rose-600" />
                Location Information
              </label>
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative group flex-1">
                  <input
                    type="text"
                    readOnly
                    placeholder="Auto-detecting address..."
                    className="w-full bg-white/50 dark:bg-gray-800/50 rounded-2xl border-2 border-gray-100 dark:border-gray-800 p-4 appearance-none focus:outline-none font-bold text-gray-900 dark:text-white transition-all group-hover:bg-white dark:group-hover:bg-gray-800 leading-tight"
                    value={formData.location || ''}
                  />
                </div>
                <button
                  type="button"
                  onClick={getLocation}
                  disabled={gettingLocation}
                  className="bg-gray-900 dark:bg-blue-600 text-white font-black py-4 px-8 rounded-2xl flex items-center justify-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-xl shadow-black/10 disabled:opacity-50"
                >
                  {gettingLocation ? <Loader2 size={20} className="animate-spin" /> : <MapPin size={20} />}
                  {gettingLocation ? 'Detecting...' : 'Get Pin'}
                </button>
              </div>

              {formData.latitude && (
                <button
                  type="button"
                  onClick={checkNearbyIssues}
                  disabled={checkingNearby}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2 font-black ml-1 transition-all"
                >
                  {checkingNearby ? <Loader2 size={14} className="animate-spin" /> : <Layers size={14} />}
                  Check for similar reports in this area
                </button>
              )}
            </div>

            {/* Evidence Section */}
            <div className="space-y-3">
              <label className="text-sm font-black text-gray-700 dark:text-gray-300 uppercase tracking-widest ml-1 flex items-center gap-2">
                <Camera size={14} className="text-blue-600" />
                Visual Evidence
              </label>

              <div className="grid grid-cols-2 gap-4">
                <label className="group cursor-pointer bg-white dark:bg-gray-800 rounded-3xl border-2 border-dashed border-gray-200 dark:border-gray-700 p-6 text-center hover:border-blue-600 dark:hover:border-blue-400 transition-all flex flex-col items-center justify-center gap-3">
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-2xl group-hover:scale-110 transition-transform text-gray-400 group-hover:text-blue-600">
                    <ImageIcon size={32} />
                  </div>
                  <span className="font-black text-sm text-gray-900 dark:text-white">Upload Gallery</span>
                  <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
                </label>

                <label className="group cursor-pointer bg-blue-50/50 dark:bg-blue-900/20 rounded-3xl border-2 border-dashed border-blue-200 dark:border-blue-800 p-6 text-center hover:border-blue-600 dark:hover:border-blue-400 transition-all flex flex-col items-center justify-center gap-3">
                  <div className="p-4 bg-blue-100 dark:bg-blue-900 rounded-2xl group-hover:scale-110 transition-transform text-blue-600">
                    <Camera size={32} />
                  </div>
                  <span className="font-black text-sm text-blue-800 dark:text-blue-200">Snap Photo</span>
                  <input type="file" accept="image/*" capture="environment" className="hidden" onChange={handleImageChange} />
                </label>
              </div>

              {/* Image Preview & Analysis Hub */}
              <AnimatePresence>
                {formData.image && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="space-y-4 pt-2"
                  >
                    <div className="relative rounded-3xl overflow-hidden shadow-xl border-4 border-white dark:border-gray-800">
                      {uploading && (
                        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-10">
                          <div className="flex flex-col items-center gap-3">
                            <Loader2 size={40} className="animate-spin text-white" />
                            <span className="text-white font-black uppercase tracking-widest text-xs">Optimizing Image...</span>
                          </div>
                        </div>
                      )}

                      {/* Depth Map Preview */}
                      {depthMap ? (
                        <div className="grid grid-cols-2 gap-1 bg-gray-900">
                          <img src={URL.createObjectURL(formData.image)} alt="Original" className="w-full h-48 object-cover opacity-80" />
                          <img src={`data:image/jpeg;base64,${depthMap}`} alt="Depth map" className="w-full h-48 object-cover" />
                        </div>
                      ) : (
                        <img src={URL.createObjectURL(formData.image)} alt="Issue" className="w-full h-64 object-cover" />
                      )}
                    </div>

                    {/* AI Severity Analysis Widget */}
                    {!depthMap && !analyzingDepth && (
                      <button
                        type="button"
                        onClick={analyzeDepth}
                        className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-black text-sm shadow-xl shadow-blue-600/20 flex items-center justify-center gap-3 hover:scale-[1.02] transition-transform"
                      >
                        <Layers size={20} />
                        Run AI Depth Severity Analysis
                      </button>
                    )}

                    {analyzingDepth && (
                      <div className="w-full p-4 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center gap-3">
                        <div className="flex gap-1">
                          {[0, 1, 2].map(i => (
                            <motion.div
                              key={i}
                              animate={{ scaleY: [1, 2, 1] }}
                              transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                              className="w-1 h-3 bg-blue-600"
                            />
                          ))}
                        </div>
                        <span className="text-xs font-black uppercase tracking-widest text-gray-500">Generating 3D spatial map...</span>
                      </div>
                    )}

                    <AnimatePresence>
                      {(analyzing || severity || analysisErrors.severity) && (
                        <motion.div
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`p-6 rounded-3xl border shadow-xl ${severity?.level === 'Critical' ? 'bg-rose-50 border-rose-100 text-rose-900' :
                            severity?.level === 'High' ? 'bg-amber-50 border-amber-100 text-amber-900' :
                              'bg-emerald-50 border-emerald-100 text-emerald-900'
                            }`}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-xl bg-white shadow-sm ${severity?.level === 'Critical' ? 'text-rose-600' : 'text-emerald-600'}`}>
                                <Zap size={18} />
                              </div>
                              <h5 className="font-black uppercase tracking-widest text-xs">AI Impact Analysis</h5>
                            </div>
                            {severity && (
                              <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${severity.level === 'Critical' ? 'bg-rose-200 text-rose-900' : 'bg-emerald-200 text-emerald-900'
                                }`}>
                                {severity.level} Match
                              </span>
                            )}
                          </div>

                          {analyzing ? (
                            <div className="flex items-center gap-3 text-blue-600 animate-pulse">
                              <Loader2 size={16} className="animate-spin" />
                              <span className="text-sm font-black">AI Calculating Severity...</span>
                            </div>
                          ) : severity ? (
                            <div className="space-y-4">
                              <p className="text-sm font-medium leading-relaxed">
                                Our vision engine detected a <span className="font-black underline">{severity.raw_label}</span>.
                                We've flagged this for priority processing based on visual indicators.
                              </p>
                              <div className="w-full h-2 bg-white/50 rounded-full overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${severity.confidence * 100}%` }}
                                  className={`h-full ${severity.level === 'Critical' ? 'bg-rose-500' : 'bg-emerald-500'}`}
                                />
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-rose-600">
                              <AlertTriangle size={16} />
                              <span className="text-xs font-black">{analysisErrors.severity}</span>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Submit Section */}
            <div className="pt-6 space-y-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 rounded-3xl font-black text-xl shadow-2xl shadow-blue-600/30 flex items-center justify-center gap-3 transition-all disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin" size={24} /> : isOnline ? <Zap size={24} /> : <CheckCircle2 size={24} />}
                {loading ? 'Processing Mission…' : isOnline ? 'Generate Action Plan' : 'Commit Offline'}
              </motion.button>

              <div className="flex items-center justify-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></div>
                <span className={`text-xs font-black uppercase tracking-widest ${isOnline ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {isOnline ? 'System Live - Real-time Sync' : 'Network Offline - Secure Vault Storage'}
                </span>
              </div>

              {submitStatus.state !== 'idle' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-5 rounded-2xl border flex items-center gap-4 ${submitStatus.state === 'success' ? 'bg-emerald-50 border-emerald-100 text-emerald-800' :
                    submitStatus.state === 'pending' ? 'bg-blue-50 border-blue-100 text-blue-800' :
                      'bg-rose-50 border-rose-100 text-rose-800'
                    }`}
                >
                  <div className={`p-2 rounded-xl bg-white shadow-sm ${submitStatus.state === 'success' ? 'text-emerald-600' :
                    submitStatus.state === 'pending' ? 'text-blue-600' : 'text-rose-600'
                    }`}>
                    {submitStatus.state === 'success' ? <CheckCircle2 size={20} /> :
                      submitStatus.state === 'pending' ? <Loader2 size={20} className="animate-spin" /> :
                        <AlertTriangle size={20} />}
                  </div>
                  <span className="text-sm font-black">{submitStatus.message}</span>
                </motion.div>
              )}

              <button
                type="button"
                onClick={() => setView('home')}
                className="w-full text-center text-gray-400 dark:text-gray-500 text-sm font-black uppercase tracking-widest hover:text-gray-600 dark:hover:text-gray-300 transition-colors py-4"
              >
                Abort Reporting
              </button>
            </div>
          </form>
        </div>
      </motion.div>

      {/* Nearby Issues Overlay - Professional Modal */}
      <AnimatePresence>
        {showNearbyModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowNearbyModal(false)}
              className="absolute inset-0 bg-gray-950/80 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-lg bg-white dark:bg-gray-900 rounded-[2.5rem] shadow-2xl shadow-blue-500/10 overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-8 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50">
                <div className="space-y-1">
                  <h3 className="text-2xl font-black text-gray-900 dark:text-white">Nearby Activity</h3>
                  <p className="text-xs font-black uppercase tracking-widest text-indigo-600">{nearbyIssues.length} Matches Detected</p>
                </div>
                <button onClick={() => setShowNearbyModal(false)} className="p-3 bg-white dark:bg-gray-700 rounded-2xl shadow-sm hover:scale-110 transition-transform">
                  <XCircle size={24} className="text-gray-400" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-4 custom-scrollbar">
                {nearbyIssues.length === 0 ? (
                  <div className="py-12 text-center space-y-4">
                    <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto text-emerald-600">
                      <CheckCircle2 size={32} />
                    </div>
                    <div>
                      <h4 className="font-black text-gray-900 dark:text-white">Safe Zone</h4>
                      <p className="text-sm text-gray-500">No overlapping issues found. Your report is unique!</p>
                    </div>
                  </div>
                ) : (
                  nearbyIssues.map((issue, idx) => (
                    <motion.div
                      key={issue.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="group p-5 bg-gray-50 dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 hover:border-indigo-600 dark:hover:border-indigo-400 transition-all"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <span className="px-3 py-1 bg-white dark:bg-gray-700 rounded-full text-[10px] font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400 shadow-sm">
                          {issue.category}
                        </span>
                        <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-gray-400">
                          <MapPin size={10} />
                          {Math.round(issue.distance_meters)}m
                        </div>
                      </div>
                      <p className="text-sm font-bold text-gray-800 dark:text-white leading-relaxed mb-4">{issue.description}</p>
                      <div className="flex justify-between items-center bg-white/50 dark:bg-gray-700/50 p-3 rounded-2xl border border-white/50 dark:border-gray-600/50">
                        <div className="flex gap-3">
                          <div className="flex items-center gap-1 text-blue-600">
                            <ThumbsUp size={12} />
                            <span className="text-xs font-black">{issue.upvotes}</span>
                          </div>
                          <div className="flex items-center gap-1 text-emerald-600 font-black text-xs uppercase tracking-tighter">
                            {issue.status}
                          </div>
                        </div>
                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                          {new Date(issue.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              <div className="p-8 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-800">
                <button
                  onClick={() => setShowNearbyModal(false)}
                  className="w-full bg-gray-900 dark:bg-blue-600 text-white py-5 rounded-2xl font-black text-lg shadow-xl hover:scale-[1.02] transition-transform"
                >
                  {nearbyIssues.length > 0 ? "Commit New Independent Report" : "Proceed with Clearance"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ReportForm;
