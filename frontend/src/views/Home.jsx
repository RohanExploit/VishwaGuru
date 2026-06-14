import React from 'react';
import { useTranslation } from 'react-i18next';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle, MapPin, Search, Activity, Camera, Trash2, ThumbsUp, Brush,
  Droplets, Zap, Truck, Flame, Dog, XCircle, Lightbulb, TreeDeciduous, Bug,
  Scan, ChevronRight, LayoutGrid, Shield, Leaf, Building, CheckCircle, Trophy, Monitor,
  Volume2, Users, Waves, Accessibility, Siren, Recycle, Eye, ChevronUp
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

const Home = ({ setView, fetchResponsibilityMap, recentIssues, handleUpvote }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showCameraCheck, setShowCameraCheck] = React.useState(false);
  const [showScrollTop, setShowScrollTop] = React.useState(false);
  const totalImpact = 1240 + (recentIssues ? recentIssues.length : 0);

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
        { id: 'noise', label: "Noise", icon: <Volume2 size={24} />, color: 'text-purple-600', bg: 'bg-purple-50' },
        { id: 'crowd', label: "Crowd", icon: <Users size={24} />, color: 'text-red-500', bg: 'bg-red-50' },
        { id: 'water-leak', label: "Water Leak", icon: <Waves size={24} />, color: 'text-blue-500', bg: 'bg-blue-50' },
        { id: 'waste', label: "Waste Sorter", icon: <Recycle size={24} />, color: 'text-emerald-600', bg: 'bg-emerald-50' },
      ]
    },
    {
      title: t('home.categories.management'),
      icon: <Monitor size={20} className="text-gray-600" />,
      items: [
        { id: 'civic-eye', label: "Civic Eye", icon: <Eye size={24} />, color: 'text-blue-600', bg: 'bg-blue-50' },
        { id: 'grievance', label: t('home.issues.grievanceManagement'), icon: <AlertTriangle size={24} />, color: 'text-orange-600', bg: 'bg-orange-50' },
        { id: 'stats', label: t('home.issues.viewStats'), icon: <Activity size={24} />, color: 'text-indigo-600', bg: 'bg-indigo-50' },
        { id: 'leaderboard', label: t('home.issues.leaderboard'), icon: <Trophy size={24} />, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        { id: 'map', label: t('home.issues.responsibilityMap'), icon: <MapPin size={24} />, color: 'text-green-600', bg: 'bg-green-50' },
      ]
    }
  ];

  return (
    <>
      <div className="space-y-8 pb-12">




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
          </button>

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
            Who is Responsible?
          </button>
          <button
            onClick={() => setView('leaderboard')}
            className="flex flex-row items-center justify-center bg-yellow-50 border border-yellow-100 p-4 rounded-xl hover:bg-yellow-100 transition shadow-sm h-16 gap-3 text-yellow-800 font-semibold"
          >
            <Trophy size={20} className="text-yellow-600" />
            Top Reporters
          </button>
          <button
            onClick={() => setShowCameraCheck(true)}
            className="flex flex-row items-center justify-center bg-slate-50 border border-slate-100 p-4 rounded-xl hover:bg-slate-100 transition shadow-sm h-16 gap-3 text-slate-800 font-semibold"
          >
            <Monitor size={20} className="text-slate-600" />
            Camera Check
          </button>
        </div>

        {showCameraCheck && <CameraCheckModal onClose={() => setShowCameraCheck(false)} />}

        {/* Recent Activity Feed */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-orange-500" />
              <h2 className="font-bold text-gray-800">Community Activity</h2>
            </div>
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">Live Feed</span>
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
                        <span className="font-medium">Verify</span>
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
                No recent activity to show.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scroll to Top Button - Appears on scroll */}
      {/* Scroll to Top Button - Portal to Body */}
      {createPortal(
        <AnimatePresence>
          {showScrollTop && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              onClick={scrollToTop}
              className="fixed right-8 bottom-[447px] bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg hover:shadow-2xl z-[9999] cursor-pointer"
              aria-label="Scroll to top"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <ChevronUp size={24} strokeWidth={2.5} />
            </motion.button>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
};

export default Home;
