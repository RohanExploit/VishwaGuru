import React, { useState, useEffect } from 'react';
import { miscApi } from '../api';
import { ArrowLeft, CheckCircle, Clock, PieChart } from 'lucide-react';

const StatsView = ({ setView }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await miscApi.getStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch stats", err);
        setError("Failed to load statistics.");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );

  if (error) return <div className="text-red-600 p-8 text-center">{error}</div>;

  const maxCount = Math.max(...Object.values(stats.issues_by_category), 1);

  return (
    <div className="p-4 sm:p-6 space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => setView('home')} className="p-2 hover:bg-gray-100 rounded-full transition">
          <ArrowLeft size={24} className="text-gray-600" />
        </button>
        <h2 className="text-2xl font-bold text-gray-800">City Statistics</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-6 rounded-xl border border-blue-100 flex flex-col items-center shadow-sm">
            <span className="text-blue-600 font-semibold mb-2 uppercase tracking-wider text-sm">Total Issues</span>
            <span className="text-4xl font-extrabold text-blue-800">{stats.total_issues}</span>
        </div>
        <div className="bg-green-50 p-6 rounded-xl border border-green-100 flex flex-col items-center shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-green-600 font-semibold uppercase tracking-wider text-sm">
                <CheckCircle size={16} />
                <span>Resolved</span>
            </div>
            <span className="text-4xl font-extrabold text-green-800">{stats.resolved_issues}</span>
        </div>
        <div className="bg-orange-50 p-6 rounded-xl border border-orange-100 flex flex-col items-center shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-orange-600 font-semibold uppercase tracking-wider text-sm">
                <Clock size={16} />
                <span>Pending</span>
            </div>
            <span className="text-4xl font-extrabold text-orange-800">{stats.pending_issues}</span>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-2 mb-6">
            <PieChart size={20} className="text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-800">Issues by Category</h3>
        </div>

        <div className="space-y-4">
            {Object.entries(stats.issues_by_category).map(([category, count]) => (
                <div key={category}>
                    <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700 capitalize">{category}</span>
                        <span className="text-gray-500">{count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                        <div
                            className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                            style={{ width: `${(count / maxCount) * 100}%` }}
                        ></div>
                    </div>
                </div>
            ))}
             {Object.keys(stats.issues_by_category).length === 0 && (
                <p className="text-center text-gray-400 py-4">No data available yet.</p>
            )}
        </div>
      </div>
    </div>
  );
};

export default StatsView;
