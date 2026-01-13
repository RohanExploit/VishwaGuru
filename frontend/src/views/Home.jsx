import React from 'react';
import { AlertTriangle, MapPin, Search, Activity, Camera, Trash2, ThumbsUp, Brush, Droplets, Zap, Truck, Flame, Dog, XCircle, Lightbulb, TreeDeciduous, Bug } from 'lucide-react';

const Home = ({ setView, fetchResponsibilityMap, recentIssues, handleUpvote }) => (
  <div className="space-y-6">
    {/* Quick Actions Grid */}
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
      <button
        onClick={() => setView('report')}
        className="flex flex-col items-center justify-center bg-blue-50 border-2 border-blue-100 p-4 rounded-xl hover:bg-blue-100 transition shadow-sm h-32"
      >
        <div className="bg-blue-500 text-white p-3 rounded-full mb-2">
          <AlertTriangle size={24} />
        </div>
        <span className="font-semibold text-blue-800 text-sm">Report Issue</span>
      </button>

      <button
        onClick={() => setView('pothole')}
        className="flex flex-col items-center justify-center bg-red-50 border-2 border-red-100 p-4 rounded-xl hover:bg-red-100 transition shadow-sm h-32"
      >
        <div className="bg-red-500 text-white p-3 rounded-full mb-2">
          <Camera size={24} />
        </div>
        <span className="font-semibold text-red-800 text-sm">Pothole</span>
      </button>

      <button
        onClick={() => setView('garbage')}
        className="flex flex-col items-center justify-center bg-orange-50 border-2 border-orange-100 p-4 rounded-xl hover:bg-orange-100 transition shadow-sm h-32"
      >
        <div className="bg-orange-500 text-white p-3 rounded-full mb-2">
          <Trash2 size={24} />
        </div>
        <span className="font-semibold text-orange-800 text-sm">Garbage</span>
      </button>

      <button
        onClick={() => setView('mh-rep')}
        className="flex flex-col items-center justify-center bg-purple-50 border-2 border-purple-100 p-4 rounded-xl hover:bg-purple-100 transition shadow-sm h-32"
      >
        <div className="bg-purple-500 text-white p-3 rounded-full mb-2">
          <Search size={24} />
        </div>
        <span className="font-semibold text-purple-800 text-sm">Find MLA</span>
      </button>

      <button
        onClick={() => setView('vandalism')}
        className="flex flex-col items-center justify-center bg-indigo-50 border-2 border-indigo-100 p-4 rounded-xl hover:bg-indigo-100 transition shadow-sm h-32"
      >
        <div className="bg-indigo-500 text-white p-3 rounded-full mb-2">
          <Brush size={24} />
        </div>
        <span className="font-semibold text-indigo-800 text-sm">Graffiti</span>
      </button>

      <button
        onClick={() => setView('flood')}
        className="flex flex-col items-center justify-center bg-cyan-50 border-2 border-cyan-100 p-4 rounded-xl hover:bg-cyan-100 transition shadow-sm h-32"
      >
        <div className="bg-cyan-500 text-white p-3 rounded-full mb-2">
          <Droplets size={24} />
        </div>
        <span className="font-semibold text-cyan-800 text-sm">Flood</span>
      </button>

      <button
        onClick={() => setView('infrastructure')}
        className="flex flex-col items-center justify-center bg-yellow-50 border-2 border-yellow-100 p-4 rounded-xl hover:bg-yellow-100 transition shadow-sm h-32"
      >
        <div className="bg-yellow-500 text-white p-3 rounded-full mb-2">
          <Zap size={24} />
        </div>
        <span className="font-semibold text-yellow-800 text-sm">Broken Infra</span>
      </button>

      {/* New Western Style Features */}
      <button
        onClick={() => setView('parking')}
        className="flex flex-col items-center justify-center bg-rose-50 border-2 border-rose-100 p-4 rounded-xl hover:bg-rose-100 transition shadow-sm h-32"
      >
        <div className="bg-rose-500 text-white p-3 rounded-full mb-2">
          <Truck size={24} />
        </div>
        <span className="font-semibold text-rose-800 text-sm">Illegal Parking</span>
      </button>

      <button
        onClick={() => setView('streetlight')}
        className="flex flex-col items-center justify-center bg-slate-50 border-2 border-slate-100 p-4 rounded-xl hover:bg-slate-100 transition shadow-sm h-32"
      >
        <div className="bg-slate-700 text-white p-3 rounded-full mb-2">
          <Lightbulb size={24} />
        </div>
        <span className="font-semibold text-slate-800 text-sm">Dark Street</span>
      </button>

      <button
        onClick={() => setView('fire')}
        className="flex flex-col items-center justify-center bg-red-100 border-2 border-red-200 p-4 rounded-xl hover:bg-red-200 transition shadow-sm h-32"
      >
        <div className="bg-red-600 text-white p-3 rounded-full mb-2">
          <Flame size={24} />
        </div>
        <span className="font-semibold text-red-900 text-sm">Fire/Smoke</span>
      </button>

      <button
        onClick={() => setView('animal')}
        className="flex flex-col items-center justify-center bg-amber-50 border-2 border-amber-100 p-4 rounded-xl hover:bg-amber-100 transition shadow-sm h-32"
      >
        <div className="bg-amber-600 text-white p-3 rounded-full mb-2">
          <Dog size={24} />
        </div>
        <span className="font-semibold text-amber-900 text-sm">Stray Animal</span>
      </button>

      <button
        onClick={() => setView('blocked')}
        className="flex flex-col items-center justify-center bg-gray-50 border-2 border-gray-100 p-4 rounded-xl hover:bg-gray-100 transition shadow-sm h-32"
      >
        <div className="bg-gray-600 text-white p-3 rounded-full mb-2">
          <XCircle size={24} />
        </div>
        <span className="font-semibold text-gray-800 text-sm">Blocked Road</span>
      </button>

      <button
        onClick={() => setView('tree')}
        className="flex flex-col items-center justify-center bg-green-50 border-2 border-green-100 p-4 rounded-xl hover:bg-green-100 transition shadow-sm h-32"
      >
        <div className="bg-green-600 text-white p-3 rounded-full mb-2">
          <TreeDeciduous size={24} />
        </div>
        <span className="font-semibold text-green-800 text-sm">Tree Hazard</span>
      </button>

      <button
        onClick={() => setView('pest')}
        className="flex flex-col items-center justify-center bg-amber-50 border-2 border-amber-100 p-4 rounded-xl hover:bg-amber-100 transition shadow-sm h-32"
      >
        <div className="bg-amber-800 text-white p-3 rounded-full mb-2">
          <Bug size={24} />
        </div>
        <span className="font-semibold text-amber-900 text-sm">Pest Control</span>
      </button>
    </div>

    <div className="grid grid-cols-1 mt-4">
       <button
        onClick={fetchResponsibilityMap}
        className="flex flex-row items-center justify-center bg-green-50 border-2 border-green-100 p-4 rounded-xl hover:bg-green-100 transition shadow-sm h-16"
      >
        <div className="bg-green-500 text-white p-2 rounded-full mr-3">
          <MapPin size={20} />
        </div>
        <span className="font-semibold text-green-800">Who is Responsible?</span>
      </button>
    </div>

    {/* Recent Activity Feed */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center gap-2">
        <Activity size={18} className="text-orange-500" />
        <h2 className="font-bold text-gray-800">Community Activity</h2>
      </div>
      <div className="divide-y divide-gray-50 max-h-60 overflow-y-auto">
        {recentIssues.length > 0 ? (
          recentIssues.map((issue) => (
            <div key={issue.id} className="p-3 hover:bg-gray-50 transition">
              <div className="flex justify-between items-start">
                <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 mb-1 capitalize">
                  {issue.category}
                </span>
                <div className="flex items-center gap-2">
                  <button
                      onClick={() => handleUpvote(issue.id)}
                      className="flex items-center gap-1 text-gray-500 hover:text-blue-600 text-xs"
                  >
                      <ThumbsUp size={12} />
                      <span>{issue.upvotes || 0}</span>
                  </button>
                  <span className="text-xs text-gray-400">
                      {new Date(issue.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-700 line-clamp-2">{issue.description}</p>
            </div>
          ))
        ) : (
          <div className="p-4 text-center text-gray-500 text-sm">
            No recent activity to show.
          </div>
        )}
      </div>
    </div>
  </div>
);

export default Home;
