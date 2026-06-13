import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Github, Chrome, ShieldCheck, Zap, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

function Login({ initialIsLogin = true }) {
    const [isLogin, setIsLogin] = useState(initialIsLogin);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [passwordFocused, setPasswordFocused] = useState(false);

    const { login, signup } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || "/";

    // Password strength calculator
    const getPasswordStrength = (pwd) => {
        if (!pwd) return { score: 0, label: '', color: '', width: '0%' };
        let score = 0;
        if (pwd.length >= 6) score++;
        if (pwd.length >= 10) score++;
        if (/[A-Z]/.test(pwd)) score++;
        if (/[a-z]/.test(pwd)) score++;
        if (/[0-9]/.test(pwd)) score++;
        if (/[^A-Za-z0-9]/.test(pwd)) score++;

        if (score <= 2) return { score, label: 'Weak', color: 'bg-red-500', textColor: 'text-red-500', width: '25%' };
        if (score <= 3) return { score, label: 'Fair', color: 'bg-orange-500', textColor: 'text-orange-500', width: '50%' };
        if (score <= 4) return { score, label: 'Good', color: 'bg-yellow-500', textColor: 'text-yellow-500', width: '75%' };
        return { score, label: 'Strong', color: 'bg-green-500', textColor: 'text-green-500', width: '100%' };
    };

    const passwordStrength = getPasswordStrength(password);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                const user = await login(email, password);
                if (!user) {
                    setError('Authentication failed. Please check your credentials.');
                    return;
                }
                if (user.role === 'admin') {
                    navigate('/admin/dashboard', { replace: true });
                } else {
                    navigate(from, { replace: true });
                }
            } else {
                await signup({ email, password, full_name: fullName });
                const user = await login(email, password);
                if (!user) {
                    setError('Signup successful, but auto-login failed. Please sign in manually.');
                    return;
                }
                if (user.role === 'admin') {
                    navigate('/admin/dashboard', { replace: true });
                } else {
                    navigate(from, { replace: true });
                }
            }
        } catch (err) {
            setError(err.message || 'Failed to authenticate');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center py-20 px-4 relative overflow-hidden">
            {/* Decorative Brushes */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none"></div>
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px] pointer-events-none"></div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-xl w-full"
            >
                <div className="bg-white dark:bg-gray-900 rounded-[32px] shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-800 relative z-10">
                    <div className="grid grid-cols-1 md:grid-cols-1">
                        <div className="p-8 lg:p-12">
                            <div className="text-center mb-10 space-y-2">
                                {/* Animated Cat Mascot */}
                                <motion.div
                                    initial={{ scale: 0, rotate: -10 }}
                                    animate={{ scale: 1, rotate: 0 }}
                                    transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                                    className="relative inline-block mb-4"
                                >
                                    <div className="relative w-28 h-28 mx-auto">
                                        {/* Cat body */}
                                        <motion.div
                                            animate={{ y: [0, -3, 0] }}
                                            transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                                            className="relative"
                                        >
                                            {/* Ears */}
                                            <div className="absolute -top-3 left-5 w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-b-[18px] border-b-amber-400 rotate-[-15deg]" />
                                            <div className="absolute -top-3 right-5 w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-b-[18px] border-b-amber-400 rotate-[15deg]" />
                                            {/* Inner ears */}
                                            <div className="absolute -top-1 left-6 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[12px] border-b-pink-300 rotate-[-15deg]" />
                                            <div className="absolute -top-1 right-6 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[12px] border-b-pink-300 rotate-[15deg]" />

                                            {/* Head */}
                                            <div className="w-24 h-20 bg-amber-400 rounded-[50%] mx-auto mt-2 relative overflow-hidden shadow-lg">
                                                {/* Face */}
                                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                                    {/* Eyes */}
                                                    <div className="flex gap-6 mb-1 mt-1">
                                                        <motion.div
                                                            animate={
                                                                passwordFocused && !showPassword
                                                                    ? { scaleY: 0.1, y: 2 }
                                                                    : { scaleY: 1, y: 0 }
                                                            }
                                                            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                                                            className="relative"
                                                        >
                                                            <div className="w-4 h-4 bg-gray-800 rounded-full relative">
                                                                <div className="absolute top-0.5 left-0.5 w-1.5 h-1.5 bg-white rounded-full" />
                                                            </div>
                                                        </motion.div>
                                                        <motion.div
                                                            animate={
                                                                passwordFocused && !showPassword
                                                                    ? { scaleY: 0.1, y: 2 }
                                                                    : { scaleY: 1, y: 0 }
                                                            }
                                                            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                                                            className="relative"
                                                        >
                                                            <div className="w-4 h-4 bg-gray-800 rounded-full relative">
                                                                <div className="absolute top-0.5 left-0.5 w-1.5 h-1.5 bg-white rounded-full" />
                                                            </div>
                                                        </motion.div>
                                                    </div>

                                                    {/* Paws covering eyes */}
                                                    <AnimatePresence>
                                                        {passwordFocused && !showPassword && (
                                                            <>
                                                                <motion.div
                                                                    initial={{ y: 30, opacity: 0 }}
                                                                    animate={{ y: -14, opacity: 1 }}
                                                                    exit={{ y: 30, opacity: 0 }}
                                                                    transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                                                                    className="absolute left-2 w-8 h-6 bg-amber-300 rounded-full border-2 border-amber-500/30 z-10"
                                                                />
                                                                <motion.div
                                                                    initial={{ y: 30, opacity: 0 }}
                                                                    animate={{ y: -14, opacity: 1 }}
                                                                    exit={{ y: 30, opacity: 0 }}
                                                                    transition={{ type: 'spring', stiffness: 400, damping: 25, delay: 0.05 }}
                                                                    className="absolute right-2 w-8 h-6 bg-amber-300 rounded-full border-2 border-amber-500/30 z-10"
                                                                />
                                                            </>
                                                        )}
                                                    </AnimatePresence>

                                                    {/* Nose */}
                                                    <div className="w-2.5 h-2 bg-pink-400 rounded-full mt-0.5" />

                                                    {/* Mouth */}
                                                    <motion.div
                                                        animate={passwordFocused && !showPassword ? { scaleX: 0.6 } : { scaleX: 1 }}
                                                        className="flex gap-0.5 -mt-0.5"
                                                    >
                                                        <div className="w-2.5 h-1.5 border-b-2 border-gray-700 rounded-b-full" />
                                                        <div className="w-2.5 h-1.5 border-b-2 border-gray-700 rounded-b-full" />
                                                    </motion.div>

                                                    {/* Whiskers */}
                                                    <div className="absolute left-0 top-[52%] space-y-1">
                                                        <div className="w-5 h-[1px] bg-gray-600/40 -rotate-6" />
                                                        <div className="w-6 h-[1px] bg-gray-600/40" />
                                                    </div>
                                                    <div className="absolute right-0 top-[52%] space-y-1">
                                                        <div className="w-5 h-[1px] bg-gray-600/40 rotate-6 ml-auto" />
                                                        <div className="w-6 h-[1px] bg-gray-600/40 ml-auto" />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Blush spots */}
                                            <motion.div
                                                animate={{ opacity: passwordFocused ? 0.8 : 0.4 }}
                                                className="absolute bottom-3 left-3 w-4 h-2.5 bg-pink-300/60 rounded-full blur-[2px]"
                                            />
                                            <motion.div
                                                animate={{ opacity: passwordFocused ? 0.8 : 0.4 }}
                                                className="absolute bottom-3 right-3 w-4 h-2.5 bg-pink-300/60 rounded-full blur-[2px]"
                                            />
                                        </motion.div>
                                    </div>

                                    {/* Speech bubble */}
                                    <AnimatePresence>
                                        {passwordFocused && !showPassword && (
                                            <motion.div
                                                initial={{ opacity: 0, scale: 0.5, x: 20 }}
                                                animate={{ opacity: 1, scale: 1, x: 0 }}
                                                exit={{ opacity: 0, scale: 0.5, x: 20 }}
                                                className="absolute -right-4 top-2 bg-white dark:bg-gray-800 text-xs font-bold text-gray-600 dark:text-gray-300 px-2.5 py-1.5 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700"
                                            >
                                                🙈 I won't peek!
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                    <AnimatePresence>
                                        {passwordFocused && showPassword && (
                                            <motion.div
                                                initial={{ opacity: 0, scale: 0.5, x: 20 }}
                                                animate={{ opacity: 1, scale: 1, x: 0 }}
                                                exit={{ opacity: 0, scale: 0.5, x: 20 }}
                                                className="absolute -right-4 top-2 bg-white dark:bg-gray-800 text-xs font-bold text-gray-600 dark:text-gray-300 px-2.5 py-1.5 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700"
                                            >
                                                👀 Oh, I see!
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.div>
                                <h2 className="text-3xl font-black text-gray-900 dark:text-white">
                                    {isLogin ? 'Welcome Back!' : 'Join the Movement'}
                                </h2>
                                <p className="text-gray-500 dark:text-gray-400 font-medium">
                                    {isLogin ? 'Enter your details to access your dashboard' : 'Create an account to start reporting civic issues'}
                                </p>
                            </div>

                            <form className="space-y-5" onSubmit={handleSubmit}>
                                <AnimatePresence mode="wait">
                                    {!isLogin && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="space-y-1.5"
                                        >
                                            <label className="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1">Full Name</label>
                                            <div className="relative group">
                                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-600 transition-colors">
                                                    <User size={20} />
                                                </div>
                                                <input
                                                    type="text"
                                                    required
                                                    className="block w-full pl-12 pr-4 py-4 bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-blue-600 dark:focus:border-blue-500 rounded-2xl text-gray-900 dark:text-white font-medium outline-none transition-all"
                                                    placeholder="John Doe"
                                                    value={fullName}
                                                    onChange={(e) => setFullName(e.target.value)}
                                                />
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <div className="space-y-1.5">
                                    <label className="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1">Email Address</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-600 transition-colors">
                                            <Mail size={20} />
                                        </div>
                                        <input
                                            type="email"
                                            required
                                            className="block w-full pl-12 pr-4 py-4 bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-blue-600 dark:focus:border-blue-500 rounded-2xl text-gray-900 dark:text-white font-medium outline-none transition-all"
                                            placeholder="name@example.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <div className="flex justify-between items-center px-1">
                                        <label className="text-sm font-bold text-gray-700 dark:text-gray-300">Password</label>
                                        <Link to="#" className="text-xs font-bold text-blue-600 hover:text-blue-700">Forgot?</Link>
                                    </div>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-600 transition-colors">
                                            <Lock size={20} />
                                        </div>
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            required
                                            className="block w-full pl-12 pr-12 py-4 bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-blue-600 dark:focus:border-blue-500 rounded-2xl text-gray-900 dark:text-white font-medium outline-none transition-all"
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            onFocus={() => setPasswordFocused(true)}
                                            onBlur={() => setPasswordFocused(false)}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-blue-600 transition-colors"
                                            tabIndex={-1}
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                        </button>
                                    </div>
                                </div>
                                {/* Password Strength Indicator - Signup only */}
                                <AnimatePresence>
                                    {!isLogin && password && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="space-y-2 -mt-2"
                                        >
                                            {/* Strength bar */}
                                            <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden mx-1">
                                                <motion.div
                                                    initial={{ width: '0%' }}
                                                    animate={{ width: passwordStrength.width }}
                                                    transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                                                    className={`h-full rounded-full ${passwordStrength.color}`}
                                                />
                                            </div>
                                            {/* Strength label + criteria */}
                                            <div className="flex justify-between items-center px-1">
                                                <motion.span
                                                    key={passwordStrength.label}
                                                    initial={{ opacity: 0, y: -5 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    className={`text-xs font-bold ${passwordStrength.textColor}`}
                                                >
                                                    {passwordStrength.label}
                                                </motion.span>
                                                <div className="flex gap-1.5">
                                                    {[
                                                        { test: password.length >= 6, tip: '6+' },
                                                        { test: /[A-Z]/.test(password), tip: 'A-Z' },
                                                        { test: /[0-9]/.test(password), tip: '0-9' },
                                                        { test: /[^A-Za-z0-9]/.test(password), tip: '#@!' },
                                                    ].map(({ test, tip }) => (
                                                        <span
                                                            key={tip}
                                                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md transition-all ${
                                                                test
                                                                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-600'
                                                            }`}
                                                        >
                                                            {tip}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                                {error && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 rounded-2xl text-red-600 dark:text-red-400 text-sm font-bold text-center"
                                    >
                                        {error}
                                    </motion.div>
                                )}

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl shadow-xl shadow-blue-600/20 transition-all flex items-center justify-center gap-2 group disabled:opacity-50"
                                >
                                    {loading ? (
                                        <span className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                    ) : (
                                        <>
                                            {isLogin ? 'Sign In' : 'Create Account'}
                                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                        </>
                                    )}
                                </button>

                                <div className="relative py-4">
                                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-100 dark:border-gray-800"></div></div>
                                    <div className="relative flex justify-center text-xs uppercase"><span className="bg-white dark:bg-gray-900 px-4 text-gray-500 font-bold">Or continue with</span></div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <button type="button" className="flex items-center justify-center gap-2 py-3 border-2 border-gray-100 dark:border-gray-800 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-bold text-sm">
                                        <Chrome size={18} className="text-red-500" /> Google
                                    </button>
                                    <button type="button" className="flex items-center justify-center gap-2 py-3 border-2 border-gray-100 dark:border-gray-800 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-bold text-sm">
                                        <Github size={18} /> GitHub
                                    </button>
                                </div>

                                <p className="text-center text-sm font-bold text-gray-500 mt-8">
                                    {isLogin ? "Don't have an account?" : "Already have an account?"}
                                    <button
                                        type="button"
                                        className="ml-2 text-blue-600 hover:underline"
                                        onClick={() => {
                                            setIsLogin(!isLogin);
                                            setError('');
                                        }}
                                    >
                                        {isLogin ? 'Create one now' : 'Sign in here'}
                                    </button>
                                </p>
                            </form>
                        </div>
                    </div>
                </div>

                {/* Trust Badges */}
                <div className="mt-12 flex items-center justify-center gap-8 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
                    <div className="flex items-center gap-2 font-black text-gray-400"><Zap size={20} /> FAST</div>
                    <div className="flex items-center gap-2 font-black text-gray-400"><ShieldCheck size={20} /> SECURE</div>
                    <div className="flex items-center gap-2 font-black text-gray-400 font-sans">VISHWAGURU</div>
                </div>
            </motion.div>
        </div>
    );
}

export default Login;
