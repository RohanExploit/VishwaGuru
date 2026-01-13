import React, { useState, useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import ChatWidget from './components/ChatWidget';
import { fakeRecentIssues, fakeResponsibilityMap } from './fakeData';

// Lazy Load Views
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
const ReportForm = React.lazy(() => import('./views/ReportForm'));
const ActionView = React.lazy(() => import('./views/ActionView'));
const MaharashtraRepView = React.lazy(() => import('./views/MaharashtraRepView'));
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

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

// Create a wrapper component to handle state management
function AppContent() {
  const navigate = useNavigate();
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Safe navigation helper
  const navigateToView = (view) => {
    const validViews = ['home', 'map', 'report', 'action', 'mh-rep', 'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure', 'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree', 'pest'];
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

  // Responsibility Map Logic
  const fetchResponsibilityMap = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/responsibility-map`);
      if (!response.ok) throw new Error('Failed to fetch data');
      const data = await response.json();
      setResponsibilityMap(data);
      navigate('/map');
    } catch (err) {
      console.error("Failed to fetch responsibility map, using fake data", err);
      setResponsibilityMap(fakeResponsibilityMap);
      navigate('/map');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <ChatWidget />
      <div className="bg-white shadow-xl rounded-2xl p-6 max-w-lg w-full mt-6 mb-24 border border-gray-100">
        <header className="text-center mb-6">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-blue-600">
            VishwaGuru
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Empowering Citizens, Solving Problems.
          </p>
        </header>

        {loading && (
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center my-4">
            {error}
          </div>
        )}

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
            <Route
              path="/report"
              element={
                <ReportForm
                  setView={navigateToView}
                  setLoading={setLoading}
                  setError={setError}
                  setActionPlan={setActionPlan}
                  loading={loading}
                />
              }
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
            <Route path="/pest" element={<PestDetector onBack={() => navigate('/')} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>

      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
