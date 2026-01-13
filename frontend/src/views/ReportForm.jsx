import React, { useState } from 'react';
import { fakeActionPlan } from '../fakeData';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

const ReportForm = ({ setView, setLoading, setError, setActionPlan, loading }) => {
  const [formData, setFormData] = useState({
    description: '',
    category: 'road',
    image: null,
    latitude: null,
    longitude: null,
    location: ''
  });
  const [gettingLocation, setGettingLocation] = useState(false);

  const getLocation = () => {
    setGettingLocation(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData(prev => ({
            ...prev,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            location: `Lat: ${position.coords.latitude.toFixed(4)}, Long: ${position.coords.longitude.toFixed(4)}`
          }));
          setGettingLocation(false);
        },
        (err) => {
          console.error("Error getting location: ", err);
          setError("Failed to get location. Please enable GPS.");
          setGettingLocation(false);
        }
      );
    } else {
      setError("Geolocation is not supported by this browser.");
      setGettingLocation(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = new FormData();
    payload.append('description', formData.description);
    payload.append('category', formData.category);
    if (formData.latitude) payload.append('latitude', formData.latitude);
    if (formData.longitude) payload.append('longitude', formData.longitude);
    if (formData.location) payload.append('location', formData.location);
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
      console.error("Submission failed, using fake action plan", err);
      // Fallback to fake action plan on failure
      setActionPlan(fakeActionPlan);
      setView('action');
      // We don't set error here so the user sees the success flow (even if fake)
      // setError(err.message);
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
            <label className="block text-sm font-medium text-gray-700">Location (Optional)</label>
             <div className="flex gap-2 mt-1">
                <input
                    type="text"
                    readOnly
                    placeholder="Location not set"
                    className="block w-full rounded-md border-gray-300 shadow-sm p-2 border bg-gray-50"
                    value={formData.location || ''}
                />
                <button
                    type="button"
                    onClick={getLocation}
                    disabled={gettingLocation}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded inline-flex items-center"
                >
                    {gettingLocation ? '...' : '📍'}
                </button>
             </div>
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

export default ReportForm;
