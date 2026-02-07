import React, { useState, useEffect, Suspense, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import ChatWidget from './components/ChatWidget';
import { fakeRecentIssues, fakeResponsibilityMap } from './fakeData';
import { issuesApi, miscApi } from './api';

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
const MyReportsView = React.lazy(() => import('./views/MyReportsView'));

// Create a wrapper component to handle state management
function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Safe navigation helper
  const navigateToView = useCallback((view) => {
    const validViews = ['home', 'map', 'report', 'action', 'mh-rep', 'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure', 'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree', 'pest', 'smart-scan', 'grievance-analysis', 'noise', 'safety-check', 'my-reports'];
    if (validViews.includes(view)) {
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
      const data = await issuesApi.getRecent(10, 0);
      setRecentIssues(data);
      setHasMore(data.length === 10);
      setSuccess('Recent issues updated successfully');
    } catch (error) {
      console.error("Failed to fetch recent issues, using fake data", error);
      setRecentIssues(fakeRecentIssues);
      setError("Using sample data - unable to connect to server");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load more issues
  const loadMoreIssues = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const offset = recentIssues.length;
      const data = await issuesApi.getRecent(10, offset);
      if (data.length < 10) setHasMore(false);
      setRecentIssues(prev => [...prev, ...data]);
    } catch (error) {
      console.error("Failed to load more issues", error);
      setError("Failed to load more issues");
    } finally {
      setLoadingMore(false);
    }
  }, [recentIssues.length, loadingMore, hasMore]);

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

  // Check if we're on the landing page
  const isLandingPage = location.pathname === '/';

  // If on landing page, render it without the main layout
  if (isLandingPage) {
    return (
      <Suspense fallback={
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
          <LoadingSpinner size="xl" variant="primary" />
        </div>
      }>
        <Landing />
      </Suspense>
    );
  }

  // Otherwise render the main app layout
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
                  setActionPlan={setActionPlan}
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
            <Route path="/smart-scan" element={<SmartScanner onBack={() => navigate('/')} />} />
            <Route path="/grievance-analysis" element={<GrievanceAnalysis onBack={() => navigate('/')} />} />
            <Route path="/noise" element={<NoiseDetector onBack={() => navigate('/')} />} />
            <Route path="/safety-check" element={
              <div className="flex flex-col h-full p-4">
                <button onClick={() => navigate('/')} className="self-start text-blue-600 mb-2 font-bold">
                  &larr; Back
                </button>
                <CivicEyeDetector onBack={() => navigate('/')} />
              </div>
            } />
            <Route path="/my-reports" element={<MyReportsView />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>

      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
