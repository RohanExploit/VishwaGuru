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
const VandalismDetector = React.lazy(() => import('./VandalismDetector'));
const FloodDetector = React.lazy(() => import('./FloodDetector'));
const InfrastructureDetector = React.lazy(() => import('./InfrastructureDetector'));
const IllegalParkingDetector = React.lazy(() => import('./IllegalParkingDetector'));
const StreetLightDetector = React.lazy(() => import('./StreetLightDetector'));
const FireDetector = React.lazy(() => import('./FireDetector'));
const StrayAnimalDetector = React.lazy(() => import('./StrayAnimalDetector'));
const BlockedRoadDetector = React.lazy(() => import('./BlockedRoadDetector'));
const TreeDetector = React.lazy(() => import('./TreeDetector'));
const PestDetector = React.lazy(() => import('./PestDetector'));
const SmartScanner = React.lazy(() => import('./SmartScanner'));
const GrievanceAnalysis = React.lazy(() => import('./views/GrievanceAnalysis'));
const NoiseDetector = React.lazy(() => import('./NoiseDetector'));
const CivicEyeDetector = React.lazy(() => import('./CivicEyeDetector'));
const CivicInsight = React.lazy(() => import('./views/CivicInsight'));
const MyReportsView = React.lazy(() => import('./views/MyReportsView'));
const TrafficSignDetector = React.lazy(() => import('./TrafficSignDetector'));
const AbandonedVehicleDetector = React.lazy(() => import('./AbandonedVehicleDetector'));

// Auth Components
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './views/Login';
import ProtectedRoute from './components/ProtectedRoute';
import AdminDashboard from './views/AdminDashboard';

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
  const navigateToView = useCallback((view) => {
    const validViews = ['home', 'map', 'report', 'action', 'mh-rep', 'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure', 'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree', 'pest', 'smart-scan', 'grievance-analysis', 'noise', 'safety-check', 'insight', 'my-reports', 'grievance', 'login', 'signup', 'traffic-sign', 'abandoned-vehicle'];
    if (validViews.includes(view)) {
      navigate(view === 'home' ? '/' : `/${view}`);
    } else {
      console.warn(`Attempted to navigate to invalid view: ${view}`);
      navigate('/');
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

// Main App Component
function App() {
  return (
    <Router>
      <DarkModeProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </DarkModeProvider>
    </Router>
  );
}

export default App;
