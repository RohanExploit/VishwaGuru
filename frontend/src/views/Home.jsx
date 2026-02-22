import React from 'react';
import { useTranslation } from 'react-i18next';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, MapPin, Search, Activity, Camera, Trash2, ThumbsUp, Brush,
  Droplets, Zap, Truck, Flame, Dog, XCircle, Lightbulb, TreeDeciduous, Bug,
  Scan, ChevronRight, LayoutGrid, Shield, Leaf, Building, CheckCircle, Trophy, Monitor,
  Volume2, Users, Waves, Accessibility, Siren, Recycle, Eye, ChevronUp, Signpost, Car
} from 'lucide-react';

const CameraCheckModal = ({ onClose }) => {
  const videoRef = React.useRef(null);
  const [status, setStatus] = React.useState('requesting');

  React.useEffect(() => {
    let stream = null;
    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setStatus('active');
        }
      } catch (e) {
        console.error("Camera access denied", e);
        setStatus('error');
      }
    };
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-sm text-center">
        <h3 className="text-lg font-bold mb-4">Camera Diagnostics</h3>
        <div className="bg-gray-100 rounded-lg h-48 mb-4 flex items-center justify-center overflow-hidden relative">
          {status === 'requesting' && <span className="text-gray-500 animate-pulse">Requesting access...</span>}
          {status === 'error' && <span className="text-red-500 font-medium">Camera access failed. Check permissions.</span>}
          <video ref={videoRef} autoPlay playsInline className={`w-full h-full object-cover ${status === 'active' ? 'block' : 'hidden'}`} />
        </div>
        {status === 'active' && <p className="text-green-600 font-medium text-sm mb-4">Camera is working correctly!</p>}
        <button onClick={onClose} className="w-full bg-blue-600 text-white py-2 rounded-lg font-bold">Close</button>
      </div>
    </div>
  );
};

const Home = ({ setView, fetchResponsibilityMap, recentIssues, handleUpvote, loadMoreIssues, hasMore, loadingMore, stats }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showCameraCheck, setShowCameraCheck] = React.useState(false);
  const [showScrollTop, setShowScrollTop] = React.useState(false);
  const totalImpact = stats?.resolved_issues || 0;

  // Scroll to top function
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Show/hide scroll to top button based on scroll position
  React.useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const categories = [
    {
      title: t('home.categories.roadTraffic'),
      icon: <LayoutGrid size={20} className="text-blue-600" />,
      items: [
        { id: 'pothole', label: t('home.issues.pothole'), icon: <Camera size={24} />, color: 'text-red-600', bg: 'bg-red-50' },
        { id: 'blocked', label: t('home.issues.blockedRoad'), icon: <XCircle size={24} />, color: 'text-gray-600', bg: 'bg-gray-50' },
        { id: 'parking', label: t('home.issues.illegalParking'), icon: <Truck size={24} />, color: 'text-rose-600', bg: 'bg-rose-50' },
        { id: 'streetlight', label: t('home.issues.darkStreet'), icon: <Lightbulb size={24} />, color: 'text-slate-600', bg: 'bg-slate-50' },
        { id: 'traffic-sign', label: t('home.issues.trafficSign'), icon: <Signpost size={24} />, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        { id: 'abandoned-vehicle', label: t('home.issues.abandonedVehicle'), icon: <Car size={24} />, color: 'text-gray-600', bg: 'bg-gray-50' },
      ]
    },
    {
      title: t('home.categories.environmentSafety'),
      icon: <Leaf size={20} className="text-green-600" />,
      items: [
        { id: 'garbage', label: t('home.issues.garbage'), icon: <Trash2 size={24} />, color: 'text-orange-600', bg: 'bg-orange-50' },
        { id: 'flood', label: t('home.issues.flood'), icon: <Droplets size={24} />, color: 'text-cyan-600', bg: 'bg-cyan-50' },
        { id: 'fire', label: t('home.issues.fireSmoke'), icon: <Flame size={24} />, color: 'text-red-600', bg: 'bg-red-50' },
        { id: 'tree', label: t('home.issues.treeHazard'), icon: <TreeDeciduous size={24} />, color: 'text-green-600', bg: 'bg-green-50' },
        { id: 'animal', label: t('home.issues.strayAnimal'), icon: <Dog size={24} />, color: 'text-amber-600', bg: 'bg-amber-50' },
        { id: 'pest', label: t('home.issues.pestControl'), icon: <Bug size={24} />, color: 'text-amber-800', bg: 'bg-amber-50' },
        { id: 'noise', label: t('home.issues.noise'), icon: <Volume2 size={24} />, color: 'text-purple-600', bg: 'bg-purple-50' },
        { id: 'crowd', label: t('home.issues.crowd'), icon: <Users size={24} />, color: 'text-red-500', bg: 'bg-red-50' },
        { id: 'water-leak', label: t('home.issues.waterLeak'), icon: <Waves size={24} />, color: 'text-blue-500', bg: 'bg-blue-50' },
        { id: 'waste', label: t('home.issues.waste'), icon: <Recycle size={24} />, color: 'text-emerald-600', bg: 'bg-emerald-50' },
      ]
    },
    {
      title: t('home.categories.management'),
      icon: <Monitor size={20} className="text-gray-600" />,
      items: [
        { id: 'safety-check', label: t('home.issues.civicEye'), icon: <Eye size={24} />, color: 'text-blue-600', bg: 'bg-blue-50' },
        { id: 'my-reports', label: t('home.issues.myReports'), icon: <CheckCircle size={24} />, color: 'text-teal-600', bg: 'bg-teal-50' },
        { id: 'grievance', label: t('home.issues.grievanceManagement'), icon: <AlertTriangle size={24} />, color: 'text-orange-600', bg: 'bg-orange-50' },
        { id: 'stats', label: t('home.issues.viewStats'), icon: <Activity size={24} />, color: 'text-indigo-600', bg: 'bg-indigo-50' },
        { id: 'leaderboard', label: t('home.issues.leaderboard'), icon: <Trophy size={24} />, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        { id: 'map', label: t('home.issues.responsibilityMap'), icon: <MapPin size={24} />, color: 'text-green-600', bg: 'bg-green-50' },
      ]
    }
  ];

  return (
    <>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 pb-12 relative z-10">




        <div className="flex justify-end">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-100 shadow-sm">
            <Shield size={14} />
            {t('home.privacyActive')}
          </span>
        </div>

        {/* Header Stats & CTA */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Impact Widget */}
          <button
            onClick={() => setView('stats')}
            className="w-full text-left bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-6 text-white shadow-lg flex justify-between items-center transform transition hover:scale-[1.02] hover:opacity-95"
          >
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity size={20} className="text-indigo-200" />
                {t('home.communityImpact')}
              </h2>
              <p className="text-indigo-100 text-sm mt-1 opacity-90">{t('home.makingChange')}</p>
            </div>
            <div className="text-right">
              <span className="text-4xl font-extrabold block">{totalImpact}</span>
              <span className="text-xs text-indigo-200 uppercase tracking-wider font-semibold">{t('home.issuesSolved')}</span>
            </div>
            <ChevronRight size={24} />
          </button>

          {/* Quick Actions Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <button
              onClick={() => setView('report')}
              className="flex flex-col items-center justify-center bg-blue-50 border-2 border-blue-100 p-4 rounded-xl hover:bg-blue-100 transition shadow-sm h-32"
            >
              <div className="bg-blue-500 text-white p-3 rounded-full mb-2">
                <AlertTriangle size={24} />
              </div>
              <span className="font-semibold text-blue-800 text-sm">{t('home.issues.reportIssue')}</span>
            </button>

            <button
              onClick={() => setView('pothole')}
              className="flex flex-col items-center justify-center bg-red-50 border-2 border-red-100 p-4 rounded-xl hover:bg-red-100 transition shadow-sm h-32"
            >
              <div className="bg-red-500 text-white p-3 rounded-full mb-2">
                <Camera size={24} />
              </div>
              <span className="font-semibold text-red-800 text-sm">{t('home.issues.pothole')}</span>
            </button>

            <button
              onClick={() => setView('garbage')}
              className="flex flex-col items-center justify-center bg-orange-50 border-2 border-orange-100 p-4 rounded-xl hover:bg-orange-100 transition shadow-sm h-32"
            >
              <div className="bg-orange-500 text-white p-3 rounded-full mb-2">
                <Trash2 size={24} />
              </div>
              <span className="font-semibold text-orange-800 text-sm">{t('home.issues.garbage')}</span>
            </button>

            <button
              onClick={() => setView('mh-rep')}
              className="flex flex-col items-center justify-center bg-purple-50 border-2 border-purple-100 p-4 rounded-xl hover:bg-purple-100 transition shadow-sm h-32"
            >
              <div className="bg-purple-500 text-white p-3 rounded-full mb-2">
                <Search size={24} />
              </div>
              <span className="font-semibold text-purple-800 text-sm">{t('home.issues.findMLA')}</span>
            </button>

            <button
              onClick={() => setView('vandalism')}
              className="flex flex-col items-center justify-center bg-indigo-50 border-2 border-indigo-100 p-4 rounded-xl hover:bg-indigo-100 transition shadow-sm h-32"
            >
              <div className="bg-indigo-500 text-white p-3 rounded-full mb-2">
                <Brush size={24} />
              </div>
              <span className="font-semibold text-indigo-800 text-sm">{t('home.issues.graffiti')}</span>
            </button>

            <button
              onClick={() => setView('flood')}
              className="flex flex-col items-center justify-center bg-cyan-50 border-2 border-cyan-100 p-4 rounded-xl hover:bg-cyan-100 transition shadow-sm h-32"
            >
              <div className="bg-cyan-500 text-white p-3 rounded-full mb-2">
                <Droplets size={24} />
              </div>
              <span className="font-semibold text-cyan-800 text-sm">{t('home.issues.flood')}</span>
            </button>

            <button
              onClick={() => setView('infrastructure')}
              className="flex flex-col items-center justify-center bg-yellow-50 border-2 border-yellow-100 p-4 rounded-xl hover:bg-yellow-100 transition shadow-sm h-32"
            >
              <div className="bg-yellow-500 text-white p-3 rounded-full mb-2">
                <Zap size={24} />
              </div>
              <span className="font-semibold text-yellow-800 text-sm">{t('home.issues.brokenInfra')}</span>
            </button>

            {/* New Western Style Features */}
            <button
              onClick={() => setView('parking')}
              className="flex flex-col items-center justify-center bg-rose-50 border-2 border-rose-100 p-4 rounded-xl hover:bg-rose-100 transition shadow-sm h-32"
            >
              <div className="bg-rose-500 text-white p-3 rounded-full mb-2">
                <Truck size={24} />
              </div>
              <span className="font-semibold text-rose-800 text-sm">{t('home.issues.illegalParking')}</span>
            </button>

            <button
              onClick={() => setView('streetlight')}
              className="flex flex-col items-center justify-center bg-slate-50 border-2 border-slate-100 p-4 rounded-xl hover:bg-slate-100 transition shadow-sm h-32"
            >
              <div className="bg-slate-700 text-white p-3 rounded-full mb-2">
                <Lightbulb size={24} />
              </div>
              <span className="font-semibold text-slate-800 text-sm">{t('home.issues.darkStreet')}</span>
            </button>

            <button
              onClick={() => setView('fire')}
              className="flex flex-col items-center justify-center bg-red-100 border-2 border-red-200 p-4 rounded-xl hover:bg-red-200 transition shadow-sm h-32"
            >
              <div className="bg-red-600 text-white p-3 rounded-full mb-2">
                <Flame size={24} />
              </div>
              <span className="font-semibold text-red-900 text-sm">{t('home.issues.fireSmoke')}</span>
            </button>

            <button
              onClick={() => setView('animal')}
              className="flex flex-col items-center justify-center bg-amber-50 border-2 border-amber-100 p-4 rounded-xl hover:bg-amber-100 transition shadow-sm h-32"
            >
              <div className="bg-amber-600 text-white p-3 rounded-full mb-2">
                <Dog size={24} />
              </div>
              <span className="font-semibold text-amber-900 text-sm">{t('home.issues.strayAnimal')}</span>
            </button>

            <button
              onClick={() => setView('blocked')}
              className="flex flex-col items-center justify-center bg-gray-50 border-2 border-gray-100 p-4 rounded-xl hover:bg-gray-100 transition shadow-sm h-32"
            >
              <div className="bg-gray-600 text-white p-3 rounded-full mb-2">
                <XCircle size={24} />
              </div>
              <span className="font-semibold text-gray-800 text-sm">{t('home.issues.blockedRoad')}</span>
            </button>

            <button
              onClick={() => setView('tree')}
              className="flex flex-col items-center justify-center bg-green-50 border-2 border-green-100 p-4 rounded-xl hover:bg-green-100 transition shadow-sm h-32"
            >
              <div className="bg-green-600 text-white p-3 rounded-full mb-2">
                <TreeDeciduous size={24} />
              </div>
              <span className="font-semibold text-green-800 text-sm">{t('home.issues.treeHazard')}</span>
            </button>

            <button
              onClick={() => setView('pest')}
              className="flex flex-col items-center justify-center bg-amber-50 border-2 border-amber-100 p-4 rounded-xl hover:bg-amber-100 transition shadow-sm h-32"
            >
              <div className="bg-amber-800 text-white p-3 rounded-full mb-2">
                <Bug size={24} />
              </div>
              <span className="font-semibold text-amber-900 text-sm">{t('home.issues.pestControl')}</span>
            </button>

            <button
              onClick={() => setView('grievance-analysis')}
              className="flex flex-col items-center justify-center bg-teal-50 border-2 border-teal-100 p-4 rounded-xl hover:bg-teal-100 transition shadow-sm h-32"
            >
              <div className="bg-teal-600 text-white p-3 rounded-full mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M13 8H7"></path><path d="M17 12H7"></path></svg>
              </div>
              <span className="font-semibold text-teal-800 text-sm">{t('home.issues.analyzeGrievance')}</span>
            </button>
          </div>

          {/* Smart Scanner CTA */}
          <button
            onClick={() => setView('smart-scan')}
            className="w-full bg-gradient-to-br from-blue-500 to-cyan-600 p-6 rounded-2xl shadow-lg flex items-center justify-between text-white hover:opacity-95 transition transform hover:scale-[1.02] active:scale-95 group"
          >
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm group-hover:bg-white/30 transition">
                <Scan size={28} />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-xl">{t('home.smartScanner')}</h3>
                <p className="text-blue-100 text-sm mt-1">{t('home.aiPoweredDetection')}</p>
              </div>
            </div>
            <div className="bg-white/10 p-2 rounded-full">
              <ChevronRight size={24} />
            </div>
          </button>
        </div>

        {/* Categorized Features */}
        <div className="space-y-8">
          {categories.map((cat, idx) => (
            <div key={idx}>
              <div className="flex items-center gap-2 mb-4 px-1">
                {cat.icon}
                <h3 className="text-lg font-bold text-gray-800">{cat.title}</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-4">
                {cat.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setView(item.id)}
                    className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-col items-center justify-center gap-3 transition-all duration-200 hover:shadow-md hover:border-blue-100 hover:-translate-y-1 h-32 group"
                  >
                    <div className={`${item.bg} ${item.color} p-3 rounded-full transition-transform group-hover:scale-110 duration-200`}>
                      {item.icon}
                    </div>
                    <span className="font-medium text-gray-700 text-sm text-center">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Additional Tools */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={fetchResponsibilityMap}
            className="flex flex-row items-center justify-center bg-emerald-50 border border-emerald-100 p-4 rounded-xl hover:bg-emerald-100 transition shadow-sm h-16 gap-3 text-emerald-800 font-semibold"
          >
            <MapPin size={20} className="text-emerald-600" />
            {t('home.tools.whoIsResponsible')}
          </button>
          <button
            onClick={() => setView('leaderboard')}
            className="flex flex-row items-center justify-center bg-yellow-50 border border-yellow-100 p-4 rounded-xl hover:bg-yellow-100 transition shadow-sm h-16 gap-3 text-yellow-800 font-semibold"
          >
            <Trophy size={20} className="text-yellow-600" />
            {t('home.tools.topReporters')}
          </button>
          <button
            onClick={() => setShowCameraCheck(true)}
            className="flex flex-row items-center justify-center bg-slate-50 border border-slate-100 p-4 rounded-xl hover:bg-slate-100 transition shadow-sm h-16 gap-3 text-slate-800 font-semibold"
          >
            <Monitor size={20} className="text-slate-600" />
            {t('home.tools.cameraCheck')}
          </button>
        </div>

        {showCameraCheck && <CameraCheckModal onClose={() => setShowCameraCheck(false)} />}

        {/* Recent Activity Feed */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-orange-500" />
              <h2 className="font-bold text-gray-800">{t('home.activity.communityActivity')}</h2>
            </div>
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{t('home.activity.liveFeed')}</span>
          </div>
          <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto custom-scrollbar">
            {recentIssues.length > 0 ? (
              recentIssues.map((issue) => (
                <div key={issue.id} className="p-4 hover:bg-gray-50 transition group">
                  <div className="flex justify-between items-start mb-1">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide mb-1 ${issue.category === 'road' ? 'bg-blue-100 text-blue-700' :
                      issue.category === 'garbage' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                      {issue.category}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(issue.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2 mb-2 group-hover:text-gray-900">{issue.description}</p>

                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-400 flex items-center gap-1">
                      <MapPin size={12} />
                      {issue.location || 'Unknown Location'}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); navigate(`/verify/${issue.id}`); }}
                        className="flex items-center gap-1.5 text-gray-500 hover:text-green-600 text-xs bg-gray-50 px-2 py-1 rounded-md transition hover:bg-green-50"
                        title="Verify Resolution"
                      >
                        <CheckCircle size={12} />
                        <span className="font-medium">{t('home.activity.verify')}</span>
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpvote(issue.id); }}
                        className="flex items-center gap-1.5 text-gray-500 hover:text-blue-600 text-xs bg-gray-50 px-2 py-1 rounded-md transition hover:bg-blue-50"
                      >
                        <ThumbsUp size={12} />
                        <span className="font-medium">{issue.upvotes || 0}</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-gray-400 text-sm flex flex-col items-center">
                <Activity size={32} className="mb-2 opacity-20" />
                {t('home.activity.noActivity')}
              </div>
            )}
          </div>
          {recentIssues.length > 0 && hasMore && (
            <div className="p-3 border-t border-gray-100 bg-gray-50/50 text-center">
              <button
                onClick={loadMoreIssues}
                disabled={loadingMore}
                className="text-sm font-medium text-blue-600 hover:text-blue-800 disabled:opacity-50 transition-colors py-1 px-3 rounded-full hover:bg-blue-50"
              >
                {loadingMore ? (
                  <span className="flex items-center gap-2 justify-center">
                    <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    {t('common.loading')}
                  </span>
                ) : (
                  t('home.activity.loadMore')
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Scroll to Top Button - Appears on scroll */}
      <AnimatePresence>
        {showScrollTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
            onClick={scrollToTop}
            className="fixed right-8 bottom-8 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg hover:shadow-2xl z-[9999] cursor-pointer"
            aria-label="Scroll to top"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <ChevronUp size={24} strokeWidth={2.5} />
          </motion.button>
        )}
      </AnimatePresence>
    </>
  );
};

export default Home;
