import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Menu, X, Sun, Moon, ChevronDown,
    LayoutGrid, Camera, XCircle, Truck, Lightbulb,
    Leaf, Trash2, Droplets, Flame, Dog,
    Monitor, Activity, MapPin, Trophy, Search,
    User, LogOut, LogIn
} from 'lucide-react';
import { useDarkMode } from '../contexts/DarkModeContext';
import { useAuth } from '../contexts/AuthContext';
import LanguageSelector from './LanguageSelector';

const Navbar = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { t } = useTranslation();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isServicesOpen, setIsServicesOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const { isDarkMode, toggleDarkMode } = useDarkMode();
    const { user, logout } = useAuth();
    const [isProfileOpen, setIsProfileOpen] = useState(false);

    const handleLogout = () => {
        logout();
        setIsProfileOpen(false);
        navigate('/login');
    };

    // Close profile dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = () => setIsProfileOpen(false);
        if (isProfileOpen) {
            document.addEventListener('click', handleClickOutside);
            return () => document.removeEventListener('click', handleClickOutside);
        }
    }, [isProfileOpen]);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const navLinks = [
        { name: t('nav.home'), path: '/' },
        { name: t('nav.about'), path: '#about' },
        { name: t('nav.services'), path: '#services', isMega: true },
        { name: t('nav.contact'), path: '#contact' },
    ];

    const handleNavClick = (path, isMega = false) => {
        if (isMega) {
            setIsServicesOpen(!isServicesOpen);
            return;
        }

        setIsServicesOpen(false);
        if (path.startsWith('#')) {
            if (location.pathname !== '/') {
                navigate('/');
                setTimeout(() => {
                    const element = document.getElementById(path.substring(1));
                    if (element) element.scrollIntoView({ behavior: 'smooth' });
                }, 300);
            } else {
                const element = document.getElementById(path.substring(1));
                if (element) element.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            navigate(path);
        }
        setIsMenuOpen(false);
    };

    const serviceCategories = [
        {
            title: t('home.categories.roadTraffic'),
            icon: <LayoutGrid size={18} />,
            items: [
                { id: 'pothole', label: t('home.issues.pothole'), icon: <Camera size={18} />, path: '/pothole' },
                { id: 'blocked', label: t('home.issues.blockedRoad'), icon: <XCircle size={18} />, path: '/blocked' },
                { id: 'parking', label: t('home.issues.illegalParking'), icon: <Truck size={18} />, path: '/parking' },
                { id: 'streetlight', label: t('home.issues.darkStreet'), icon: <Lightbulb size={18} />, path: '/streetlight' },
            ]
        },
        {
            title: t('home.categories.environmentSafety'),
            icon: <Leaf size={18} />,
            items: [
                { id: 'garbage', label: t('home.issues.garbage'), icon: <Trash2 size={18} />, path: '/garbage' },
                { id: 'flood', label: t('home.issues.flood'), icon: <Droplets size={18} />, path: '/flood' },
                { id: 'fire', label: t('home.issues.fireSmoke'), icon: <Flame size={18} />, path: '/fire' },
                { id: 'animal', label: t('home.issues.strayAnimal'), icon: <Dog size={18} />, path: '/animal' },
            ]
        },
        {
            title: t('home.categories.management'),
            icon: <Monitor size={18} />,
            items: [
                { id: 'insight', label: "Civic Insight", icon: <Activity size={18} />, path: '/insight' },
                { id: 'stats', label: t('home.issues.viewStats'), icon: <Activity size={18} />, path: '/stats' },
                { id: 'map', label: t('home.issues.responsibilityMap'), icon: <MapPin size={18} />, path: '/map' },
                { id: 'leaderboard', label: t('home.issues.leaderboard'), icon: <Trophy size={18} />, path: '/leaderboard' },
                { id: 'mh-rep', label: t('home.issues.findMLA'), icon: <Search size={18} />, path: '/mh-rep' },
            ]
        }
    ];

    return (
        <nav className={`fixed top-0 left-0 w-full z-50 transition-all duration-500 ${scrolled
            ? 'bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl shadow-2xl border-b border-white/20 dark:border-gray-800/50 py-3'
            : 'bg-white/40 dark:bg-gray-950/40 backdrop-blur-md border-b border-white/10 dark:border-gray-900/30 py-4'
            }`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center">
                    {/* Logo */}
                    <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
                        <div className="w-10 h-10 relative flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                            <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-sm" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="50" cy="50" r="38" stroke="#2D60FF" strokeWidth="8" fill="white" className="dark:fill-gray-800" />
                                <path d="M77 77L92 92" stroke="#2D60FF" strokeWidth="10" strokeLinecap="round" />
                                <path d="M32 62V52" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
                                <path d="M44 62V42" stroke="#2D60FF" strokeWidth="6" strokeLinecap="round" />
                                <path d="M56 62V33" stroke="#4ADE80" strokeWidth="6" strokeLinecap="round" />
                                <path d="M68 62V48" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
                                <path d="M28 58L42 45L52 50L70 28" stroke="#16A34A" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M70 28H58M70 28V40" stroke="#16A34A" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h1 className="text-xl font-extrabold text-gray-900 dark:text-white tracking-tight">
                            FixMyIndia / <span className="text-blue-600 dark:text-blue-400 font-black">VishwaGuru</span>
                        </h1>
                    </div>

                    {/* Desktop Nav Links */}
                    <div className="hidden md:flex items-center space-x-6">
                        {navLinks.map((link) => (
                            <div key={link.name} className="relative group">
                                <button
                                    onClick={() => handleNavClick(link.path, link.isMega)}
                                    onMouseEnter={() => link.isMega && setIsServicesOpen(true)}
                                    className={`flex items-center gap-1.5 text-sm font-bold transition-all duration-300 ${isServicesOpen && link.isMega
                                        ? 'text-blue-600 dark:text-blue-400 scale-105'
                                        : 'text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
                                        }`}
                                >
                                    {link.name}
                                    {link.isMega && <ChevronDown size={14} className={`transition-transform duration-300 ${isServicesOpen ? 'rotate-180' : ''}`} />}
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Action Buttons */}
                    <div className="hidden md:flex items-center space-x-4">
                        <LanguageSelector />
                        <button
                            onClick={toggleDarkMode}
                            className="p-2.5 rounded-xl bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm border border-white/20 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-white/80 dark:hover:bg-gray-800 transition-all duration-200 shadow-sm"
                        >
                            {isDarkMode ? <Sun size={20} className="text-yellow-500" /> : <Moon size={20} />}
                        </button>

                        {/* User Profile / Login */}
                        {user ? (
                            <div className="relative">
                                <button
                                    onClick={(e) => { e.stopPropagation(); setIsProfileOpen(!isProfileOpen); }}
                                    className="flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800/50 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-all duration-200 shadow-sm"
                                >
                                    <User size={18} />
                                    <span className="text-sm font-bold max-w-[120px] truncate">{user.full_name || user.email}</span>
                                    <ChevronDown size={14} className={`transition-transform duration-300 ${isProfileOpen ? 'rotate-180' : ''}`} />
                                </button>
                                <AnimatePresence>
                                    {isProfileOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                            className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden z-50"
                                        >
                                            <div className="p-4 border-b border-gray-100 dark:border-gray-800">
                                                <p className="text-sm font-black text-gray-900 dark:text-white truncate">{user.full_name || 'User'}</p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
                                                <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">{user.role}</span>
                                            </div>
                                            <div className="p-2">
                                                <button
                                                    onClick={handleLogout}
                                                    className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                                                >
                                                    <LogOut size={16} />
                                                    Logout
                                                </button>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        ) : (
                            <button
                                onClick={() => navigate('/login')}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 transition-all duration-200 shadow-sm"
                            >
                                <LogIn size={16} />
                                Login
                            </button>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center gap-4">
                        <button
                            onClick={toggleDarkMode}
                            className="p-3 rounded-2xl bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl border border-white/20 dark:border-gray-800/50 text-gray-700 dark:text-gray-300 shadow-xl"
                        >
                            {isDarkMode ? <Sun size={20} className="text-yellow-500" /> : <Moon size={20} />}
                        </button>
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="p-3 rounded-2xl bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl border border-white/20 dark:border-gray-800/50 text-gray-700 dark:text-gray-300 shadow-xl"
                        >
                            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mega Menu Dropdown */}
            <AnimatePresence>
                {isServicesOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        onMouseLeave={() => setIsServicesOpen(false)}
                        className="hidden md:block absolute top-full left-0 w-full bg-white/90 dark:bg-gray-950/90 backdrop-blur-3xl border-b border-white/20 dark:border-gray-800/50 shadow-[0_20px_50px_rgba(0,0,0,0.1)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.5)] py-12 z-40 overflow-hidden"
                    >
                        {/* Decorative background glow */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none">
                            <div className="absolute top-[-20%] left-[10%] w-[30%] h-[140%] bg-blue-500/5 blur-[120px] rounded-full" />
                            <div className="absolute top-[-20%] right-[10%] w-[30%] h-[140%] bg-purple-500/5 blur-[120px] rounded-full" />
                        </div>

                        <div className="max-w-7xl mx-auto px-8 relative z-10">
                            <div className="grid grid-cols-3 gap-10">
                                {serviceCategories.map((cat, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="space-y-8"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-2xl shadow-lg shadow-blue-500/20">
                                                {cat.icon}
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-black text-gray-950 dark:text-white uppercase tracking-wider">
                                                    {cat.title}
                                                </h3>
                                                <div className="h-1 w-8 bg-blue-500 rounded-full mt-1.5" />
                                            </div>
                                        </div>

                                        <div className="grid gap-3">
                                            {cat.items.map((item) => (
                                                <button
                                                    key={item.id}
                                                    onClick={() => { navigate(item.path); setIsServicesOpen(false); }}
                                                    className="group flex items-start gap-4 p-4 rounded-2xl hover:bg-white dark:hover:bg-gray-900/50 transition-all duration-300 text-left border border-transparent hover:border-blue-100 dark:hover:border-blue-900/30 hover:shadow-xl hover:shadow-blue-500/5 relative overflow-hidden"
                                                >
                                                    <div className="p-2.5 bg-gray-50 dark:bg-gray-800/50 text-gray-500 group-hover:bg-blue-600 group-hover:text-white rounded-xl transition-all duration-300 shadow-sm">
                                                        {item.icon}
                                                    </div>
                                                    <div className="flex-grow pt-0.5">
                                                        <p className="text-sm font-bold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                                            {item.label}
                                                        </p>
                                                        <p className="text-[11px] text-gray-400 dark:text-gray-500 font-medium mt-0.5 group-hover:text-gray-500 dark:group-hover:text-gray-400 transition-colors">
                                                            Quick access to service
                                                        </p>
                                                    </div>
                                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 translate-x-2 transition-all duration-300 text-blue-500">
                                                        <ChevronDown size={14} className="-rotate-90" />
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            {/* Bottom CTA in Mega Menu */}
                            <div className="mt-12 pt-8 border-t border-gray-100 dark:border-gray-800/50 flex items-center justify-between">
                                <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    {t('home.landing.features.responseTime') || "Support active 24/7"}
                                </div>
                                <button
                                    onClick={() => { navigate('/report'); setIsServicesOpen(false); }}
                                    className="text-xs font-black text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 group"
                                >
                                    View All Services <ChevronDown size={12} className="-rotate-90 group-hover:translate-x-1 transition-transform" />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, x: '100%' }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed inset-0 top-[72px] md:hidden bg-white/95 dark:bg-gray-950/95 backdrop-blur-2xl z-40 overflow-y-auto"
                    >
                        <div className="p-6 space-y-8">
                            {/* Main Nav Links on Mobile */}
                            <div className="space-y-4">
                                {navLinks.map((link) => (
                                    <div key={link.name} className="space-y-4">
                                        <button
                                            onClick={() => link.isMega ? setIsServicesOpen(!isServicesOpen) : handleNavClick(link.path)}
                                            className={`flex w-full items-center justify-between px-5 py-4 text-xl font-black rounded-2xl transition-all ${isServicesOpen && link.isMega
                                                ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/20'
                                                : 'text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-900'
                                                }`}
                                        >
                                            {link.name}
                                            {link.isMega && <ChevronDown size={24} className={`transition-transform duration-300 ${isServicesOpen ? 'rotate-180' : ''}`} />}
                                        </button>

                                        {/* Mobile Services Accordion */}
                                        <AnimatePresence>
                                            {link.isMega && isServicesOpen && (
                                                <motion.div
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: 'auto' }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                    className="overflow-hidden bg-gray-50 dark:bg-gray-900/50 rounded-3xl"
                                                >
                                                    <div className="p-4 space-y-6">
                                                        {serviceCategories.map((cat, cIdx) => (
                                                            <div key={cIdx} className="space-y-3">
                                                                <div className="px-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-400 dark:text-gray-500">
                                                                    {cat.icon} {cat.title}
                                                                </div>
                                                                <div className="grid grid-cols-1 gap-1">
                                                                    {cat.items.map((item) => (
                                                                        <button
                                                                            key={item.id}
                                                                            onClick={() => { navigate(item.path); setIsMenuOpen(false); setIsServicesOpen(false); }}
                                                                            className="flex items-center gap-4 px-4 py-3.5 text-sm font-bold text-gray-700 dark:text-gray-300 hover:text-blue-600 active:scale-95 transition-all"
                                                                        >
                                                                            <div className="p-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm">
                                                                                {item.icon}
                                                                            </div>
                                                                            {item.label}
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                ))}
                            </div>

                            {/* Mobile Extra Actions */}
                            <div className="pt-8 border-t border-gray-100 dark:border-gray-800/50 space-y-6">
                                <div className="px-4">
                                    <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4">Settings</p>
                                    <LanguageSelector />
                                </div>

                                {/* Mobile User/Logout */}
                                <div className="px-4">
                                    {user ? (
                                        <div className="p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl space-y-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                                                    <User size={20} className="text-blue-600 dark:text-blue-400" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-black text-gray-900 dark:text-white">{user.full_name || 'User'}</p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => { handleLogout(); setIsMenuOpen(false); }}
                                                className="flex w-full items-center justify-center gap-2 py-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl font-bold text-sm"
                                            >
                                                <LogOut size={16} />
                                                Logout
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => { navigate('/login'); setIsMenuOpen(false); }}
                                            className="flex w-full items-center justify-center gap-2 py-4 bg-blue-600 text-white rounded-2xl font-black text-sm shadow-xl"
                                        >
                                            <LogIn size={18} />
                                            Login / Sign Up
                                        </button>
                                    )}
                                </div>

                                <div className="px-4 pb-12">
                                    <div className="p-6 bg-gradient-to-br from-blue-600 to-blue-700 rounded-[2rem] text-white shadow-2xl shadow-blue-600/30">
                                        <h4 className="text-lg font-black mb-2">Need help?</h4>
                                        <p className="text-sm opacity-80 mb-6">Our team is available 24/7 to assist with your civic reports.</p>
                                        <button
                                            onClick={() => navigate('/contact')}
                                            className="w-full py-4 bg-white text-blue-600 rounded-2xl font-black text-sm shadow-xl"
                                        >
                                            Contact Support
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
};

export default Navbar;
