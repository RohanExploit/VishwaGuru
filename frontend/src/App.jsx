import React, { useState, useEffect, Suspense, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { fakeRecentIssues, fakeResponsibilityMap } from './fakeData';
import { issuesApi, miscApi } from './api';

// Lazy loaded components
const ChatWidget = React.lazy(() => import('./components/ChatWidget'));

// Lazy Load Views
const Landing = React.lazy(() => import('./views/Landing'));
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
const ImpactMapView = React.lazy(() => import('./views/ImpactMapView'));
const ReportForm = React.lazy(() => import('./views/ReportForm'));
const ActionView = React.lazy(() => import('./views/ActionView'));
const MaharashtraRepView = React.lazy(() => import('./views/MaharashtraRepView'));
const VerifyView = React.lazy(() => import('./views/VerifyView'));
const StatsView = React.lazy(() => import('./views/StatsView'));
const LeaderboardView = React.lazy(() => import('./views/LeaderboardView'));
const GrievanceView = React.lazy(() => import('./views/GrievanceView'));
const NotFound = React.lazy(() => import('./views/NotFound'));

// Lazy Load Detectors
const PotholeDetector = React.lazy(() => import('./PotholeDetector'));
const GarbageDetector = React.lazy(() => import('./GarbageDetector'));
const WasteDetector = React.lazy(() => import('./WasteDetector'));
const VandalismDetector = React.lazy(() => import('./VandalismDetector'));
const FloodDetector = React.lazy(() => import('./FloodDetector'));
const InfrastructureDetector = React.lazy(() => import('./InfrastructureDetector'));
const IllegalParkingDetector = React.lazy(() => import('./IllegalParkingDetector'));
const StreetLightDetector = React.lazy(() => import('./StreetLightDetector'));
const FireDetector = React.lazy(() => import('./FireDetector'));
const StrayAnimalDetector = React.lazy(() => import('./StrayAnimalDetector'));
const BlockedRoadDetector = React.lazy(() => import('./BlockedRoadDetector'));
const TreeDetector = React.lazy(() => import('./TreeDetector'));

// Loader
const Loader = () => (
  <div className="flex justify-center my-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
  </div>
);

function App() {
  const [view, setView] = useState('home'); // home, map, impact-map, report, action, mh-rep, pothole, garbage, vandalism, flood, infrastructure
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

  // Fetch recent issues
  const fetchRecentIssues = useCallback(async () => {
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
        }>
          <Routes>
            <Route
              path="/"
              element={
                <Home
                  setView={navigateToView}
                  fetchResponsibilityMap={fetchResponsibilityMap}
                  recentIssues={recentIssues}
                  handleUpvote={handleUpvote}
                />
              }
            />
            <Route
              path="/map"
              element={
                <MapView
                  responsibilityMap={responsibilityMap}
                  setView={navigateToView}
                />
              }
            />
          )}
          {view === 'impact-map' && (
            <ImpactMapView
              setView={setView}
            />
          )}
          {view === 'report' && (
            <ReportForm
              setView={setView}
              setLoading={setLoading}
              setError={setError}
              setActionPlan={setActionPlan}
              loading={loading}
            />
            <Route
              path="/action"
              element={
                <ActionView
                  actionPlan={actionPlan}
                  setView={navigateToView}
                />
              }
            />
            <Route
              path="/mh-rep"
              element={
                <MaharashtraRepView
                  setView={navigateToView}
                  setLoading={setLoading}
                  setError={setError}
                  setMaharashtraRepInfo={setMaharashtraRepInfo}
                  maharashtraRepInfo={maharashtraRepInfo}
                  loading={loading}
                />
              }
            />
            <Route path="/pothole" element={<PotholeDetector onBack={() => navigate('/')} />} />
            <Route path="/garbage" element={<GarbageDetector onBack={() => navigate('/')} />} />
            <Route
              path="/vandalism"
              element={
                <div className="flex flex-col h-full">
                  <button onClick={() => navigate('/')} className="self-start text-blue-600 mb-2">
                    &larr; Back
                  </button>
                  <VandalismDetector />
                </div>
              }
            />
            <Route
              path="/flood"
              element={
                <div className="flex flex-col h-full">
                  <button onClick={() => navigate('/')} className="self-start text-blue-600 mb-2">
                    &larr; Back
                  </button>
                  <FloodDetector />
                </div>
              }
            />
            <Route
              path="/infrastructure"
              element={<InfrastructureDetector onBack={() => navigate('/')} />}
            />
            <Route path="/parking" element={<IllegalParkingDetector onBack={() => navigate('/')} />} />
            <Route path="/streetlight" element={<StreetLightDetector onBack={() => navigate('/')} />} />
            <Route path="/fire" element={<FireDetector onBack={() => navigate('/')} />} />
            <Route path="/animal" element={<StrayAnimalDetector onBack={() => navigate('/')} />} />
            <Route path="/blocked" element={<BlockedRoadDetector onBack={() => navigate('/')} />} />
            <Route path="/tree" element={<TreeDetector onBack={() => navigate('/')} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>

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
