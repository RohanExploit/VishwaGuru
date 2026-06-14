import React, { useState, useEffect } from 'react';
import { miscApi } from '../api';
import { Trophy, Medal, User, ArrowLeft, Star, Shield } from 'lucide-react';

const LeaderboardView = ({ setView }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const data = await miscApi.getLeaderboard();
        if (data && data.leaderboard) {
            setLeaderboard(data.leaderboard);
        }
      } catch (e) {
        console.error("Failed to fetch leaderboard", e);
      } finally {
        setLoading(false);
      }
    };
    fetchLeaderboard();
  }, []);

  const getRankIcon = (rank) => {
    if (rank === 1) return <Trophy className="text-yellow-500" size={24} />;
    if (rank === 2) return <Medal className="text-gray-400" size={24} />;
    if (rank === 3) return <Medal className="text-amber-600" size={24} />;
    return <span className="font-bold text-gray-500 w-6 text-center">{rank}</span>;
  };

  return (
    <div className="h-full flex flex-col">
       <button onClick={() => setView('home')} className="self-start text-blue-600 mb-4 flex items-center gap-1 hover:underline">
          <ArrowLeft size={16} /> Back to Home
       </button>

       <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center justify-center gap-2">
             <Trophy className="text-yellow-500" />
             Top Citizens
          </h2>
          <p className="text-gray-500 text-sm">Recognizing our most active community members</p>
       </div>

       {loading ? (
         <div className="flex justify-center my-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
         </div>
       ) : (
         <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="grid grid-cols-12 bg-gray-50 p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
               <div className="col-span-2 text-center">Rank</div>
               <div className="col-span-6">User</div>
               <div className="col-span-2 text-center">Reports</div>
               <div className="col-span-2 text-center">Upvotes</div>
            </div>
            <div className="divide-y divide-gray-50">
               {leaderboard.length > 0 ? (
                 leaderboard.map((entry) => (
                   <div key={entry.rank} className="grid grid-cols-12 p-4 items-center hover:bg-gray-50 transition">
                      <div className="col-span-2 flex justify-center">
                         {getRankIcon(entry.rank)}
                      </div>
                      <div className="col-span-6 flex items-center gap-2">
                         <div className="bg-blue-100 p-1.5 rounded-full text-blue-600">
                             <User size={16} />
                         </div>
                         <div className="flex flex-col">
                             <span className="font-medium text-gray-800 text-sm">{entry.user_email}</span>
                             {entry.reports_count > 5 && (
                                 <span className="flex items-center gap-1 text-[10px] font-bold text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded-full border border-purple-100 w-fit">
                                     <Shield size={10} fill="currentColor" />
                                     Civic Hero
                                 </span>
                             )}
                         </div>
                      </div>
                      <div className="col-span-2 text-center font-semibold text-gray-700">
                         {entry.reports_count}
                      </div>
                      <div className="col-span-2 text-center flex items-center justify-center gap-1 text-orange-600 font-medium">
                         <Star size={12} fill="currentColor" />
                         {entry.total_upvotes}
                      </div>
                   </div>
                 ))
               ) : (
                 <div className="p-8 text-center text-gray-400 text-sm">
                    No data available yet. Be the first to report!
                 </div>
               )}
            </div>
         </div>
       )}
    </div>
  );
};

export default LeaderboardView;
