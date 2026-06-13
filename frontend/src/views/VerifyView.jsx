import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Camera, Upload, CheckCircle, XCircle, AlertTriangle, ArrowLeft, ShieldCheck, ShieldAlert, Link as LinkIcon } from 'lucide-react';
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
  const [blockchainResult, setBlockchainResult] = useState(null);
  const [verifyingBlockchain, setVerifyingBlockchain] = useState(false);

  useEffect(() => {
    const fetchIssue = async () => {
      try {
        // Optimized O(1) fetch instead of O(N) filtering
        const data = await issuesApi.getById(id);
        setIssue(data);
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
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="text-blue-600" size={24} />
            <h2 className="text-xl font-bold">Blockchain Integrity Seal</h2>
          </div>
          {!blockchainResult && (
            <button
              onClick={handleVerifyBlockchain}
              disabled={verifyingBlockchain}
              className="text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-semibold hover:bg-blue-100 transition disabled:opacity-50"
            >
              {verifyingBlockchain ? 'Verifying...' : 'Verify Seal'}
            </button>
          )}
        </div>

        {blockchainResult ? (
          <div className={`p-4 rounded-lg ${blockchainResult.is_valid ? 'bg-blue-50 border border-blue-100' : 'bg-orange-50 border border-orange-100'}`}>
            <div className="flex gap-3">
              {blockchainResult.is_valid ? (
                <ShieldCheck size={24} className="text-blue-600 shrink-0" />
              ) : (
                <ShieldAlert size={24} className="text-orange-600 shrink-0" />
              )}
              <div>
                <p className={`font-bold ${blockchainResult.is_valid ? 'text-blue-900' : 'text-orange-900'}`}>
                  {blockchainResult.is_valid ? 'Integrity Verified' : 'Integrity Compromised'}
                </p>
                <p className="text-sm text-gray-600 mb-3">{blockchainResult.message}</p>

                <div className="space-y-2">
                  <div className="bg-white/50 p-2 rounded text-xs font-mono break-all">
                    <span className="text-gray-500 block mb-1 uppercase tracking-wider text-[10px] font-bold">Current Hash</span>
                    {blockchainResult.current_hash}
                  </div>

                  {blockchainResult.is_valid && (
                    <div className="flex items-center gap-2 text-xs text-blue-700 font-medium mt-2">
                      <LinkIcon size={14} />
                      Linked to previous report hash
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">
            Cryptographically verify that this report hasn't been tampered with since creation.
          </p>
        )}
      </div>
    </div>
  );
};

export default VerifyView;
