import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, MapPin, ThumbsUp, ChevronLeft, Loader2, AlertTriangle } from 'lucide-react';

// Get API URL from environment variable
const API_URL = import.meta.env.VITE_API_URL || '';

const MyReportsView = () => {
  const navigate = useNavigate();
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [email, setEmail] = useState(localStorage.getItem('user_email') || '');

  const fetchIssues = async (userEmail) => {
    if (!userEmail) return;
    setLoading(true);
    setError(null);
    try {
        const response = await fetch(`${API_URL}/api/issues/user?user_email=${encodeURIComponent(userEmail)}&limit=50`);
        if (!response.ok) throw new Error('Failed to fetch issues');
        const data = await response.json();
        setIssues(data);
    } catch (err) {
        console.error("Error fetching my issues", err);
        setError("Failed to load your reports. Please try again.");
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    if (localStorage.getItem('user_email')) {
        fetchIssues(localStorage.getItem('user_email'));
    }
  }, []);

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    if (email) {
        localStorage.setItem('user_email', email);
        fetchIssues(email);
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto min-h-screen">
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => navigate('/')} className="p-2 hover:bg-gray-100 rounded-full">
            <ChevronLeft size={24} />
        </button>
        <h1 className="text-xl font-bold">My Reports</h1>
      </div>

      {!localStorage.getItem('user_email') && !issues.length ? (
         <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
            <h2 className="text-lg font-bold mb-2">Track Your Impact</h2>
            <p className="text-gray-500 mb-4">Enter your email to see the issues you've reported.</p>
            <form onSubmit={handleEmailSubmit} className="flex gap-2">
                <input
                    type="email"
                    required
                    className="flex-1 border rounded-lg px-3 py-2"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold">
                    View
                </button>
            </form>
         </div>
      ) : (
        <div className="space-y-4">
            <div className="flex justify-between items-center px-2">
                 <span className="text-sm text-gray-500">Showing reports for <b>{email}</b></span>
                 <button onClick={() => { localStorage.removeItem('user_email'); setEmail(''); setIssues([]); }} className="text-xs text-red-500 hover:underline">Change Email</button>
            </div>

            {loading && (
                <div className="flex justify-center py-8">
                    <Loader2 className="animate-spin text-blue-600" size={32} />
                </div>
            )}

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertTriangle size={20} />
                    {error}
                </div>
            )}

            {!loading && !error && issues.length === 0 && (
                <div className="text-center py-12 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    <Activity size={48} className="mx-auto mb-2 opacity-20" />
                    <p>No reports found for this email.</p>
                    <button onClick={() => navigate('/report')} className="mt-4 text-blue-600 font-bold hover:underline">Report your first issue</button>
                </div>
            )}

            <div className="space-y-3">
                {issues.map(issue => (
                    <div key={issue.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:border-blue-200 transition cursor-pointer" onClick={() => navigate(`/verify/${issue.id}`)}>
                         <div className="flex justify-between items-start mb-2">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${
                                issue.status === 'resolved' ? 'bg-green-100 text-green-700' :
                                issue.status === 'verified' ? 'bg-blue-100 text-blue-700' :
                                'bg-gray-100 text-gray-600'
                            }`}>
                                {issue.status}
                            </span>
                            <span className="text-xs text-gray-400">{new Date(issue.created_at).toLocaleDateString()}</span>
                         </div>
                         <h3 className="font-medium text-gray-800 line-clamp-2 mb-2">{issue.description}</h3>
                         <div className="flex justify-between items-center text-xs text-gray-500">
                             <div className="flex items-center gap-1">
                                <MapPin size={12} />
                                <span className="truncate max-w-[150px]">{issue.location || 'Unknown Location'}</span>
                             </div>
                             <div className="flex items-center gap-3">
                                 <span className="flex items-center gap-1"><ThumbsUp size={12}/> {issue.upvotes}</span>
                                 <span className="text-blue-600 font-bold hover:underline">View Status &rarr;</span>
                             </div>
                         </div>
                    </div>
                ))}
            </div>
        </div>
      )}
    </div>
  );
};

export default MyReportsView;
