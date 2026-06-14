import React, { useState, useEffect, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import ChatWidget from './components/ChatWidget';

// Lazy Load Views
const Landing = React.lazy(() => import('./views/Landing'));
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
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

function Layout({ children }) {
    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
            <ChatWidget />
            <div className="bg-white shadow-xl rounded-2xl p-6 max-w-lg w-full mt-6 mb-24 border border-gray-100">
                <header className="text-center mb-6">
                    <Link to="/">
                        <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-blue-600 cursor-pointer">
                            VishwaGuru
                        </h1>
                    </Link>
                    <p className="text-gray-500 text-sm mt-1">
                        Empowering Citizens, Solving Problems.
                    </p>
                </header>
                {children}
            </div>
        </div>
    );
}

function App() {
  const [recentIssues, setRecentIssues] = useState([]);

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

  useEffect(() => {
    fetchRecentIssues();
  }, []);

  const handleUpvote = async (id) => {
    try {
        const response = await fetch(`${API_URL}/api/issues/${id}/vote`, {
            method: 'POST'
        });
        if (response.ok) {
            // Update local state to reflect change immediately (optimistic UI or re-fetch)
            setRecentIssues(prev => prev.map(issue =>
                issue.id === id ? { ...issue, upvotes: (issue.upvotes || 0) + 1 } : issue
            ));
        }
    } catch (e) {
        console.error("Failed to upvote", e);
    }
  };

  return (
    <BrowserRouter>
        <Layout>
            <Suspense fallback={
              <div className="flex justify-center my-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            }>
                <Routes>
                    <Route path="/" element={<Home recentIssues={recentIssues} handleUpvote={handleUpvote} />} />
                    <Route path="/map" element={<MapView />} />
                    <Route path="/report" element={<ReportForm />} />
                    <Route path="/action" element={<ActionView />} />
                    <Route path="/mh-rep" element={<MaharashtraRepView />} />
                    <Route path="/pothole" element={<PotholeDetector />} />
                    <Route path="/garbage" element={<GarbageDetector />} />
                    <Route path="/vandalism" element={<VandalismDetector />} />
                    <Route path="/flood" element={<FloodDetector />} />
                    <Route path="/infrastructure" element={<InfrastructureDetector />} />
                </Routes>
            </Suspense>
        </Layout>
    </BrowserRouter>
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
