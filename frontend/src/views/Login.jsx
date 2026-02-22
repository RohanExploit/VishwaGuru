import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Github, Chrome, ShieldCheck, Zap } from 'lucide-react';
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

    const { login, signup } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || "/";

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
                                <motion.div
                                    initial={{ scale: 0.5 }}
                                    animate={{ scale: 1 }}
                                    className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl shadow-xl shadow-blue-600/20 mb-6"
                                >
                                    <ShieldCheck className="text-white" size={32} />
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
                                            type="password"
                                            required
                                            className="block w-full pl-12 pr-4 py-4 bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-blue-600 dark:focus:border-blue-500 rounded-2xl text-gray-900 dark:text-white font-medium outline-none transition-all"
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                        />
                                    </div>
                                </div>

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
