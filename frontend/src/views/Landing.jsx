import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Building2, MessageCircle, Users, Shield, Star, FileText,
    Search, ArrowRight
} from 'lucide-react';

const Landing = () => {
    const navigate = useNavigate();

    // Animation variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.15,
                delayChildren: 0.2
            }
        }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: {
                type: 'spring',
                stiffness: 100,
                damping: 12
            }
        }
    };

    const slideInLeft = {
        hidden: { x: -50, opacity: 0 },
        visible: {
            x: 0,
            opacity: 1,
            transition: {
                type: 'spring',
                stiffness: 80,
                damping: 20
            }
        }
    };

    const slideInRight = {
        hidden: { x: 50, opacity: 0 },
        visible: {
            x: 0,
            opacity: 1,
            transition: {
                type: 'spring',
                stiffness: 80,
                damping: 20
            }
        }
    };

    return (
        <div className="min-h-screen relative overflow-hidden font-sans bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 selection:bg-blue-200">
            {/* Animated Gradient Background */}

            {/* Top Left - Blue Gradient with Animation */}
            <motion.div
                animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.5, 0.6, 0.5]
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-[-20%] left-[-20%] w-[70%] h-[90%] rounded-full bg-gradient-to-br from-blue-500/50 via-blue-400/40 to-blue-300/30 blur-[100px] -z-10 will-change-transform"
            />

            {/* Top Right - Purple/Pink Gradient with Animation */}
            <motion.div
                animate={{
                    scale: [1, 1.15, 1],
                    opacity: [0.5, 0.55, 0.5]
                }}
                transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                className="absolute top-[-15%] right-[-20%] w-[65%] h-[85%] rounded-full bg-gradient-to-bl from-purple-500/50 via-pink-500/40 to-rose-400/30 blur-[100px] -z-10 will-change-transform"
            />

            {/* Bottom Left - Orange Gradient with Animation */}
            <motion.div
                animate={{
                    scale: [1, 1.12, 1],
                    opacity: [0.45, 0.5, 0.45]
                }}
                transition={{ duration: 9, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                className="absolute bottom-[-15%] left-[-15%] w-[60%] h-[70%] rounded-full bg-gradient-to-tr from-orange-500/45 via-amber-400/35 to-yellow-300/25 blur-[90px] -z-10 will-change-transform"
            />

            {/* Bottom Right - Indigo/Violet Gradient with Animation */}
            <motion.div
                animate={{
                    scale: [1, 1.08, 1],
                    opacity: [0.45, 0.52, 0.45]
                }}
                transition={{ duration: 11, repeat: Infinity, ease: "easeInOut", delay: 3 }}
                className="absolute bottom-[-20%] right-[-15%] w-[55%] h-[75%] rounded-full bg-gradient-to-tl from-indigo-500/45 via-violet-500/35 to-purple-400/25 blur-[95px] -z-10 will-change-transform"
            />




            {/* Header - Fixed and Stable */}
            <header
                className="bg-white/90 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100 shadow-sm"
            >
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-20">
                        {/* Logo */}
                        <div className="flex items-center gap-3 cursor-pointer group">
                            {/* Programmatic Logo - Magnifying Glass with Growth Chart */}
                            <div className="w-10 h-10 relative flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-sm" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    {/* Glass Circle - Perfectly Centered */}
                                    <circle cx="50" cy="50" r="38" stroke="#2D60FF" strokeWidth="8" fill="white" />

                                    {/* Handle */}
                                    <path d="M77 77L92 92" stroke="#2D60FF" strokeWidth="10" strokeLinecap="round" />

                                    {/* Centered Bar Chart - Scaled to fit safely inside */}
                                    <path d="M32 62V52" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M44 62V42" stroke="#2D60FF" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M56 62V33" stroke="#4ADE80" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M68 62V48" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />

                                    {/* Growth Arrow - Fully contained */}
                                    <path d="M28 58L42 45L52 50L70 28" stroke="#16A34A" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M70 28H58M70 28V40" stroke="#16A34A" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </div>
                            <h1 className="text-xl font-bold text-gray-800 tracking-tight">
                                FixMyIndia / <span className="text-blue-600">VishwaGuru</span>
                            </h1>
                        </div>


                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
                {/* Hero Section */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 mb-24 items-center">
                    {/* Left Content (5 cols) */}
                    <motion.div
                        variants={slideInLeft}
                        initial="hidden"
                        animate="visible"
                        className="lg:col-span-5 space-y-8"
                    >
                        <div className="space-y-6">
                            <motion.h1
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.1 }}
                                className="text-4xl md:text-5xl lg:text-6xl font-black text-gray-900 leading-[1.1] tracking-tight"
                            >
                                <motion.span
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.3, delay: 0.2 }}
                                    className="inline-block"
                                >
                                    Empowering Citizens
                                </motion.span>
                                <br />
                                <motion.span
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.3, delay: 0.3 }}
                                    className="text-gray-400 font-bold inline-block"
                                >
                                    for Better Governance
                                </motion.span>
                            </motion.h1>
                            <motion.p
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.4 }}
                                className="text-lg text-gray-600 leading-relaxed max-w-lg"
                            >
                                Report civic issues and get AI-generated solutions. Connect with officials via Telegram to actively participate in governance.
                            </motion.p>
                        </div>

                        <motion.button
                            whileHover={{ scale: 1.05, translateY: -3 }}
                            whileTap={{ scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            onClick={() => navigate('/home')}
                            className="bg-[#2D60FF] hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-[0_10px_20px_-5px_rgba(37,99,235,0.3)] hover:shadow-[0_15px_30px_-5px_rgba(37,99,235,0.5)] transition-all duration-150 flex items-center gap-2 group"
                        >
                            Call Action Issue
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </motion.button>
                    </motion.div>

                    {/* Right Content (7 cols) */}
                    <motion.div
                        variants={slideInRight}
                        initial="hidden"
                        animate="visible"
                        className="lg:col-span-7 grid grid-cols-1 md:grid-cols-2 gap-6 relative"
                    >
                        {/* Decorative background blur */}
                        <div className="absolute -inset-10 bg-blue-50/50 rounded-full blur-3xl -z-10" />

                        <div className="space-y-6">
                            {/* DepMyIndia Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.5 }}
                                whileHover={{ y: -8, scale: 1.02 }}
                                className="bg-gradient-to-r from-[#2D60FF] to-[#1E40AF] rounded-3xl p-6 text-white shadow-xl hover:shadow-2xl border-2 border-transparent hover:border-blue-300 relative overflow-hidden group transition-all duration-150"
                            >
                                <div className="absolute top-0 right-0 p-4 opacity-20">
                                    <Search className="w-8 h-8" />
                                </div>
                                <div className="flex items-start gap-4 mb-8">
                                    <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                                        <Building2 className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg">DepMyIndia</h3>
                                        <p className="text-blue-100 text-sm opacity-90">Report Citizens with <br /> generated civic governance</p>
                                    </div>
                                </div>
                                <div className="h-1 w-full bg-white/20 rounded-full overflow-hidden">
                                    <div className="h-full w-2/3 bg-white/40 rounded-full"></div>
                                </div>
                            </motion.div>

                            {/* Government Services Card */}
                            <motion.div
                                whileHover={{ y: -8, scale: 1.02 }}
                                transition={{ duration: 0.15 }}
                                className="bg-white rounded-3xl p-6 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.05)] hover:shadow-xl border-2 border-gray-100 hover:border-orange-400 group transition-all duration-150"
                            >
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="font-bold text-gray-800">Government Services</h3>
                                    <div className="text-gray-400">•••</div>
                                </div>
                                <div className="bg-gradient-to-br from-orange-50 to-white border border-orange-100 rounded-2xl p-5 group-hover:border-orange-200 transition-colors">
                                    <div className="flex items-start gap-4">
                                        <div className="w-10 h-10 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center flex-shrink-0">
                                            <MessageCircle className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-gray-900 mb-1">Question the Government</h4>
                                            <p className="text-sm text-gray-500 leading-snug">Submit queries, demand transparency, and hold officials accountable</p>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        </div>

                        {/* Community Image Card */}
                        <motion.div
                            whileHover={{ y: -5 }}
                            className="bg-gray-900 rounded-3xl overflow-hidden shadow-xl h-full min-h-[300px] relative group"
                        >
                            <img
                                src="https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                                alt="Community"
                                className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-60 transition-opacity duration-500"
                            />
                            <div className="absolute inset-x-0 bottom-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
                                <p className="text-white font-medium mb-1">Community Action</p>
                                <p className="text-gray-300 text-sm">Join the movement</p>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>

                {/* Bottom Features Section */}
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20"
                >
                    {/* Feature 1 */}
                    <motion.div
                        variants={itemVariants}
                        whileHover={{ y: -8, scale: 1.02 }}
                        transition={{ duration: 0.15 }}
                        className="bg-white p-8 rounded-3xl border-2 border-gray-100 hover:border-blue-400 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.02)] hover:shadow-xl text-center group transition-all duration-150"
                    >
                        <div className="w-16 h-16 mx-auto mb-6 relative">
                            <div className="absolute inset-0 bg-gray-100 rounded-2xl transform rotate-3 group-hover:rotate-12 transition-transform"></div>
                            <div className="absolute inset-0 bg-white border-2 border-gray-100 rounded-2xl flex items-center justify-center relative z-10">
                                <Building2 className="w-8 h-8 text-gray-700" />
                            </div>
                        </div>
                        <h3 className="font-bold text-gray-900 mb-1">Public Trust</h3>
                        <p className="text-gray-500 text-sm">& Ethics</p>
                    </motion.div>

                    {/* Feature 2 (Green Accent) */}
                    <motion.div
                        variants={itemVariants}
                        whileHover={{ y: -8, scale: 1.02 }}
                        transition={{ duration: 0.15 }}
                        className="bg-white p-8 rounded-3xl border-2 border-gray-100 hover:border-green-400 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.02)] hover:shadow-xl text-center group transition-all duration-150"
                    >
                        <div className="w-16 h-16 mx-auto mb-6 bg-green-50 border border-green-100 rounded-2xl flex items-center justify-center">
                            <MessageCircle className="w-8 h-8 text-green-600" />
                        </div>
                        <h3 className="font-bold text-gray-900 mb-1">Civic Issues</h3>
                        <p className="text-gray-500 text-sm">Report problems</p>
                    </motion.div>

                    {/* Feature 3 */}
                    <motion.div
                        variants={itemVariants}
                        whileHover={{ y: -8, scale: 1.02 }}
                        transition={{ duration: 0.15 }}
                        className="bg-white p-8 rounded-3xl border-2 border-gray-100 hover:border-purple-400 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.02)] hover:shadow-xl text-center transition-all duration-150"
                    >
                        <div className="w-16 h-16 mx-auto mb-6 bg-blue-50 border border-blue-100 rounded-2xl flex items-center justify-center">
                            <Star className="w-8 h-8 text-blue-600" />
                        </div>
                        <h3 className="font-bold text-gray-900 mb-1">Voice Your Vote</h3>
                        <p className="text-gray-500 text-xs">Share ideas for better policies</p>
                    </motion.div>

                    {/* AI Header (Span 4th col) */}
                    <motion.div
                        variants={itemVariants}
                        className="space-y-4 flex flex-col justify-center pl-4"
                    >
                        <h2 className="text-2xl font-bold text-gray-900 leading-tight">
                            AI for Democracy <br /> & Civic Actions
                        </h2>
                        <p className="text-gray-500 text-sm">
                            Leveraging technology for transparent governance and faster resolutions.
                        </p>
                    </motion.div>
                </motion.div>

                {/* AI Features Grid */}
                {/* Professional Stats/Features Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mt-16">
                    {[
                        {
                            icon: <Star className="w-6 h-6" />,
                            title: "Smart Analysis",
                            subtitle: "AI-Powered Insights",
                            bg: "bg-blue-50",
                            color: "text-blue-600",
                            border: "hover:border-blue-200"
                        },
                        {
                            icon: <Users className="w-6 h-6" />,
                            title: "Community",
                            subtitle: "10k+ Active Citizens",
                            bg: "bg-purple-50",
                            color: "text-purple-600",
                            border: "hover:border-purple-200"
                        },
                        {
                            icon: <Shield className="w-6 h-6" />,
                            title: "Secure & Safe",
                            subtitle: "Verified Reports",
                            bg: "bg-emerald-50",
                            color: "text-emerald-600",
                            border: "hover:border-emerald-200"
                        },
                        {
                            icon: <FileText className="w-6 h-6" />,
                            title: "Quick Action",
                            subtitle: "24h Response Time",
                            bg: "bg-orange-50",
                            color: "text-orange-600",
                            border: "hover:border-orange-200"
                        }
                    ].map((item, index) => (
                        <motion.div
                            key={index}
                            whileHover={{ y: -5 }}
                            className={`bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 group ${item.border}`}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className={`w-12 h-12 ${item.bg} ${item.color} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                                    {item.icon}
                                </div>
                            </div>
                            <h3 className="font-bold text-gray-900 text-lg">{item.title}</h3>
                            <p className="text-gray-500 text-sm font-medium mt-1">{item.subtitle}</p>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Simple Footer */}
            <div className="text-center py-8 bg-black text-white text-sm border-t border-gray-800 mt-12">
                © {new Date().getFullYear()} VishwaGuru. All rights reserved.
            </div>        </div>
    );
};

export default Landing;
