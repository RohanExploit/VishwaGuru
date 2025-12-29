import React, { useState, useEffect } from 'react';
import { getMaharashtraRepContacts } from './api/location';
import PotholeDetector from './PotholeDetector';
import GarbageDetector from './GarbageDetector';
import ChatWidget from './components/ChatWidget';
import { AlertTriangle, MapPin, Search, Activity, Camera, Trash2, ThumbsUp } from 'lucide-react';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

// Home View Component
const Home = ({ setView, fetchResponsibilityMap, recentIssues, handleUpvote }) => (
  <div className="space-y-6">
    {/* Quick Actions Grid */}
    <div className="grid grid-cols-2 gap-4">
      <button
        onClick={() => setView('report')}
        className="flex flex-col items-center justify-center bg-blue-50 border-2 border-blue-100 p-4 rounded-xl hover:bg-blue-100 transition shadow-sm h-32"
      >
        <div className="bg-blue-500 text-white p-3 rounded-full mb-2">
          <AlertTriangle size={24} />
        </div>
        <span className="font-semibold text-blue-800">Report Issue</span>
      </button>

      <button
        onClick={() => setView('pothole')}
        className="flex flex-col items-center justify-center bg-red-50 border-2 border-red-100 p-4 rounded-xl hover:bg-red-100 transition shadow-sm h-32"
      >
        <div className="bg-red-500 text-white p-3 rounded-full mb-2">
          <Camera size={24} />
        </div>
        <span className="font-semibold text-red-800">Detect Pothole</span>
      </button>

      <button
        onClick={() => setView('garbage')}
        className="flex flex-col items-center justify-center bg-orange-50 border-2 border-orange-100 p-4 rounded-xl hover:bg-orange-100 transition shadow-sm h-32"
      >
        <div className="bg-orange-500 text-white p-3 rounded-full mb-2">
          <Trash2 size={24} />
        </div>
        <span className="font-semibold text-orange-800">Detect Garbage</span>
      </button>

      <button
        onClick={() => setView('mh-rep')}
        className="flex flex-col items-center justify-center bg-purple-50 border-2 border-purple-100 p-4 rounded-xl hover:bg-purple-100 transition shadow-sm h-32"
      >
        <div className="bg-purple-500 text-white p-3 rounded-full mb-2">
          <Search size={24} />
        </div>
        <span className="font-semibold text-purple-800">Find MLA</span>
      </button>
    </div>

    <div className="grid grid-cols-1">
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

const MapView = ({ responsibilityMap, setView }) => (
  <div className="mt-6 border-t pt-4">
    <h2 className="text-xl font-semibold mb-4 text-center">Responsibility Map</h2>
    <div className="grid gap-4 sm:grid-cols-2">
      {responsibilityMap && Object.entries(responsibilityMap).map(([key, value]) => (
        <div key={key} className="bg-gray-50 p-4 rounded shadow-sm border">
          <h3 className="font-bold text-lg capitalize mb-2">{key.replace('_', ' ')}</h3>
          <p className="font-medium text-gray-800">{value.authority}</p>
          <p className="text-sm text-gray-600 mt-1">{value.description}</p>
        </div>
      ))}
    </div>
    <button onClick={() => setView('home')} className="mt-6 text-blue-600 underline text-center w-full block">Back to Home</button>
  </div>
);

const ReportForm = ({ setView, setLoading, setError, setActionPlan, loading }) => {
  const [formData, setFormData] = useState({ description: '', category: 'road', image: null });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = new FormData();
    payload.append('description', formData.description);
    payload.append('category', formData.category);
    if (formData.image) {
      payload.append('image', formData.image);
    }

    try {
      const response = await fetch(`${API_URL}/api/issues`, {
        method: 'POST',
        body: payload,
      });

      if (!response.ok) throw new Error('Failed to submit issue');

      const data = await response.json();
      setActionPlan(data.action_plan);
      setView('action');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6">
       <h2 className="text-xl font-semibold mb-4 text-center">Report an Issue</h2>
       <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Category</label>
            <select
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
            >
              <option value="road">Road / Potholes</option>
              <option value="water">Water Supply</option>
              <option value="garbage">Garbage / Sanitation</option>
              <option value="streetlight">Streetlight</option>
              <option value="college_infra">College Infrastructure</option>
              <option value="women_safety">Women Safety</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              rows="3"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Describe the issue..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Photo (Optional)</label>
            <input
              type="file"
              accept="image/*"
              className="mt-1 block w-full text-sm text-gray-500"
              onChange={(e) => setFormData({...formData, image: e.target.files[0]})}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Generate Action Plan'}
          </button>
          <button type="button" onClick={() => setView('home')} className="mt-2 text-blue-600 underline text-center w-full block">Cancel</button>
       </form>
    </div>
  );
};

const ActionView = ({ actionPlan, setView }) => {
  if (!actionPlan) return null;

  return (
    <div className="mt-6 space-y-6">
      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
        <h2 className="text-xl font-bold text-green-800 mb-2">Action Plan Generated!</h2>
        <p className="text-green-700">Here are ready-to-use drafts to send to authorities.</p>
      </div>

      <div className="bg-white p-4 rounded shadow border">
        <h3 className="font-bold text-lg mb-2 flex items-center">
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm mr-2">WhatsApp</span>
        </h3>
        <div className="bg-gray-100 p-3 rounded text-sm mb-3 whitespace-pre-wrap">
          {actionPlan.whatsapp}
        </div>
        <a
          href={`https://wa.me/?text=${encodeURIComponent(actionPlan.whatsapp)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full text-center bg-green-500 text-white py-2 rounded hover:bg-green-600 transition"
        >
          Send on WhatsApp
        </a>
      </div>

      <div className="bg-white p-4 rounded shadow border">
        <h3 className="font-bold text-lg mb-2">Email Draft</h3>
        <div className="mb-2">
          <span className="font-semibold text-gray-700">Subject:</span> {actionPlan.email_subject}
        </div>
        <div className="bg-gray-100 p-3 rounded text-sm mb-3 whitespace-pre-wrap">
          {actionPlan.email_body}
        </div>
        <a
          href={`mailto:?subject=${encodeURIComponent(actionPlan.email_subject)}&body=${encodeURIComponent(actionPlan.email_body)}`}
           className="block w-full text-center bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition"
        >
          Open in Email App
        </a>
      </div>

      <button onClick={() => setView('home')} className="text-blue-600 underline text-center w-full block">Back to Home</button>
    </div>
  );
};

const MaharashtraRepView = ({ setView, setLoading, setError, setMaharashtraRepInfo, maharashtraRepInfo, loading }) => {
  const [pincode, setPincode] = useState('');
  const [localError, setLocalError] = useState(null);

  const handleLookup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLocalError(null);
    setError(null);

    try {
      const data = await getMaharashtraRepContacts(pincode);
      setMaharashtraRepInfo(data);
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-4 text-center">Find Your Maharashtra MLA</h2>

      {!maharashtraRepInfo ? (
        <form onSubmit={handleLookup} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter your 6-digit pincode
            </label>
            <input
              type="text"
              required
              maxLength="6"
              pattern="[0-9]{6}"
              className="block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              value={pincode}
              onChange={(e) => setPincode(e.target.value)}
              placeholder="e.g., 411001"
            />
            <p className="text-xs text-gray-500 mt-1">
              Currently supporting limited pincodes in Maharashtra (MVP)
            </p>
          </div>

          {localError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {localError}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || pincode.length !== 6}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 transition disabled:opacity-50"
          >
            {loading ? 'Looking up...' : 'Find My Representatives'}
          </button>

          <button
            type="button"
            onClick={() => setView('home')}
            className="mt-2 text-blue-600 underline text-center w-full block"
          >
            Cancel
          </button>
        </form>
      ) : (
        <div className="space-y-4">
          {/* Location Info */}
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="font-bold text-purple-800 mb-2">Your Location</h3>
            <div className="text-sm space-y-1">
              <p><span className="font-semibold">Pincode:</span> {maharashtraRepInfo.pincode}</p>
              <p><span className="font-semibold">District:</span> {maharashtraRepInfo.district}</p>
              <p><span className="font-semibold">Constituency:</span> {maharashtraRepInfo.assembly_constituency}</p>
            </div>
          </div>

          {/* MLA Info */}
          <div className="bg-white p-4 rounded shadow border">
            <h3 className="font-bold text-lg mb-3 flex items-center">
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm mr-2">Your MLA</span>
            </h3>
            <div className="space-y-2">
              <p className="text-lg font-semibold text-gray-800">{maharashtraRepInfo.mla.name}</p>
              <p className="text-sm text-gray-600"><span className="font-medium">Party:</span> {maharashtraRepInfo.mla.party}</p>
              <p className="text-sm text-gray-600"><span className="font-medium">Phone:</span> {maharashtraRepInfo.mla.phone}</p>
              <p className="text-sm text-gray-600"><span className="font-medium">Email:</span> {maharashtraRepInfo.mla.email}</p>
            </div>

            {maharashtraRepInfo.mla.twitter && maharashtraRepInfo.mla.twitter !== "Not Available" && (
              <div className="mt-3">
                <a
                  href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(
                    `Hello ${maharashtraRepInfo.mla.twitter}, I am a resident of ${maharashtraRepInfo.assembly_constituency} (Pincode: ${maharashtraRepInfo.pincode}). I want to bring to your attention... @PMOIndia @CMOMaharashtra`
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center bg-black text-white py-2 rounded hover:bg-gray-800 transition flex items-center justify-center gap-2"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5 fill-current"><g><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></g></svg>
                  Post on X
                </a>
              </div>
            )}

            {maharashtraRepInfo.description && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm text-gray-700 italic">{maharashtraRepInfo.description}</p>
              </div>
            )}
          </div>

          {/* Grievance Links */}
          <div className="bg-green-50 p-4 rounded shadow border border-green-200">
            <h3 className="font-bold text-lg mb-3 text-green-800">File a Grievance</h3>
            <div className="space-y-2">
              <a
                href={maharashtraRepInfo.grievance_links.central_cpgrams}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
              >
                Central CPGRAMS Portal
              </a>
              <a
                href={maharashtraRepInfo.grievance_links.maharashtra_portal}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center bg-orange-600 text-white py-2 rounded hover:bg-orange-700 transition"
              >
                Maharashtra Aaple Sarkar Portal
              </a>
            </div>
            <p className="text-xs text-gray-600 mt-3 text-center">
              {maharashtraRepInfo.grievance_links.note}
            </p>
          </div>

          <button
            onClick={() => {
              setMaharashtraRepInfo(null);
              setPincode('');
              setView('home');
            }}
            className="text-blue-600 underline text-center w-full block"
          >
            Back to Home
          </button>
        </div>
      )}
    </div>
  );
};

function App() {
  const [view, setView] = useState('home'); // home, map, report, action, mh-rep, pothole, garbage
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [maharashtraRepInfo, setMaharashtraRepInfo] = useState(null);
  const [recentIssues, setRecentIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch recent issues on mount
  const fetchRecentIssues = async () => {
    try {
      const response = await fetch(`${API_URL}/api/issues/recent`);
      if (response.ok) {
        const data = await response.json();
        setRecentIssues(data);
      }
    } catch (e) {
      console.error("Failed to fetch recent issues", e);
    }
  };

  useEffect(() => {
    fetchRecentIssues();
  }, []);

  const handleUpvote = async (id) => {
    try {
        const response = await fetch(`${API_URL}/api/issues/${id}/vote`, {
            method: 'POST'
        });
        if (response.ok) {
            // Update local state to reflect change immediately (optimistic UI or re-fetch)
            setRecentIssues(prev => prev.map(issue =>
                issue.id === id ? { ...issue, upvotes: (issue.upvotes || 0) + 1 } : issue
            ));
        }
    } catch (e) {
        console.error("Failed to upvote", e);
    }
  };

  // Responsibility Map Logic
  const fetchResponsibilityMap = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/responsibility-map`);
      if (!response.ok) throw new Error('Failed to fetch data');
      const data = await response.json();
      setResponsibilityMap(data);
      setView('map');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <ChatWidget />
      <div className="bg-white shadow-xl rounded-2xl p-6 max-w-lg w-full mt-6 mb-24 border border-gray-100">
        <header className="text-center mb-6">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-blue-600">
            VishwaGuru
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Empowering Citizens, Solving Problems.
          </p>
        </header>

        {loading && !['report', 'mh-rep'].includes(view) && (
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center my-4">
            {error}
          </div>
        )}

        {view === 'home' && (
          <Home
            setView={setView}
            fetchResponsibilityMap={fetchResponsibilityMap}
            recentIssues={recentIssues}
            handleUpvote={handleUpvote}
          />
        )}
        {view === 'map' && (
          <MapView
            responsibilityMap={responsibilityMap}
            setView={setView}
          />
        )}
        {view === 'report' && (
          <ReportForm
            setView={setView}
            setLoading={setLoading}
            setError={setError}
            setActionPlan={setActionPlan}
            loading={loading}
          />
        )}
        {view === 'action' && (
          <ActionView
            actionPlan={actionPlan}
            setView={setView}
          />
        )}
        {view === 'mh-rep' && (
          <MaharashtraRepView
            setView={setView}
            setLoading={setLoading}
            setError={setError}
            setMaharashtraRepInfo={setMaharashtraRepInfo}
            maharashtraRepInfo={maharashtraRepInfo}
            loading={loading}
          />
        )}
        {view === 'pothole' && <PotholeDetector onBack={() => setView('home')} />}
        {view === 'garbage' && <GarbageDetector onBack={() => setView('home')} />}

      </div>
    </div>
  );
}

export default App;
