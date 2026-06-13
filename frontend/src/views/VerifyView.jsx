import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Camera, Upload, CheckCircle, XCircle, AlertTriangle, ArrowLeft, ShieldCheck } from 'lucide-react';
import { issuesApi } from '../api/issues';

const API_URL = import.meta.env.VITE_API_URL || '';

const VerifyView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [issue, setIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [blockchainLoading, setBlockchainLoading] = useState(false);
  const [blockchainResult, setBlockchainResult] = useState(null);

  useEffect(() => {
    const fetchIssue = async () => {
      try {
        // Optimization: Fetch issue by ID directly (O(1)) instead of searching recent list (O(N))
        const data = await issuesApi.getById(id);
        if (data) {
          setIssue(data);
        } else {
          setError("Issue not found.");
        }
      } catch (err) {
        console.error("Load failed", err);
        setError("Failed to load issue details.");
      } finally {
        setLoading(false);
      }
    };
    fetchIssue();
  }, [id]);

  const handleVerifyBlockchain = async () => {
    setVerifyingBlockchain(true);
    try {
      const data = await issuesApi.verifyBlockchain(id);
      setBlockchainResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to verify blockchain integrity.");
    } finally {
      setVerifyingBlockchain(false);
    }
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
      setResult(null); // Reset result on new image
    }
  };

  const handleBlockchainVerify = async () => {
    setBlockchainLoading(true);
    setBlockchainResult(null);
    try {
      const data = await issuesApi.verifyBlockchain(id);
      setBlockchainResult(data);
    } catch (err) {
      console.error("Blockchain verification failed", err);
      setBlockchainResult({
        is_valid: false,
        message: "Failed to connect to the blockchain verification service."
      });
    } finally {
      setBlockchainLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!image) return;
    setVerifying(true);

    const formData = new FormData();
    formData.append('image', image);

    try {
      const response = await fetch(`${API_URL}/api/issues/${id}/verify`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error("Verification failed");

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to verify resolution.");
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (error && !issue) return <div className="p-8 text-center text-red-600">{error}</div>;

  return (
    <div className="p-4 max-w-lg mx-auto">
      <button onClick={() => navigate(-1)} className="flex items-center text-gray-600 mb-4">
        <ArrowLeft size={20} className="mr-1" /> Back
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h1 className="text-2xl font-bold mb-2">Verify Resolution</h1>
        <div className="mb-4">
            <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-semibold uppercase">
                {issue.category}
            </span>
        </div>
        <p className="text-gray-700 mb-4">{issue.description}</p>

        <div className="border-t pt-4">
            <h3 className="font-semibold mb-3">Upload Proof of Fix</h3>

            <div className="flex gap-3 mb-4">
                <label className="flex-1 cursor-pointer bg-blue-50 text-blue-700 p-4 rounded-lg flex flex-col items-center justify-center border border-blue-200 hover:bg-blue-100 transition">
                    <Camera size={24} className="mb-2" />
                    <span className="font-medium">Camera</span>
                    <input type="file" accept="image/*" capture="environment" className="hidden" onChange={handleImageChange} />
                </label>
                <label className="flex-1 cursor-pointer bg-gray-50 text-gray-700 p-4 rounded-lg flex flex-col items-center justify-center border border-gray-200 hover:bg-gray-100 transition">
                    <Upload size={24} className="mb-2" />
                    <span className="font-medium">Upload</span>
                    <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
                </label>
            </div>

            {image && (
                <div className="mb-4 text-center">
                    <p className="text-sm text-green-600 font-medium mb-2">Selected: {image.name}</p>
                    <button
                        onClick={handleVerify}
                        disabled={verifying}
                        className="w-full bg-green-600 text-white py-3 rounded-lg font-bold shadow hover:bg-green-700 transition disabled:opacity-50"
                    >
                        {verifying ? 'Verifying with AI...' : 'Verify Resolution'}
                    </button>
                </div>
            )}

            {result && (
                <div className={`mt-6 p-4 rounded-lg border ${result.is_resolved ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center gap-3 mb-2">
                        {result.is_resolved ? (
                            <CheckCircle size={28} className="text-green-600" />
                        ) : (
                            <XCircle size={28} className="text-red-600" />
                        )}
                        <div>
                            <h3 className={`font-bold text-lg ${result.is_resolved ? 'text-green-800' : 'text-red-800'}`}>
                                {result.is_resolved ? 'Verified Resolved' : 'Not Resolved'}
                            </h3>
                            <p className="text-sm opacity-80">AI Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                        </div>
                    </div>
                    <p className="text-sm mt-2">
                        <strong>AI Analysis:</strong> The system analyzed the image asking "{result.question_asked}" and the answer was "{result.ai_answer}".
                    </p>
                    {result.is_resolved && (
                        <p className="text-sm mt-2 text-green-700 font-medium">
                            The issue status has been updated to "Verified".
                        </p>
                    )}
                </div>
            )}
        </div>
      </div>

      {/* Blockchain Integrity Seal Section */}
      <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl shadow-sm border border-indigo-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <ShieldCheck className="text-indigo-600" size={28} />
          <h2 className="text-xl font-bold text-indigo-900">Blockchain Integrity Seal</h2>
        </div>

        <p className="text-indigo-800 text-sm mb-4">
          Every report in our system is cryptographically sealed and linked to the previous report, creating an immutable chain of records. Verify that this report hasn't been tampered with.
        </p>

        <button
          onClick={handleBlockchainVerify}
          disabled={blockchainLoading}
          className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
        >
          {blockchainLoading ? 'Verifying Integrity Hash...' : 'Verify Cryptographic Seal'}
        </button>

        {blockchainResult && (
          <div className={`mt-4 p-3 rounded border text-sm ${blockchainResult.is_valid ? 'bg-white border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
            <div className="flex items-start gap-2">
              {blockchainResult.is_valid ? (
                <CheckCircle size={18} className="text-green-600 mt-0.5" />
              ) : (
                <XCircle size={18} className="text-red-600 mt-0.5" />
              )}
              <div>
                <p className="font-bold">{blockchainResult.is_valid ? 'Integrity Verified' : 'Integrity Compromised'}</p>
                <p className="opacity-90">{blockchainResult.message}</p>
                {blockchainResult.current_hash && (
                  <div className="mt-2 pt-2 border-t border-gray-100 font-mono text-[10px] break-all">
                    <p className="font-semibold text-gray-500 mb-1 uppercase tracking-tighter">Current Hash:</p>
                    {blockchainResult.current_hash}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyView;
