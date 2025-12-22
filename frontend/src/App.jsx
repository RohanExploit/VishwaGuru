import React, { useState, Suspense } from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import jwt_decode from "jwt-decode";

// NOTE: Replace with your actual Client ID
const GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";

function App() {
  const [view, setView] = useState('home'); // home, map, report, action
  const [responsibilityMap, setResponsibilityMap] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  const handleLoginSuccess = (credentialResponse) => {
    // In a real app, verify this token with your backend
    const decoded = jwt_decode(credentialResponse.credential);
    setUser(decoded);
    console.log("Logged in user:", decoded);
  };

  const handleLoginError = () => {
    console.log('Login Failed');
  };

  // Home View Components
  const Home = () => (
    <div className="space-y-4">
      {!user && (
         <div className="flex justify-center mb-4">
             <GoogleLogin
                onSuccess={handleLoginSuccess}
                onError={handleLoginError}
              />
         </div>
      )}
      {user && (
          <p className="text-center text-green-600 font-semibold mb-4">Welcome, {user.name}!</p>
      )}

      <button
        onClick={() => setView('report')}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition font-medium shadow-md"
      >
        Start an Issue
      </button>
      <button
        onClick={fetchResponsibilityMap}
        className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition font-medium shadow-md"
      >
        Who is Responsible?
      </button>
    </div>
  );

  // Responsibility Map Logic
  const fetchResponsibilityMap = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/responsibility-map');
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

  const MapView = () => (
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

  // Report Issue Logic
  const ReportForm = () => {
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

      // Pass user email if logged in (Optional)
      if (user) {
        payload.append('user_email', user.email);
      }

      try {
        const response = await fetch('/api/issues', {
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

  // Action Plan View
  const ActionView = () => {
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

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <div className="bg-white shadow-lg rounded-lg p-6 max-w-lg w-full mt-10">
        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">
          VishwaGuru
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Civic action, simplified.
        </p>

        {loading && view !== 'report' && <p className="text-center text-gray-500 my-4">Loading...</p>}
        {error && <p className="text-center text-red-500 my-4">{error}</p>}

        {view === 'home' && <Home />}
        {view === 'map' && <MapView />}
        {view === 'report' && <ReportForm />}
        {view === 'action' && <ActionView />}

      </div>
    </div>
    </GoogleOAuthProvider>
  );
}

export default App;
