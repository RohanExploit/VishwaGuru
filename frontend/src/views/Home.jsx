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
        { id: 'report', label: t('home.issues.trafficSign'), icon: <Signpost size={24} />, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        { id: 'report', label: t('home.issues.abandonedVehicle'), icon: <Car size={24} />, color: 'text-gray-600', bg: 'bg-gray-50' },
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
        { id: 'report', label: t('home.issues.crowd'), icon: <Users size={24} />, color: 'text-red-500', bg: 'bg-red-50' },
        { id: 'report', label: t('home.issues.waterLeak'), icon: <Waves size={24} />, color: 'text-blue-500', bg: 'bg-blue-50' },
        { id: 'report', label: t('home.issues.waste'), icon: <Recycle size={24} />, color: 'text-emerald-600', bg: 'bg-emerald-50' },
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12 pb-24 relative z-10">

        {/* Privacy Shield - High End Style */}
        <div className="flex justify-end pt-4">
          <motion.span
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800/50 shadow-sm"
          >
            <Shield size={14} className="animate-pulse" />
            {t('home.privacyActive') || 'Privacy Shield Active'}
          </motion.span>
        </div>

        {/* Hero Section / Impact Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Impact Card */}
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={() => setView('stats')}
            className="lg:col-span-8 group relative overflow-hidden bg-white/70 dark:bg-gray-900/70 backdrop-blur-3xl rounded-[2.5rem] p-10 border border-white/20 dark:border-gray-800/50 shadow-2xl text-left transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 to-indigo-600/5 dark:from-blue-400/10 dark:to-indigo-400/10 -z-10"></div>
            <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-600/10 rounded-full blur-[100px] group-hover:bg-blue-600/20 transition-colors"></div>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-600 rounded-2xl shadow-xl shadow-blue-600/20 text-white">
                    <Activity size={28} />
                  </div>
                  <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">
                    {t('home.communityImpact')}
                  </h2>
                </div>
                <p className="text-gray-500 dark:text-gray-400 text-lg font-medium max-w-md leading-relaxed">
                  {t('home.makingChange') || 'Our platform empowers citizens to drive real change in their local neighborhoods through AI-assisted oversight.'}
                </p>
                <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-black text-sm uppercase tracking-widest group">
                  View Global Statistics
                  <ChevronRight size={18} className="translate-x-0 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>

              <div className="relative text-center md:text-right px-6 py-4 bg-white/50 dark:bg-gray-800/50 rounded-[2rem] border border-white/50 dark:border-gray-700/50 shadow-inner">
                <span className="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-br from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 block leading-tight">
                  {totalImpact}
                </span>
                <span className="text-xs text-gray-400 font-black uppercase tracking-[0.2em]">
                  {t('home.issuesSolved') || 'Cases Resolved'}
                </span>
              </div>
            </div>
          </motion.button>

          {/* Smart Scanner Quick Access */}
          <motion.button
            whileHover={{ scale: 1.02, y: -5 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setView('smart-scan')}
            className="lg:col-span-4 group relative overflow-hidden bg-gray-900 rounded-[2.5rem] p-10 shadow-2xl text-white flex flex-col justify-between"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-indigo-700 opacity-90 -z-10 group-hover:scale-110 transition-transform duration-700"></div>
            <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2"></div>

            <div className="p-4 bg-white/20 backdrop-blur-md rounded-2xl w-fit shadow-xl">
              <Scan size={32} />
            </div>

            <div className="pt-8 space-y-2">
              <h3 className="text-3xl font-black tracking-tight">{t('home.smartScanner')}</h3>
              <p className="text-blue-100/80 font-medium">Auto-detect issues using computer vision.</p>
              <div className="h-1 w-12 bg-white rounded-full mt-4"></div>
            </div>
          </motion.button>
        </div>

        {/* Priority Actions */}
        <div className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-lg font-black text-gray-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
              <Zap size={18} className="text-amber-500" />
              Priority Actions
            </h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {[
              { id: 'report', label: t('home.issues.reportIssue'), icon: <AlertTriangle size={24} />, color: 'bg-blue-600', text: 'text-blue-600', bg: 'bg-blue-50/50' },
              { id: 'pothole', label: t('home.issues.pothole'), icon: <Camera size={24} />, color: 'bg-rose-600', text: 'text-rose-600', bg: 'bg-rose-50/50' },
              { id: 'garbage', label: t('home.issues.garbage'), icon: <Trash2 size={24} />, color: 'bg-orange-600', text: 'text-orange-600', bg: 'bg-orange-50/50' },
              { id: 'mh-rep', label: t('home.issues.findMLA'), icon: <Search size={24} />, color: 'bg-purple-600', text: 'text-purple-600', bg: 'bg-purple-50/50' },
              { id: 'flood', label: t('home.issues.flood'), icon: <Droplets size={24} />, color: 'bg-cyan-600', text: 'text-cyan-600', bg: 'bg-cyan-50/50' },
              { id: 'streetlight', label: t('home.issues.darkStreet'), icon: <Lightbulb size={24} />, color: 'bg-gray-800', text: 'text-gray-800', bg: 'bg-gray-100/50' },
            ].map((action, idx) => (
              <motion.button
                key={action.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ y: -5, backgroundColor: 'rgba(255,255,255,1)' }}
                onClick={() => setView(action.id)}
                className="group flex flex-col items-center justify-center bg-white/50 dark:bg-gray-800/50 backdrop-blur-lg border border-white/50 dark:border-gray-700/50 p-6 rounded-[2rem] shadow-lg transition-all h-40 gap-4"
              >
                <div className={`${action.color} text-white p-4 rounded-2xl shadow-xl shadow-${action.color}/20 group-hover:scale-110 transition-transform`}>
                  {action.icon}
                </div>
                <span className="font-black text-gray-800 dark:text-gray-200 text-xs uppercase tracking-widest text-center">
                  {action.label}
                </span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Feature Categories */}
        <div className="space-y-12">
          {categories.map((cat, catIdx) => (
            <div key={catIdx} className="space-y-6">
              <div className="flex items-center gap-3 px-2">
                <div className="p-2 bg-white/50 dark:bg-gray-800/50 rounded-xl border border-white/50 dark:border-gray-700/50 shadow-sm text-blue-600">
                  {cat.icon}
                </div>
                <h3 className="text-lg font-black text-gray-900 dark:text-white uppercase tracking-widest">{cat.title}</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {cat.items.map((item, itemIdx) => (
                  <motion.button
                    key={item.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: itemIdx * 0.05 }}
                    onClick={() => setView(item.id)}
                    className="group bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-[2rem] border border-white/50 dark:border-gray-800/50 p-8 flex flex-col items-start gap-6 hover:shadow-2xl hover:bg-white dark:hover:bg-gray-800 transition-all duration-300 h-56"
                  >
                    <div className={`${item.bg} ${item.color} p-4 rounded-2xl shadow-sm transition-transform group-hover:scale-110 duration-300`}>
                      {React.cloneElement(item.icon, { size: 28 })}
                    </div>
                    <div className="space-y-1">
                      <span className="font-black text-gray-900 dark:text-gray-100 text-lg tracking-tight block">
                        {item.label}
                      </span>
                      <p className="text-xs text-gray-400 font-medium tracking-wide">AI-Powered Verification</p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Community Activity & Tools */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">

          {/* Recent Activity Feed - Professional Redesign */}
          <div className="xl:col-span-8 bg-white/70 dark:bg-gray-900/70 backdrop-blur-3xl rounded-[2.5rem] border border-white/20 dark:border-gray-800/50 shadow-2xl overflow-hidden flex flex-col">
            <div className="p-8 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/30">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-orange-50 dark:bg-orange-900/30 text-orange-600 rounded-xl">
                  <Activity size={20} />
                </div>
                <div>
                  <h2 className="font-black text-gray-900 dark:text-white uppercase tracking-widest text-sm">
                    {t('home.activity.communityActivity')}
                  </h2>
                  <p className="text-[10px] text-gray-400 font-bold tracking-widest uppercase">Live Surveillance Feed</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 bg-white/50 dark:bg-gray-800 rounded-full border border-gray-100 dark:border-gray-700 shadow-sm">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-[10px] font-black text-gray-500 dark:text-gray-400 uppercase tracking-widest">
                  {t('home.activity.liveFeed')}
                </span>
              </div>
            </div>

            <div className="divide-y divide-gray-50 dark:divide-gray-800 max-h-[500px] overflow-y-auto custom-scrollbar bg-white/30 dark:bg-transparent">
              {recentIssues.length > 0 ? (
                recentIssues.map((issue, idx) => (
                  <motion.div
                    key={issue.id}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: idx * 0.05 }}
                    className="p-8 hover:bg-white dark:hover:bg-gray-800/50 transition-all group relative cursor-pointer"
                  >
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-blue-600 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity"></div>

                    <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                      <div className="space-y-4 flex-1">
                        <div className="flex flex-wrap items-center gap-3">
                          <span className={`px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.1em] border ${issue.category === 'road' ? 'bg-blue-50 border-blue-100 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-400' :
                            issue.category === 'garbage' ? 'bg-orange-50 border-orange-100 text-orange-700 dark:bg-orange-900/30 dark:border-orange-800 dark:text-orange-400' :
                              'bg-gray-50 border-gray-100 text-gray-600 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400'
                            }`}>
                            {issue.category}
                          </span>
                          <span className="text-[10px] text-gray-400 font-black uppercase tracking-widest flex items-center gap-1.5">
                            <MapPin size={12} className="text-gray-300" />
                            {issue.location || 'Unknown Sector'}
                          </span>
                        </div>

                        <p className="text-gray-700 dark:text-gray-300 font-bold leading-relaxed group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
                          {issue.description}
                        </p>
                      </div>

                      <div className="flex flex-row md:flex-col items-center md:items-end gap-3 w-full md:w-auto pt-2 md:pt-0">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); navigate(`/verify/${issue.id}`); }}
                            className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-black text-[10px] uppercase tracking-widest bg-emerald-50 dark:bg-emerald-900/30 px-3 py-2 rounded-xl border border-emerald-100 dark:border-emerald-800/50 hover:bg-emerald-600 hover:text-white transition-all shadow-sm"
                          >
                            <CheckCircle size={14} />
                            {t('home.activity.verify')}
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleUpvote(issue.id); }}
                            className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-black text-[10px] uppercase tracking-widest bg-blue-50 dark:bg-blue-900/30 px-3 py-2 rounded-xl border border-blue-100 dark:border-blue-800/50 hover:bg-blue-600 hover:text-white transition-all shadow-sm"
                          >
                            <ThumbsUp size={14} />
                            {issue.upvotes || 0}
                          </button>
                        </div>
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest ml-auto md:ml-0">
                          {new Date(issue.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="py-24 text-center space-y-4">
                  <div className="w-20 h-20 bg-gray-50 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto text-gray-200 dark:text-gray-700">
                    <Activity size={40} />
                  </div>
                  <div>
                    <h4 className="font-black text-gray-900 dark:text-white uppercase tracking-widest text-sm">Silence in the Grid</h4>
                    <p className="text-gray-500 text-xs font-medium uppercase tracking-widest">No active threats detected in your area</p>
                  </div>
                </div>
              )}
            </div>

            {recentIssues.length > 0 && hasMore && (
              <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-transparent text-center">
                <button
                  onClick={loadMoreIssues}
                  disabled={loadingMore}
                  className="inline-flex items-center gap-3 px-8 py-3 rounded-2xl bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 font-black uppercase tracking-widest text-[10px] shadow-lg shadow-black/5 hover:scale-105 transition-all disabled:opacity-50 border border-gray-100 dark:border-gray-700"
                >
                  {loadingMore ? (
                    <>
                      <Loader2 className="animate-spin" size={14} />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <ChevronDown size={14} />
                      {t('home.activity.loadMore') || 'Explore Deep Feed'}
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Side Tools - Minimalist Glass Cards */}
          <div className="xl:col-span-4 space-y-6">
            <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.3em] px-2 mb-2">Auxiliary Systems</h3>

            <motion.button
              whileHover={{ scale: 1.02, x: 5 }}
              onClick={fetchResponsibilityMap}
              className="w-full flex items-center gap-6 bg-emerald-600 rounded-[2rem] p-8 text-white shadow-2xl shadow-emerald-500/20 group overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              <div className="p-4 bg-white/20 rounded-2xl">
                <MapPin size={28} />
              </div>
              <div className="text-left">
                <span className="block text-xl font-black leading-tight">{t('home.tools.whoIsResponsible')}</span>
                <span className="text-[10px] font-black uppercase tracking-widest opacity-80 mt-1 block">Jurisdiction Map</span>
              </div>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02, x: 5 }}
              onClick={() => setView('leaderboard')}
              className="w-full flex items-center gap-6 bg-amber-500 rounded-[2rem] p-8 text-white shadow-2xl shadow-amber-500/20 group overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              <div className="p-4 bg-white/20 rounded-2xl">
                <Trophy size={28} />
              </div>
              <div className="text-left">
                <span className="block text-xl font-black leading-tight">{t('home.tools.topReporters')}</span>
                <span className="text-[10px] font-black uppercase tracking-widest opacity-80 mt-1 block">Citizen Rankings</span>
              </div>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02, x: 5 }}
              onClick={() => setShowCameraCheck(true)}
              className="w-full flex items-center gap-6 bg-gray-900 rounded-[2rem] p-8 text-white shadow-2xl group overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              <div className="p-4 bg-white/20 rounded-2xl">
                <Monitor size={28} />
              </div>
              <div className="text-left">
                <span className="block text-xl font-black leading-tight">{t('home.tools.cameraCheck')}</span>
                <span className="text-[10px] font-black uppercase tracking-widest opacity-80 mt-1 block">Diagnostics Hub</span>
              </div>
            </motion.button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;
