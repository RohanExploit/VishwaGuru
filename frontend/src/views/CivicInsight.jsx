import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { miscApi } from '../api';
import {
    Activity, CheckCircle2, Clock, AlertTriangle,
    MapPin, Bell, Shield, TrendingUp, Users
} from 'lucide-react';

const CivicInsight = () => {
    // eslint-disable-next-line no-unused-vars
    const { t } = useTranslation();
    const [stats, setStats] = useState({ total_issues: 0, resolved_issues: 0, pending_issues: 0 });
    const [loading, setLoading] = useState(true);
    const [watchArea, setWatchArea] = useState('');
    const [subscribed, setSubscribed] = useState(false);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await miscApi.getStats();
                if (data) setStats(data);
            } catch (error) {
                console.error("Failed to fetch stats", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const handleSubscribe = (e) => {
        e.preventDefault();
        if (watchArea) {
            setSubscribed(true);
            // In a real app, this would call an API to subscribe
        }
    };

    // Calculate percentages for the simple bar chart
    const total = stats.total_issues || 1; // Avoid division by zero
    const resolvedPercent = Math.round((stats.resolved_issues / total) * 100);
    const pendingPercent = Math.round((stats.pending_issues / total) * 100);
    const criticalPercent = 100 - resolvedPercent - pendingPercent; // Mock critical for visualization

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-black text-gray-900 dark:text-white tracking-tight mb-4">
                    Civic Intelligence Dashboard
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                    Real-time insights into your city's health and community engagement.
                </p>
            </div>

            {/* Key Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-800 flex items-center justify-between group hover:scale-[1.02] transition-transform">
                    <div>
                        <p className="text-sm font-black uppercase tracking-widest text-gray-500 mb-1">Total Reports</p>
                        <h3 className="text-4xl font-black text-blue-600 dark:text-blue-400">
                            {loading ? '...' : stats.total_issues}
                        </h3>
                    </div>
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-2xl text-blue-600 dark:text-blue-400 group-hover:rotate-12 transition-transform">
                        <Activity size={32} />
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-800 flex items-center justify-between group hover:scale-[1.02] transition-transform">
                    <div>
                        <p className="text-sm font-black uppercase tracking-widest text-gray-500 mb-1">Resolved</p>
                        <h3 className="text-4xl font-black text-emerald-600 dark:text-emerald-400">
                            {loading ? '...' : stats.resolved_issues}
                        </h3>
                    </div>
                    <div className="p-4 bg-emerald-50 dark:bg-emerald-900/30 rounded-2xl text-emerald-600 dark:text-emerald-400 group-hover:rotate-12 transition-transform">
                        <CheckCircle2 size={32} />
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-800 flex items-center justify-between group hover:scale-[1.02] transition-transform">
                    <div>
                        <p className="text-sm font-black uppercase tracking-widest text-gray-500 mb-1">Pending Action</p>
                        <h3 className="text-4xl font-black text-amber-600 dark:text-amber-400">
                            {loading ? '...' : stats.pending_issues}
                        </h3>
                    </div>
                    <div className="p-4 bg-amber-50 dark:bg-amber-900/30 rounded-2xl text-amber-600 dark:text-amber-400 group-hover:rotate-12 transition-transform">
                        <Clock size={32} />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Visual Analytics Card */}
                <div className="bg-white dark:bg-gray-900 rounded-[2.5rem] p-8 shadow-2xl border border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded-2xl text-indigo-600 dark:text-indigo-400">
                            <TrendingUp size={24} />
                        </div>
                        <h2 className="text-2xl font-black text-gray-900 dark:text-white">Resolution Metrics</h2>
                    </div>

                    <div className="space-y-8">
                        {/* Custom Bar Chart */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm font-bold">
                                <span className="flex items-center gap-2 text-emerald-600">
                                    <CheckCircle2 size={16} /> Resolved
                                </span>
                                <span>{resolvedPercent}%</span>
                            </div>
                            <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-emerald-500 rounded-full transition-all duration-1000"
                                    style={{ width: `${loading ? 0 : resolvedPercent}%` }}
                                ></div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm font-bold">
                                <span className="flex items-center gap-2 text-amber-600">
                                    <Clock size={16} /> In Progress
                                </span>
                                <span>{pendingPercent}%</span>
                            </div>
                            <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-amber-500 rounded-full transition-all duration-1000 delay-100"
                                    style={{ width: `${loading ? 0 : pendingPercent}%` }}
                                ></div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm font-bold">
                                <span className="flex items-center gap-2 text-rose-600">
                                    <AlertTriangle size={16} /> Critical Attention
                                </span>
                                <span>{criticalPercent > 0 ? criticalPercent : 0}%</span>
                            </div>
                            <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-rose-500 rounded-full transition-all duration-1000 delay-200"
                                    style={{ width: `${loading ? 0 : Math.max(0, criticalPercent)}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Neighborhood Watch Card */}
                <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[2.5rem] p-8 shadow-2xl text-white relative overflow-hidden">
                    {/* Background Pattern */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-black/10 rounded-full blur-3xl -ml-16 -mb-16 pointer-events-none"></div>

                    <div className="relative z-10 h-full flex flex-col justify-between">
                        <div>
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 bg-white/20 backdrop-blur-md rounded-2xl">
                                    <Shield size={24} className="text-white" />
                                </div>
                                <h2 className="text-2xl font-black">Neighborhood Watch</h2>
                            </div>
                            <p className="text-blue-100 font-medium mb-8 leading-relaxed">
                                Join the community safety network. Get instant alerts for civic issues reported in your area and help keep your neighborhood safe.
                            </p>
                        </div>

                        {!subscribed ? (
                            <form onSubmit={handleSubscribe} className="space-y-4">
                                <div className="relative">
                                    <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                    <input
                                        type="text"
                                        placeholder="Enter your area or pincode"
                                        className="w-full bg-white text-gray-900 rounded-2xl py-4 pl-12 pr-4 font-bold placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
                                        value={watchArea}
                                        onChange={(e) => setWatchArea(e.target.value)}
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="w-full bg-black/20 hover:bg-black/30 backdrop-blur-md text-white py-4 rounded-2xl font-black flex items-center justify-center gap-2 transition-all border border-white/20"
                                >
                                    <Bell size={20} />
                                    Subscribe to Alerts
                                </button>
                            </form>
                        ) : (
                            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 text-center border border-white/20 animate-fade-in">
                                <div className="w-12 h-12 bg-green-400 rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg">
                                    <CheckCircle2 size={24} className="text-white" />
                                </div>
                                <h3 className="text-xl font-black mb-1">You're Covered!</h3>
                                <p className="text-blue-100 text-sm">
                                    Alerts active for <span className="font-bold text-white">{watchArea}</span>.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Recent Activity Mockup */}
            <div className="mt-12">
                <div className="flex items-center gap-4 mb-6">
                    <div className="p-3 bg-orange-50 dark:bg-orange-900/30 rounded-2xl text-orange-600 dark:text-orange-400">
                        <Users size={24} />
                    </div>
                    <h2 className="text-2xl font-black text-gray-900 dark:text-white">Community Pulse</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="bg-white dark:bg-gray-900 p-5 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-lg transition-all">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700"></div>
                                <div>
                                    <p className="text-xs font-black text-gray-900 dark:text-white">Resident</p>
                                    <p className="text-[10px] text-gray-500">2 hours ago</p>
                                </div>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                                "Spotted a new pothole on Main St. Thanks for the quick fix on the last one!"
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default CivicInsight;
