import React, { useState, useEffect } from 'react';
import { getMaharashtraRepContacts } from './api/location';
import PotholeDetector from './PotholeDetector';
import ChatWidget from './components/ChatWidget';
import { AlertTriangle, MapPin, Search, Activity, Camera } from 'lucide-react';

// Lazy loaded components
const ChatWidget = React.lazy(() => import('./components/ChatWidget'));

function App() {
  const [view, setView] = useState('home'); // home, map, report, action, mh-rep
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch recent issues on mount
  useEffect(() => {
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
    fetchRecentIssues();
  }, []);

  // Home View Components
  const Home = () => (
    <div className="space-y-6">
      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => setView('report')}
          className="flex flex-col items-center justify-center bg-blue-50 border-2 border-blue-100 p-4 rounded-xl hover:bg-blue-100 transition shadow-sm h-32"
        >
          <div className="bg-blue-500 text-white p-3 rounded-full mb-2">
            <AlertTriangle size={24} />
          </div>
          <span className="font-semibold text-blue-800">Report Issue</span>
        </button>

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
          onClick={() => setView('mh-rep')}
          className="flex flex-col items-center justify-center bg-purple-50 border-2 border-purple-100 p-4 rounded-xl hover:bg-purple-100 transition shadow-sm h-32"
        >
          <div className="bg-purple-500 text-white p-3 rounded-full mb-2">
            <Search size={24} />
          </div>
          <span className="font-semibold text-purple-800">Find MLA</span>
        </button>

        <button
          onClick={fetchResponsibilityMap}
          className="flex flex-col items-center justify-center bg-green-50 border-2 border-green-100 p-4 rounded-xl hover:bg-green-100 transition shadow-sm h-32"
        >
          <div className="bg-green-500 text-white p-3 rounded-full mb-2">
            <MapPin size={24} />
          </div>
          <span className="font-semibold text-green-800">Responsibility</span>
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
                  <span className="text-xs text-gray-400">
                    {new Date(issue.created_at).toLocaleDateString()}
                  </span>
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

// Loader
const Loader = () => (
  <div className="flex justify-center my-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
  </div>
);

// Lazy Load Detectors Map
const DETECTORS = {
  pothole: PotholeDetector,
  garbage: GarbageDetector,
  waste: WasteDetector,
  vandalism: VandalismDetector,
  flood: FloodDetector,
  infrastructure: InfrastructureDetector,
  parking: IllegalParkingDetector,
  streetlight: StreetLightDetector,
  fire: FireDetector,
  animal: StrayAnimalDetector,
  blocked: BlockedRoadDetector,
  tree: TreeDetector,
  pest: PestDetector,
  'smart-scan': SmartScanner,
  noise: NoiseDetector,
  'water-leak': WaterLeakDetector,
  accessibility: AccessibilityDetector,
  crowd: CrowdDetector,
  severity: SeverityDetector,
};

// Valid view paths for navigation safety
const VALID_VIEWS = [
  'home', 'map', 'report', 'action', 'mh-rep', 'stats',
  'leaderboard', 'grievance', ...Object.keys(DETECTORS), 'verify'
];

// Loading spinner component with enhanced design
const LoadingSpinner = ({ className = "", size = "md", variant = "primary" }) => {
  const sizeClasses = {
    sm: "h-6 w-6 border-2",
    md: "h-10 w-10 border-3",
    lg: "h-16 w-16 border-4",
    xl: "h-24 w-24 border-6"
  };

  const variantClasses = {
    primary: "border-blue-200 border-t-blue-600",
    secondary: "border-orange-200 border-t-orange-500",
    light: "border-gray-200 border-t-gray-600"
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

  const { bg, border, text, icon } = config[variant];

  return (
    <div className={`${bg} border-l-4 ${border} p-4 rounded-lg my-4 animate-fadeIn`}>
      <div className="flex items-start">
        <div className="flex-shrink-0 pt-0.5">
          {icon}
        </div>
        <div className="ml-3 flex-1">
          <p className={`text-sm font-medium ${text}`}>{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-500 transition-colors duration-200 flex items-center gap-1 group"
            >
              <span>Try again</span>
              <svg
                className="w-4 h-4 transform group-hover:translate-x-1 transition-transform duration-200"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Success alert component
const SuccessAlert = ({ message }) => (
  <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg my-4 animate-fadeIn">
    <div className="flex items-center">
      <div className="flex-shrink-0">
        <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      </div>
      <div className="ml-3">
        <p className="text-sm font-medium text-green-700">{message}</p>
      </div>
    </div>
  </div>
);

// Navigation breadcrumb component
const NavigationBreadcrumb = () => {
  const location = useLocation();
  const paths = location.pathname.split('/').filter(Boolean);

  if (paths.length === 0) return null;

  return (
    <nav className="mb-6" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2 text-sm">
        <li>
          <a href="/" className="text-gray-500 hover:text-blue-600 transition-colors duration-200">
            Home
          </a>
        </li>
        {paths.map((path, index) => (
          <li key={path} className="flex items-center">
            <svg className="h-4 w-4 text-gray-400 mx-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            <span className={`capitalize ${index === paths.length - 1 ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
              {path.replace('-', ' ')}
            </span>
          </li>
        ))}
      </ol>
    </nav>
  );
};

// Enhanced detector wrapper with animated header
const DetectorWrapper = ({ children, onBack, title = null }) => {
  const location = useLocation();
  const detectorName = location.pathname.split('/').pop()?.replace('-', ' ') || 'Detector';

  return (
    <div className="min-h-[70vh] flex flex-col">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-100">
        <button
          onClick={onBack}
          className="group flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-all duration-300 hover:-translate-x-1"
        >
          <svg
            className="w-5 h-5 transform group-hover:-translate-x-1 transition-transform duration-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span className="font-medium">Back to Home</span>
        </button>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-blue-600 bg-clip-text text-transparent animate-gradient">
          {title || detectorName.charAt(0).toUpperCase() + detectorName.slice(1)} Scanner
        </h2>
        <div className="w-24"></div> {/* Spacer for alignment */}
      </div>

      <div className="flex-1 bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 border border-gray-200 shadow-inner">
        {children}
      </div>
    </div>
  );
};

// Enhanced header component with animated gradient
const AppHeader = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

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
            Empowering Citizens, Solving Problems — A Smart Civic Engagement Platform
          </p>
        </div>
      </div>
    </header>
  );
};

// Enhanced footer component
const AppFooter = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-16 pt-8 pb-12 border-t border-gray-200 relative">
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <div className="h-12 w-32 bg-gradient-to-r from-orange-500/20 to-blue-500/20 blur-xl rounded-full"></div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="inline-flex items-center justify-center space-x-4 mb-4">
            <div className="h-8 w-8 bg-gradient-to-r from-orange-500 to-blue-500 rounded-full"></div>
            <div className="h-8 w-8 bg-gradient-to-r from-blue-500 to-orange-500 rounded-full animate-pulse"></div>
            <div className="h-8 w-8 bg-gradient-to-r from-orange-500 to-blue-500 rounded-full"></div>
          </div>

          <p className="text-gray-500 text-sm mb-3 tracking-wide">
            &copy; {currentYear} VishwaGuru Civic Platform. All rights reserved.
          </p>
          <p className="text-gray-400 text-xs max-w-lg mx-auto leading-relaxed">
            Committed to transparent governance and community-driven solutions.
            Making cities smarter, one issue at a time.
          </p>

          <div className="mt-6 flex items-center justify-center space-x-6 text-xs text-gray-400">
            <a href="/privacy" className="hover:text-blue-600 transition-colors duration-200">Privacy Policy</a>
            <span className="h-1 w-1 bg-gray-400 rounded-full"></span>
            <a href="/terms" className="hover:text-blue-600 transition-colors duration-200">Terms of Service</a>
            <span className="h-1 w-1 bg-gray-400 rounded-full"></span>
            <a href="/contact" className="hover:text-blue-600 transition-colors duration-200">Contact Us</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

// Floating action button for quick actions
const FloatingActions = ({ setView }) => {
  const [isOpen, setIsOpen] = useState(false);

  const quickActions = [
    { label: 'Report Issue', icon: '📝', view: 'report', bgColor: 'from-green-500 to-emerald-600' },
    { label: 'Quick Scan', icon: '📷', view: 'smart-scan', bgColor: 'from-blue-500 to-cyan-600' },
    { label: 'View Map', icon: '🗺️', view: 'map', bgColor: 'from-purple-500 to-indigo-600' },
    { label: 'Emergency', icon: '🚨', view: 'fire', bgColor: 'from-red-500 to-orange-600' },
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

// Enhanced ChatWidget wrapper
const EnhancedChatWidget = () => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="fixed bottom-8 right-8 z-50">
      <div
        className="relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Chat label that appears on hover */}
        <div className={`absolute right-16 -top-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-3 py-1 rounded-lg shadow-lg transition-all duration-300 ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4 pointer-events-none'
          }`}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">AI Assistant</span>
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <div className="absolute right-0 top-1/2 transform translate-x-1/2 -translate-y-1/2">
            <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rotate-45"></div>
          </div>
        </div>

        <div className={`transform transition-all duration-300 ${isHovered ? 'scale-110 rotate-3' : ''
          }`}>
          <ChatWidget />
        </div>

        {/* Online indicator */}
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
      </div>
    </div>
  );
};

// Floating buttons manager component
const FloatingButtonsManager = ({ setView }) => {
  return (
    <>
      <EnhancedChatWidget />
      <FloatingActions setView={setView} />
    </>
  );
};

// App content with state management
function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
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
