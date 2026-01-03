import React, { useState, useEffect, Suspense } from 'react';
import { getMaharashtraRepContacts } from './api/location';
import ChatWidget from './components/ChatWidget';

// Lazy Load Views
const Home = React.lazy(() => import('./views/Home'));
const MapView = React.lazy(() => import('./views/MapView'));
const ReportForm = React.lazy(() => import('./views/ReportForm'));
const ActionView = React.lazy(() => import('./views/ActionView'));
const MaharashtraRepView = React.lazy(() => import('./views/MaharashtraRepView'));

// Lazy Load Detectors
const PotholeDetector = React.lazy(() => import('./PotholeDetector'));
const GarbageDetector = React.lazy(() => import('./GarbageDetector'));
const VandalismDetector = React.lazy(() => import('./VandalismDetector'));
const FloodDetector = React.lazy(() => import('./FloodDetector'));
const InfrastructureDetector = React.lazy(() => import('./InfrastructureDetector'));
const TrafficDetector = React.lazy(() => import('./TrafficDetector'));

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [view, setView] = useState('home'); // home, map, report, action, mh-rep, pothole, garbage
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch recent issues on mount
  const fetchRecentIssues = async () => {
    try {
      const response = await fetch(`${API_URL}/api/issues/recent`);
      if (response.ok) {
        const data = await response.json();
        setRecentIssues(data);
      }
    } catch (e) {
      console.error("Failed to fetch recent issues", e);
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
      setView('map');
    } catch (err) {
      setError(err.message);
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

        {loading && !['report', 'mh-rep'].includes(view) && (
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
          {view === 'home' && (
            <Home
              setView={setView}
              fetchResponsibilityMap={fetchResponsibilityMap}
              recentIssues={recentIssues}
              handleUpvote={handleUpvote}
            />
          )}
          {view === 'map' && (
            <MapView
              responsibilityMap={responsibilityMap}
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
          )}
          {view === 'action' && (
            <ActionView
              actionPlan={actionPlan}
              setView={setView}
            />
          )}
          {view === 'mh-rep' && (
            <MaharashtraRepView
              setView={setView}
              setLoading={setLoading}
              setError={setError}
              setMaharashtraRepInfo={setMaharashtraRepInfo}
              maharashtraRepInfo={maharashtraRepInfo}
              loading={loading}
            />
          )}
          {view === 'pothole' && <PotholeDetector onBack={() => setView('home')} />}
          {view === 'garbage' && <GarbageDetector onBack={() => setView('home')} />}
          {view === 'vandalism' && (
            <div className="flex flex-col h-full">
              <button onClick={() => setView('home')} className="self-start text-blue-600 mb-2">
                 &larr; Back
              </button>
              <VandalismDetector />
            </div>
          )}
          {view === 'flood' && (
            <div className="flex flex-col h-full">
               <button onClick={() => setView('home')} className="self-start text-blue-600 mb-2">
                 &larr; Back
              </button>
              <FloodDetector />
            </div>
          )}
          {view === 'infrastructure' && (
             <InfrastructureDetector onBack={() => setView('home')} />
          )}
          {view === 'traffic' && (
             <TrafficDetector onBack={() => setView('home')} />
          )}
        </Suspense>

      </div>
    </div>
  );
}

export default App;
