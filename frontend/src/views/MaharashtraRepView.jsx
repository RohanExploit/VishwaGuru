import React, { useState } from 'react';
import { getMaharashtraRepContacts } from '../api/location';

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

export default MaharashtraRepView;
