import React, { useState, useEffect } from 'react';
import { getMaharashtraRepContacts } from './api/location';
import PotholeDetector from './PotholeDetector';
import GarbageDetector from './GarbageDetector';
import NoiseDetector from './NoiseDetector';
import VandalismDetector from './VandalismDetector';
import ChatWidget from './components/ChatWidget';
import { AlertTriangle, MapPin, Search, Activity, Camera, Trash2, ThumbsUp, Volume2, SprayCan } from 'lucide-react';

// Lazy loaded components
const ChatWidget = React.lazy(() => import('./components/ChatWidget'));

function App() {
  const [view, setView] = useState('home'); // home, map, report, action, mh-rep, pothole, garbage, noise, vandalism
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Safe navigation helper
  const navigateToView = (view) => {
    const validViews = ['home', 'map', 'report', 'action', 'mh-rep', 'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure', 'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree'];
    if (validViews.includes(view)) {
      navigate(view === 'home' ? '/' : `/${view}`);
    }
  };

  // Fetch recent issues on mount
  const fetchRecentIssues = async () => {
    try {
      const response = await fetch(`${API_URL}/api/issues/recent`);
      if (response.ok) {
        const data = await response.json();
        setRecentIssues(data);
      } else {
        throw new Error("Failed to fetch");
      }
    } catch (e) {
      console.error("Failed to fetch recent issues, using fake data", e);
      setRecentIssues(fakeRecentIssues);
    }
  };

  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // Safe navigation helper with validation
  const navigateToView = useCallback((view) => {
    if (VALID_VIEWS.includes(view.split('/')[0])) {
      navigate(`/${view}`);
    } else {
      console.warn(`Attempted to navigate to invalid view: ${view}`);
      navigate('/home');
    }
  }, [navigate]);

        <button
          onClick={() => setView('pothole')}
          className="flex flex-col items-center justify-center bg-red-50 border-2 border-red-100 p-4 rounded-xl hover:bg-red-100 transition shadow-sm h-32"
        >
          <div className="bg-red-500 text-white p-3 rounded-full mb-2">
            <Camera size={24} />
          </div>
          <span className="font-semibold text-red-800">Detect Pothole</span>
        </button>

        <button
          onClick={() => setView('garbage')}
          className="flex flex-col items-center justify-center bg-orange-50 border-2 border-orange-100 p-4 rounded-xl hover:bg-orange-100 transition shadow-sm h-32"
        >
          <div className="bg-orange-500 text-white p-3 rounded-full mb-2">
            <Trash2 size={24} />
          </div>
          <span className="font-semibold text-orange-800">Detect Garbage</span>
        </button>

        <button
          onClick={() => setView('noise')}
          className="flex flex-col items-center justify-center bg-teal-50 border-2 border-teal-100 p-4 rounded-xl hover:bg-teal-100 transition shadow-sm h-32"
        >
          <div className="bg-teal-500 text-white p-3 rounded-full mb-2">
            <Volume2 size={24} />
          </div>
          <span className="font-semibold text-teal-800">Noise Level</span>
        </button>

        {/* New Feature: Vandalism Detector (Placeholder until VandalismDetector component is created, or re-use Report form)
            For now, let's assume we use the same PotholeDetector logic but with different endpoint,
            or just a button to Report view with category pre-selected.
            Actually, let's reuse Report view for now or better, create a simple VandalismDetector component later.
            Wait, I promised to use HF model. I should make a VandalismDetector component.
        */}
        <button
           onClick={() => setView('vandalism')}
           className="flex flex-col items-center justify-center bg-indigo-50 border-2 border-indigo-100 p-4 rounded-xl hover:bg-indigo-100 transition shadow-sm h-32"
        >
           <div className="bg-indigo-500 text-white p-3 rounded-full mb-2">
             <SprayCan size={24} />
           </div>
           <span className="font-semibold text-indigo-800">Scan Vandalism</span>
        </button>

        <button
          onClick={() => setView('mh-rep')}
          className="flex flex-col items-center justify-center bg-purple-50 border-2 border-purple-100 p-4 rounded-xl hover:bg-purple-100 transition shadow-sm h-32"
        >
          <div className="bg-purple-500 text-white p-3 rounded-full mb-2">
            <Search size={24} />
          </div>
          <span className="font-semibold text-purple-800">Find MLA</span>
        </button>
      </div>

      <div className="grid grid-cols-1">
         <button
          onClick={fetchResponsibilityMap}
          className="flex flex-row items-center justify-center bg-green-50 border-2 border-green-100 p-4 rounded-xl hover:bg-green-100 transition shadow-sm h-16"
        >
          <div className="bg-green-500 text-white p-2 rounded-full mr-3">
            <MapPin size={20} />
          </div>
          <span className="font-semibold text-green-800">Who is Responsible?</span>
        </button>
      </div>

      {/* Recent Activity Feed */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <Activity size={18} className="text-orange-500" />
          <h2 className="font-bold text-gray-800">Community Activity</h2>
        </div>
        <div className="divide-y divide-gray-50 max-h-60 overflow-y-auto">
          {recentIssues.length > 0 ? (
            recentIssues.map((issue) => (
              <div key={issue.id} className="p-3 hover:bg-gray-50 transition">
                <div className="flex justify-between items-start">
                  <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 mb-1 capitalize">
                    {issue.category}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleUpvote(issue.id)}
                        className="flex items-center gap-1 text-gray-500 hover:text-blue-600 text-xs"
                    >
                        <ThumbsUp size={12} />
                        <span>{issue.upvotes || 0}</span>
                    </button>
                    <span className="text-xs text-gray-400">
                        {new Date(issue.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-700 line-clamp-2">{issue.description}</p>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-gray-500 text-sm">
              No recent activity to show.
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Responsibility Map Logic
  const fetchResponsibilityMap = async () => {
    setLoading(true);
    try {
      const data = await issuesApi.getRecent();
      setRecentIssues(data);
      setSuccess('Recent issues updated successfully');
    } catch (error) {
      console.error("Failed to fetch recent issues, using fake data", error);
      setRecentIssues(fakeRecentIssues);
      setError("Using sample data - unable to connect to server");
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle upvote with optimistic update
  const handleUpvote = useCallback(async (id) => {
    const originalUpvotes = [...recentIssues];
    try {
      setRecentIssues(prev => prev.map(issue =>
        issue.id === id ? { ...issue, upvotes: (issue.upvotes || 0) + 1 } : issue
      ));
      await issuesApi.vote(id);
      setSuccess('Upvote recorded successfully!');
    } catch (error) {
      console.error("Failed to upvote", error);
      setRecentIssues(originalUpvotes);
      setError("Failed to record upvote. Please try again.");
    }
  }, [recentIssues]);

  // Responsibility Map Logic
  const fetchResponsibilityMap = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await miscApi.getResponsibilityMap();
      setResponsibilityMap(data);
      setSuccess('Responsibility map loaded successfully');
      navigate('/map');
    } catch (error) {
      console.error("Failed to fetch responsibility map", error);
      setError("Using sample data - unable to load responsibility map");
      setResponsibilityMap(fakeResponsibilityMap);
      navigate('/map');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // Initialize on mount
  useEffect(() => {
    fetchRecentIssues();
  }, [fetchRecentIssues]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-100 text-gray-900 font-sans overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-orange-300/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-300/10 rounded-full blur-3xl animate-pulse-slow animation-delay-1000"></div>
      </div>

      <FloatingButtonsManager setView={navigateToView} />

      <div className="relative z-10">
        <AppHeader />

        <Suspense fallback={
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center my-4">
            {error}
          </div>
        )}

        {view === 'home' && <Home />}
        {view === 'map' && <MapView />}
        {view === 'report' && <ReportForm />}
        {view === 'action' && <ActionView />}
        {view === 'mh-rep' && <MaharashtraRepView />}
        {view === 'pothole' && <PotholeDetector onBack={() => setView('home')} />}
        {view === 'garbage' && <GarbageDetector onBack={() => setView('home')} />}
        {view === 'noise' && <NoiseDetector onBack={() => setView('home')} />}
        {/* Reuse GarbageDetector logic for Vandalism but change endpoint prop if possible,
            or copy component. Since GarbageDetector is specific, I'll assume we need a VandalismDetector.
            For now, I'll use GarbageDetector as a base but I need to pass the endpoint.
            I'll quickly create VandalismDetector.jsx which is a copy of GarbageDetector with different endpoint.
        */}
        {view === 'vandalism' && <VandalismDetector onBack={() => setView('home')} />}

      </div>
    </div>
  );
}

// Add custom animations to global styles
const GlobalStyles = () => (
  <style jsx global>{`
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes gradient {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }
    
    @keyframes gradient-slow {
      0%, 100% { opacity: 0.3; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.02); }
    }
    
    @keyframes pulse-slow {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 0.8; }
    }
    
    @keyframes loading-bar {
      0% { transform: translateX(-100%); }
      50% { transform: translateX(20%); }
      100% { transform: translateX(100%); }
    }
    
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }
    
    .animate-fadeIn {
      animation: fadeIn 0.5s ease-out;
    }
    
    .animate-fadeInUp {
      animation: fadeInUp 0.6s ease-out;
    }
    
    .animate-gradient {
      background-size: 200% auto;
      animation: gradient 3s ease infinite;
    }
    
    .animate-gradient-slow {
      animation: gradient-slow 6s ease-in-out infinite;
    }
    
    .animate-pulse-slow {
      animation: pulse-slow 3s ease-in-out infinite;
    }
    
    .animate-loading-bar {
      animation: loading-bar 1.5s ease-in-out infinite;
    }
    
    .animate-float {
      animation: float 3s ease-in-out infinite;
    }
    
    .animation-delay-1000 {
      animation-delay: 1s;
    }
    
    .animation-delay-2000 {
      animation-delay: 2s;
    }
    
    /* Smooth scroll behavior */
    html {
      scroll-behavior: smooth;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
      width: 10px;
    }
    
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.05);
      border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
      background: linear-gradient(to bottom, #f97316, #3b82f6);
      border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: linear-gradient(to bottom, #ea580c, #2563eb);
    }
    
    /* Selection color */
    ::selection {
      background: rgba(249, 115, 22, 0.3);
      color: #1f2937;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
      .floating-actions {
        bottom: 100px;
        right: 16px;
      }
      
      .floating-chat {
        bottom: 24px;
        right: 16px;
      }
    }
    
    @media (max-width: 480px) {
      .floating-actions {
        bottom: 120px;
        right: 12px;
      }
      
      .floating-chat {
        bottom: 20px;
        right: 12px;
      }
    }
  `}</style>
);

// Main App Component
function App() {
  return (
    <Router>
      <AppContent />
      <GlobalStyles />
    </Router>
  );
}

export default App;
