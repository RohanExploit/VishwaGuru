import React, { useState, useEffect, Suspense, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fakeRecentIssues, fakeResponsibilityMap } from './fakeData';
import { issuesApi, miscApi } from './api';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import FloatingButtonsManager from './components/FloatingButtonsManager';
import LoadingSpinner from './components/LoadingSpinner';
import { DarkModeProvider, useDarkMode } from './contexts/DarkModeContext';

// Lazy Load Views
const Landing = React.lazy(() => import('./views/Landing'));
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
const ReportForm = React.lazy(() => import('./views/ReportForm'));
const ActionView = React.lazy(() => import('./views/ActionView'));
const MaharashtraRepView = React.lazy(() => import('./views/MaharashtraRepView'));
const VerifyView = React.lazy(() => import('./views/VerifyView'));
const TrackView = React.lazy(() => import('./views/TrackView'));
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


// Auth Components
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './views/Login';
import ProtectedRoute from './components/ProtectedRoute';
import AdminDashboard from './views/AdminDashboard';

const VALID_VIEWS = ['home', 'map', 'report', 'action', 'mh-rep', 'pothole', 'garbage', 'vandalism', 'flood', 'infrastructure', 'parking', 'streetlight', 'fire', 'animal', 'blocked', 'tree', 'pest', 'smart-scan', 'grievance-analysis', 'leaderboard', 'stats', 'grievance'];

// Create a wrapper component to handle state management
function AppContent() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { isDarkMode } = useDarkMode();
  const { user, loading: authLoading } = useAuth();
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [stats, setStats] = useState({ total_issues: 0, resolved_issues: 0, pending_issues: 0 });
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Safe navigation helper with validation
  const navigateToView = useCallback((view) => {
    // Handle paths vs view names
    const viewName = view.startsWith('/') ? view.substring(1) : view;
    // Simple check for valid views or just navigate
    if (view === 'home' || view === '/') {
        navigate('/');
    } else {
        navigate(`/${viewName}`);
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
      // Removed automatic navigate('/map') from here to prevent loops
    } catch (error) {
      console.error("Failed to fetch responsibility map", error);
      setResponsibilityMap(fakeResponsibilityMap);
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // Initialize on mount
  useEffect(() => {
    fetchResponsibilityMap();
    fetchRecentIssues();

    // Fetch system stats
    miscApi.getStats()
      .then(data => setStats(data))
      .catch(err => console.error("Failed to fetch stats", err));
  }, [fetchRecentIssues, fetchResponsibilityMap]);

  // Handle Auth Loading to prevent blinking
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-950">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  // Check if we're on the landing page
  const isLandingPage = location.pathname === '/';

  // If on landing page and NOT logged in, render it without the main layout
  if (isLandingPage && !user) {
    return (
      <Suspense fallback={
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      }>
        <Landing />
      </Suspense>
    );
  }

  // Otherwise render the main app layout
  return (
    <div className={`min-h-screen relative overflow-hidden font-sans transition-colors duration-300 ${isDarkMode ? 'dark bg-gray-950 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Animated background elements - Optimized for performance */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div
          className="absolute top-1/4 left-1/4 w-72 h-72 bg-orange-300/10 dark:bg-orange-300/5 rounded-full blur-3xl animate-pulse-slow transition-colors duration-300"
          style={{ willChange: 'opacity' }}
        ></div>
        <div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-300/10 dark:bg-blue-300/5 rounded-full blur-3xl animate-pulse-slow animation-delay-1000 transition-colors duration-300"
          style={{ willChange: 'opacity' }}
        ></div>
      </div>

      <div className="relative z-10">
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
                  loadMoreIssues={loadMoreIssues}
                  hasMore={hasMore}
                  loadingMore={loadingMore}
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
            <Route
              path="/verify/:id"
              element={<VerifyView />}
            />
            <Route
              path="/track"
              element={<TrackView />}
            />
            <Route
              path="/track/:id"
              element={<TrackView />}
            />
            <Route
              path="/leaderboard"
              element={<LeaderboardView />}
            />
            <Route
              path="/stats"
              element={<StatsView />}
            />
             <Route
              path="/grievance"
              element={<GrievanceView />}
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
                  <CivicEyeDetector onBack={() => navigate('/')} />
                </div>
              } />
              <Route path="/my-reports" element={
                <ProtectedRoute>
                  <MyReportsView />
                </ProtectedRoute>
              } />
              <Route path="/grievance" element={
                <ProtectedRoute>
                  <GrievanceView />
                </ProtectedRoute>
              } />
              <Route path="/insight" element={
                <ProtectedRoute>
                  <CivicInsight />
                </ProtectedRoute>
              } />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
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
