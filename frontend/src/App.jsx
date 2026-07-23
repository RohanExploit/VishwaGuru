import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import ChatWidget from './components/ChatWidget';
import { issuesApi, miscApi } from './api';
import { fakeRecentIssues, fakeResponsibilityMap } from './fakeData';
import ErrorBoundary from './components/ErrorBoundary';
// Lazy-load view components
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
const ReportForm = React.lazy(() => import('./views/ReportForm'));
const ActionView = React.lazy(() => import('./views/ActionView'));
const MaharashtraRepView = React.lazy(() => import('./views/MaharashtraRepView'));
const NotFound = React.lazy(() => import('./views/NotFound'));

// Lazy-load detector components
const PotholeDetector = React.lazy(() => import('./features/detectors/PotholeDetector'));
const GarbageDetector = React.lazy(() => import('./features/detectors/GarbageDetector'));
const VandalismDetector = React.lazy(() => import('./features/detectors/VandalismDetector'));
const FloodDetector = React.lazy(() => import('./features/detectors/FloodDetector'));
const InfrastructureDetector = React.lazy(() => import('./features/detectors/InfrastructureDetector'));
const IllegalParkingDetector = React.lazy(() => import('./features/detectors/IllegalParkingDetector'));
const StreetLightDetector = React.lazy(() => import('./features/detectors/StreetLightDetector'));
const FireDetector = React.lazy(() => import('./features/detectors/FireDetector'));
const StrayAnimalDetector = React.lazy(() => import('./features/detectors/StrayAnimalDetector'));
const BlockedRoadDetector = React.lazy(() => import('./features/detectors/BlockedRoadDetector'));
const TreeDetector = React.lazy(() => import('./features/detectors/TreeDetector'));

// ─── Valid view paths for navigation safety ────────────────────────────────────
const VALID_VIEWS = [
  'home', 'map', 'report', 'action', 'mh-rep',
  'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure',
  'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree'
];

// ─── Enhanced header component with animated gradient ──────────────────────────
const AppHeader = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`sticky top-0 z-40 transition-all duration-500 ${isScrolled ? 'py-4 bg-white/95 backdrop-blur-lg shadow-lg' : 'py-8'}`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="inline-block transform transition-all duration-700 hover:scale-[1.03]">
            <h1 className="text-5xl md:text-6xl font-black bg-gradient-to-r from-orange-500 via-orange-600 to-blue-600 bg-clip-text text-transparent animate-gradient tracking-tighter">
              VishwaGuru
            </h1>
            <div className="h-1.5 w-32 mx-auto mt-4 bg-gradient-to-r from-orange-500 to-blue-500 rounded-full animate-pulse-slow"></div>
          </div>
          <p className="text-gray-600 font-medium mt-4 text-lg md:text-xl max-w-3xl mx-auto leading-relaxed">
            Empowering Citizens, Solving Problems &mdash; A Smart Civic Engagement Platform
          </p>
        </div>
      </div>
    </header>
  );
};

// ─── Floating action button for quick actions ──────────────────────────────────
const FloatingActions = ({ setView }) => {
  const [isOpen, setIsOpen] = useState(false);

  const quickActions = [
    { label: 'Report Issue', icon: '\u{1F4DD}', view: 'report', bgColor: 'from-green-500 to-emerald-600' },
    { label: 'Detect Pothole', icon: '\u{1F4F7}', view: 'pothole', bgColor: 'from-blue-500 to-cyan-600' },
    { label: 'View Map', icon: '\u{1F5FA}', view: 'map', bgColor: 'from-purple-500 to-indigo-600' },
    { label: 'Emergency', icon: '\u{1F6A8}', view: 'fire', bgColor: 'from-red-500 to-orange-600' },
  ];

  return (
    <div className="fixed bottom-28 right-8 z-40 flex flex-col items-end space-y-3">
      {isOpen && (
        <div className="space-y-3 animate-fadeInUp">
          {quickActions.map((action) => (
            <button
              key={action.view}
              onClick={() => {
                setView(action.view);
                setIsOpen(false);
              }}
              className={`flex items-center gap-3 bg-gradient-to-r ${action.bgColor} text-white shadow-xl rounded-full px-5 py-3 hover:shadow-2xl transform hover:scale-105 transition-all duration-300 group min-w-[180px] justify-end`}
            >
              <span className="text-lg transform group-hover:scale-110 transition-transform duration-300">
                {action.icon}
              </span>
              <span className="text-sm font-medium whitespace-nowrap">
                {action.label}
              </span>
            </button>
          ))}
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`h-14 w-14 rounded-full shadow-2xl hover:shadow-3xl transform transition-all duration-300 flex items-center justify-center ${isOpen
          ? 'bg-gradient-to-r from-gray-600 to-gray-800 rotate-45 scale-105'
          : 'bg-gradient-to-r from-orange-500 to-blue-600 hover:scale-105'
          }`}
        aria-label={isOpen ? 'Close quick actions' : 'Open quick actions'}
      >
        <svg
          className="w-6 h-6 text-white transform transition-transform duration-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={isOpen ? "M6 18L18 6M6 6l12 12" : "M12 4v16m8-8H4"}
          />
        </svg>
      </button>
    </div>
  );
};

// ─── Enhanced ChatWidget wrapper ───────────────────────────────────────────────
const EnhancedChatWidget = () => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="fixed bottom-8 right-8 z-50">
      <div
        className="relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className={`absolute right-16 -top-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-3 py-1 rounded-lg shadow-lg transition-all duration-300 ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4 pointer-events-none'
          }`}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">AI Assistant</span>
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          </div>
        </div>

        <div className={`transform transition-all duration-300 ${isHovered ? 'scale-110 rotate-3' : ''
          }`}>
          <ChatWidget />
        </div>

        <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
      </div>
    </div>
  );
};

// ─── Floating buttons manager ──────────────────────────────────────────────────
const FloatingButtonsManager = ({ setView }) => (
  <>
    <EnhancedChatWidget />
    <FloatingActions setView={setView} />
  </>
);

// ─── App content with state management ─────────────────────────────────────────
function AppContent() {
  const navigate = useNavigate();
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Auto-dismiss alerts after 5s
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // Safe navigation helper
  const navigateToView = useCallback((view) => {
    if (VALID_VIEWS.includes(view.split('/')[0])) {
      navigate(view === 'home' ? '/' : `/${view}`);
    } else {
      console.warn(`Attempted to navigate to invalid view: ${view}`);
      navigate('/');
    }
  }, [navigate]);

  // Fetch recent issues
  const fetchRecentIssues = useCallback(async () => {
    setLoading(true);
    try {
      const data = await issuesApi.getRecent();
      setRecentIssues(data);
    } catch (err) {
      console.error("Failed to fetch recent issues, using fake data", err);
      setRecentIssues(fakeRecentIssues);
      setError("Using sample data - unable to connect to server");
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle upvote with optimistic update
  const handleUpvote = useCallback(async (id) => {
    const originalIssues = [...recentIssues];
    try {
      setRecentIssues(prev => prev.map(issue =>
        issue.id === id ? { ...issue, upvotes: (issue.upvotes || 0) + 1 } : issue
      ));
      await issuesApi.vote(id);
    } catch (err) {
      console.error("Failed to upvote", err);
      setRecentIssues(originalIssues);
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
      navigate('/map');
    } catch (err) {
      console.error("Failed to fetch responsibility map", err);
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

        {/* Alert banners */}
        {error && (
          <div className="max-w-6xl mx-auto px-4 mt-2">
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-lg text-sm animate-fadeIn">
              {error}
            </div>
          </div>
        )}
        {success && (
          <div className="max-w-6xl mx-auto px-4 mt-2">
            <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-3 rounded-lg text-sm animate-fadeIn">
              {success}
            </div>
          </div>
        )}

<ErrorBoundary>
        <Suspense fallback={
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
        }>
          <Routes>          <Route path="/home" element={<Navigate to="/" replace />} />
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
              element={<MapView responsibilityMap={responsibilityMap} setView={navigateToView} />}
            />
            <Route
              path="/report"
              element={
                <ReportForm
  setView={navigateToView}
  setLoading={setLoading}
  setError={setError}
  setActionPlan={setActionPlan}
  fetchRecentIssues={fetchRecentIssues}
  loading={loading}
/>
              }
            />
            <Route
              path="/action"
element={<ActionView actionPlan={actionPlan} setActionPlan={setActionPlan} setView={navigateToView} />}            />
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
            {/* Detector routes */}
            <Route path="/pothole" element={<PotholeDetector onBack={() => navigate('/')} />} />
            <Route path="/garbage" element={<GarbageDetector onBack={() => navigate('/')} />} />
            <Route path="/vandalism" element={<VandalismDetector onBack={() => navigate('/')} />} />
            <Route path="/flood" element={<FloodDetector onBack={() => navigate('/')} />} />
            <Route path="/infrastructure" element={<InfrastructureDetector onBack={() => navigate('/')} />} />
            <Route path="/parking" element={<IllegalParkingDetector onBack={() => navigate('/')} />} />
            <Route path="/streetlight" element={<StreetLightDetector onBack={() => navigate('/')} />} />
            <Route path="/fire" element={<FireDetector onBack={() => navigate('/')} />} />
            <Route path="/animal" element={<StrayAnimalDetector onBack={() => navigate('/')} />} />
            <Route path="/blocked" element={<BlockedRoadDetector onBack={() => navigate('/')} />} />
            <Route path="/tree" element={<TreeDetector onBack={() => navigate('/')} />} />
            <Route path="*" element={<NotFound />} />
</Routes>
        </Suspense>
        </ErrorBoundary>      </div>
    </div>
  );
}

// ─── Global Styles ─────────────────────────────────────────────────────────────
const GlobalStyles = () => (
  <style>{`
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
    @keyframes pulse-slow {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 0.8; }
    }
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }
    .animate-fadeIn { animation: fadeIn 0.5s ease-out; }
    .animate-fadeInUp { animation: fadeInUp 0.6s ease-out; }
    .animate-gradient { background-size: 200% auto; animation: gradient 3s ease infinite; }
    .animate-pulse-slow { animation: pulse-slow 3s ease-in-out infinite; }
    .animate-float { animation: float 3s ease-in-out infinite; }
    .animation-delay-1000 { animation-delay: 1s; }
    .animation-delay-2000 { animation-delay: 2s; }

    html { scroll-behavior: smooth; }

    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); border-radius: 5px; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(to bottom, #f97316, #3b82f6); border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(to bottom, #ea580c, #2563eb); }

    ::selection { background: rgba(249, 115, 22, 0.3); color: #1f2937; }
  `}</style>
);

// ─── Main App Component ────────────────────────────────────────────────────────
function App() {
  return (
    <Router>
      <AppContent />
      <GlobalStyles />
    </Router>
  );
}

export default App;
