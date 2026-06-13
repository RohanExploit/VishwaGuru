import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

const ReportForm = () => {
  const [formData, setFormData] = useState({ description: '', category: 'road', image: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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
      // Pass action plan via state
      navigate('/action', { state: { actionPlan: data.action_plan } });
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
       {error && <div className="text-red-500 mb-2">{error}</div>}
       <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Category</label>
            <select
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
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

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Generate Action Plan'}
          </button>
          <button type="button" onClick={() => navigate('/')} className="mt-2 text-blue-600 underline text-center w-full block">Cancel</button>
       </form>
    </div>
  );
};

export default ReportForm;
