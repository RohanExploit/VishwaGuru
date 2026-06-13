import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
    Building2, MessageCircle, Users, Shield, Star, FileText,
    Search, ArrowRight, CheckCircle2, Globe, Heart, Zap
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Landing = () => {
    const navigate = useNavigate();
    const { t } = useTranslation();

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

    return (
        <div className="min-h-screen relative overflow-x-hidden font-sans bg-white dark:bg-gray-950 selection:bg-blue-200 dark:selection:bg-blue-800 transition-colors duration-300">
            <Navbar />

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
                {/* Background Blobs */}
                <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl animate-pulse"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                            className="lg:col-span-12 xl:col-span-6 space-y-10"
                        >
                            <div className="space-y-6">
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 text-blue-600 dark:text-blue-400 text-sm font-bold"
                                >
                                    <Zap size={16} />
                                    <span>{t('home.smartScanner') || 'Next Gen Civic Platform'}</span>
                                </motion.div>
                                <h1 className="text-5xl md:text-6xl lg:text-7xl font-black text-gray-900 dark:text-white leading-[1.05] tracking-tight">
                                    {t('home.landing.empowering')} <br />
                                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                                        {t('home.landing.governance')}
                                    </span>
                                </h1>
                                <p className="text-xl text-gray-500 dark:text-gray-400 leading-relaxed max-w-xl">
                                    {t('home.landing.subtitle')}
                                </p>
                            </div>

                            <div className="flex flex-col sm:flex-row gap-4">
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => navigate('/login')}
                                    className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-5 rounded-2xl font-bold text-lg shadow-xl shadow-blue-600/20 transition-all flex items-center justify-center gap-2 group"
                                >
                                    {t('home.landing.cta.button') || t('home.landing.cta')}
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </motion.button>
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    className="bg-white dark:bg-gray-900 border-2 border-gray-100 dark:border-gray-800 text-gray-900 dark:text-white px-10 py-5 rounded-2xl font-bold text-lg hover:border-blue-600 transition-all flex items-center justify-center gap-2"
                                >
                                    {t('nav.about')}
                                </motion.button>
                            </div>

                            <div className="flex items-center gap-6 pt-4">
                                <div className="flex -space-x-3">
                                    {[1, 2, 3, 4].map((i) => (
                                        <div key={i} className="w-10 h-10 rounded-full border-2 border-white dark:border-gray-950 bg-gray-200 dark:bg-gray-800 flex items-center justify-center overflow-hidden">
                                            <img src={`https://i.pravatar.cc/100?img=${i + 10}`} alt="User" />
                                        </div>
                                    ))}
                                </div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                                    <span className="text-gray-900 dark:text-white font-bold">10k+</span> {t('home.landing.features.citizenCount')}
                                </p>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                            className="lg:col-span-12 xl:col-span-6 relative"
                        >
                            <div className="relative z-10 rounded-3xl overflow-hidden shadow-2xl border-8 border-white dark:border-gray-900">
                                <img
                                    src="https://images.unsplash.com/photo-1573164713988-8665fc963095?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
                                    alt="Platform Demo"
                                    className="w-full h-auto object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-gray-900/60 to-transparent flex items-end p-8">
                                    <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 w-full">
                                        <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center text-white shadow-lg">
                                            <CheckCircle2 />
                                        </div>
                                        <div>
                                            <p className="text-white font-bold text-sm">Issue #3928 Resolved</p>
                                            <p className="text-gray-300 text-xs text-blue-400">Pothole fixed in 48 hours</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Decorative elements */}
                            <div className="absolute -top-10 -right-10 w-40 h-40 bg-orange-400/20 rounded-full blur-2xl"></div>
                            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-400/20 rounded-full blur-2xl"></div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Services Section */}
            <section id="services" className="py-32 relative overflow-hidden transition-colors duration-300">
                {/* Visual Background Elements */}
                <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-800 to-transparent"></div>
                <div className="absolute -top-24 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-[120px] pointer-events-none"></div>
                <div className="absolute top-1/2 right-0 w-80 h-80 bg-purple-500/5 rounded-full blur-[100px] pointer-events-none"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center max-w-3xl mx-auto mb-24 space-y-6"
                    >
                        <h2 className="text-blue-600 dark:text-blue-400 font-black tracking-[0.2em] uppercase text-xs">
                            {t('nav.services')}
                        </h2>
                        <h3 className="text-4xl md:text-5xl lg:text-6xl font-black text-gray-900 dark:text-white leading-[1.1]">
                            {t('home.landing.aiDemocracy') || 'AI-Powered Digital Democracy'}
                        </h3>
                        <div className="h-1.5 w-24 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mx-auto mt-4"></div>
                        <p className="text-gray-500 dark:text-gray-400 text-lg md:text-xl font-medium pt-2">
                            {t('home.landing.features.aiDesc') || 'State-of-the-art tools for the modern citizen.'}
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <Zap size={28} />,
                                title: t('home.smartScanner') || 'Real-time Detection',
                                desc: 'AI-powered detection for potholes, garbage, and more.',
                                color: "blue",
                                tag: "AI Feature"
                            },
                            {
                                icon: <Globe size={28} />,
                                title: t('home.landing.features.publicTrust') || 'Global Transparency',
                                desc: 'Every report is tracked and verified for absolute accountability.',
                                color: "emerald",
                                tag: "Platform"
                            },
                            {
                                icon: <Shield size={28} />,
                                title: t('home.landing.features.secureSafe') || 'Secure Escapes',
                                desc: 'End-to-end encrypted reporting and privacy-first data handling.',
                                color: "indigo",
                                tag: "Security"
                            },
                            {
                                icon: <Star size={28} />,
                                title: t('home.landing.features.smartAnalysis') || 'Data Insights',
                                desc: 'Advanced heatmaps and trend analysis for civic planning.',
                                color: "purple",
                                tag: "Analysis"
                            },
                            {
                                icon: <Users size={28} />,
                                title: t('home.landing.cards.communityAction') || 'Social Impact',
                                desc: 'Collaborate with fellow citizens and organize local cleanups.',
                                color: "orange",
                                tag: "Community"
                            },
                            {
                                icon: <FileText size={28} />,
                                title: t('home.landing.features.quickAction') || 'Resolution Hub',
                                desc: 'Direct escalation to relevant authorities with automated tracking.',
                                color: "rose",
                                tag: "Action"
                            }
                        ].map((service, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                                className="group relative"
                                onClick={() => navigate('/report')}
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent dark:from-white/5 dark:to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[2.5rem] blur-xl -z-10"></div>
                                <div className="h-full bg-white/40 dark:bg-gray-950/40 backdrop-blur-xl p-10 rounded-[2.5rem] border border-white/20 dark:border-gray-800/50 shadow-[0_8px_32px_rgba(0,0,0,0.05)] hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-500 hover:-translate-y-2 flex flex-col items-start text-left cursor-pointer">
                                    <div className={`p-4 rounded-2xl bg-gradient-to-br from-${service.color}-500 to-${service.color}-600 text-white mb-8 shadow-lg shadow-${service.color}-500/20 group-hover:scale-110 transition-transform duration-500`}>
                                        {service.icon}
                                    </div>
                                    <div className={`px-3 py-1 bg-${service.color}-100/50 dark:bg-${service.color}-900/20 text-${service.color}-600 dark:text-${service.color}-400 text-[10px] font-black uppercase tracking-widest rounded-full mb-4`}>
                                        {service.tag}
                                    </div>
                                    <h4 className="text-2xl font-black text-gray-900 dark:text-white mb-4 leading-tight">{service.title}</h4>
                                    <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-medium">
                                        {service.desc}
                                    </p>
                                    <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-800/50 w-full">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); navigate('/report'); }}
                                            className="text-sm font-black text-blue-600 dark:text-blue-400 flex items-center gap-2 group/btn transition-all"
                                        >
                                            Learn More
                                            <ArrowRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* Secondary Services/Demos CTA */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.5 }}
                        className="mt-24 p-8 md:p-12 rounded-[3.5rem] bg-gray-900 dark:bg-blue-600 flex flex-col md:flex-row items-center justify-between gap-10 shadow-2xl relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-20 -mt-20"></div>
                        <div className="relative z-10">
                            <h4 className="text-3xl font-black text-white mb-4">Want to see it in action?</h4>
                            <p className="text-gray-400 dark:text-blue-100 text-lg">Explore our live demo with interactive reporting tools.</p>
                        </div>
                        <button
                            onClick={() => navigate('/login')}
                            className="relative z-10 bg-white dark:bg-gray-950 text-gray-900 dark:text-white px-10 py-5 rounded-2xl font-black shadow-xl hover:scale-105 transition-transform"
                        >
                            Get Started Now
                        </button>
                    </motion.div>
                </div>
            </section>

            {/* About Section */}
            <section id="about" className="py-24 overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            className="relative"
                        >
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-4 pt-12">
                                    <div className="rounded-3xl overflow-hidden shadow-lg h-64 bg-blue-600 flex flex-col items-center justify-center text-white p-6 text-center">
                                        <Globe size={48} className="mb-4" />
                                        <h5 className="text-4xl font-black">150+</h5>
                                        <p className="text-sm opacity-80">Cities Covered</p>
                                    </div>
                                    <div className="rounded-3xl overflow-hidden shadow-lg h-48">
                                        <img src="https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=400&q=80" alt="About 1" className="w-full h-full object-cover" />
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div className="rounded-3xl overflow-hidden shadow-lg h-48">
                                        <img src="https://images.unsplash.com/photo-1541810270633-93720766f628?auto=format&fit=crop&w=400&q=80" alt="About 2" className="w-full h-full object-cover" />
                                    </div>
                                    <div className="rounded-3xl overflow-hidden shadow-lg h-64 bg-indigo-600 flex flex-col items-center justify-center text-white p-6 text-center">
                                        <Heart size={48} className="mb-4" />
                                        <h5 className="text-4xl font-black">98%</h5>
                                        <p className="text-sm opacity-80">Satisfaction Rate</p>
                                    </div>
                                </div>
                            </div>
                            <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-600/10 rounded-full blur-[100px]"></div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="space-y-8"
                        >
                            <div className="space-y-4">
                                <h2 className="text-blue-600 dark:text-blue-400 font-black tracking-widest uppercase text-sm">{t('nav.about')}</h2>
                                <h3 className="text-4xl md:text-5xl font-black text-gray-900 dark:text-white leading-tight">
                                    {t('home.landing.about.title').split('Authority')[0]} <span className="text-blue-600">Citizens</span> & <span className="text-indigo-600">Authority</span>
                                </h3>
                                <p className="text-gray-500 dark:text-gray-400 text-lg leading-relaxed">
                                    {t('home.landing.about.subtitle')}
                                </p>
                            </div>

                            <ul className="space-y-4">
                                {[
                                    t('home.landing.about.feature1'),
                                    t('home.landing.about.feature2'),
                                    t('home.landing.about.feature3'),
                                    t('home.landing.about.feature4')
                                ].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-gray-700 dark:text-gray-300 font-bold">
                                        <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
                                            <CheckCircle2 size={16} />
                                        </div>
                                        {item}
                                    </li>
                                ))}
                            </ul>

                            <button className="text-blue-600 font-black flex items-center gap-2 group">
                                {t('home.landing.about.mission')}
                                <ArrowRight className="group-hover:translate-x-1 transition-transform" />
                            </button>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section id="contact" className="py-24">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div
                        whileHover={{ scale: 1.01 }}
                        className="relative rounded-[40px] bg-gradient-to-tr from-blue-700 via-blue-600 to-indigo-700 p-12 lg:p-24 overflow-hidden shadow-2xl shadow-blue-600/30"
                    >
                        {/* Decorative Circles */}
                        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
                        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-indigo-400/20 rounded-full blur-3xl"></div>

                        <div className="relative z-10 text-center space-y-10">
                            <h2 className="text-4xl md:text-6xl font-black text-white leading-tight">
                                {t('home.landing.cta.title')}
                            </h2>
                            <p className="text-blue-100 text-xl max-w-2xl mx-auto opacity-90">
                                {t('home.landing.cta.subtitle')}
                            </p>
                            <div className="flex flex-col sm:flex-row gap-4 justify-center">
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => navigate('/signup')}
                                    className="bg-white text-blue-600 px-10 py-5 rounded-2xl font-black text-lg transition-all shadow-xl shadow-black/10"
                                >
                                    {t('home.landing.cta.button')}
                                </motion.button>
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    className="bg-blue-800/40 backdrop-blur-md border border-white/20 text-white px-10 py-5 rounded-2xl font-black text-lg hover:bg-blue-800/60 transition-all"
                                >
                                    {t('home.landing.cta.support')}
                                </motion.button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default Landing;
