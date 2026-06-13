import React, { useState, useRef, useCallback, useEffect } from 'react';
import { resolutionProofApi } from '../api/resolutionProof';

/**
 * ResolutionProofCapture - Authority-facing component for capturing
 * geo-temporally bound resolution evidence.
 *
 * Features:
 * - GPS permission enforcement
 * - Camera-only capture (no gallery uploads)
 * - Client-side SHA-256 hashing of media
 * - Real-time geofence validation feedback
 * - Token lifecycle management
 */
const ResolutionProofCapture = ({ grievanceId, authorityEmail, onEvidenceSubmitted }) => {
    const [step, setStep] = useState('idle'); // idle | token | capture | submitting | done | error
    const [token, setToken] = useState(null);
    const [gpsPosition, setGpsPosition] = useState(null);
    const [gpsError, setGpsError] = useState(null);
    const [capturedFile, setCapturedFile] = useState(null);
    const [evidenceHash, setEvidenceHash] = useState(null);
    const [geofenceStatus, setGeofenceStatus] = useState(null);
    const [error, setError] = useState(null);
    const [timeLeft, setTimeLeft] = useState(null);
    const fileInputRef = useRef(null);
    const watchIdRef = useRef(null);

    // Request GPS permission and start watching
    const startGpsWatch = useCallback(() => {
        if (!navigator.geolocation) {
            setGpsError('Geolocation is not supported by this browser');
            return;
        }

        setGpsError(null);

        watchIdRef.current = navigator.geolocation.watchPosition(
            (position) => {
                setGpsPosition({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                });
                setGpsError(null);
            },
            (err) => {
                setGpsError(`GPS Error: ${err.message}. Please enable location services.`);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
        );
    }, []);

    // Cleanup GPS watch on unmount
    useEffect(() => {
        return () => {
            if (watchIdRef.current !== null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
            }
        };
    }, []);

    // Token countdown timer
    useEffect(() => {
        if (!token) return;

        const interval = setInterval(() => {
            const now = new Date();
            const expiry = new Date(token.valid_until);
            const diff = Math.max(0, Math.floor((expiry - now) / 1000));
            setTimeLeft(diff);

            if (diff <= 0) {
                setError('Token expired. Please generate a new token.');
                setStep('idle');
                setToken(null);
                clearInterval(interval);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [token]);

    // Check geofence distance
    useEffect(() => {
        if (!token || !gpsPosition) return;

        const R = 6371000; // Earth radius in meters
        const lat1 = (token.geofence_latitude * Math.PI) / 180;
        const lat2 = (gpsPosition.latitude * Math.PI) / 180;
        const dLat = ((gpsPosition.latitude - token.geofence_latitude) * Math.PI) / 180;
        const dLon = ((gpsPosition.longitude - token.geofence_longitude) * Math.PI) / 180;

        const a =
            Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
        const c = 2 * Math.asin(Math.sqrt(a));
        const distance = R * c;

        setGeofenceStatus({
            distance: Math.round(distance),
            isInside: distance <= token.geofence_radius_meters,
            radius: token.geofence_radius_meters,
        });
    }, [token, gpsPosition]);

    // SHA-256 hash of file
    const computeHash = async (file) => {
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
    };

    // Generate device fingerprint hash
    const getDeviceFingerprint = async () => {
        const raw = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset().toString(),
        ].join('|');
        const encoder = new TextEncoder();
        const data = encoder.encode(raw);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
    };

    // Step 1: Generate Token
    const handleGenerateToken = async () => {
        setError(null);
        setStep('token');
        startGpsWatch();

        try {
            const tokenData = await resolutionProofApi.generateToken(
                grievanceId,
                authorityEmail
            );
            setToken(tokenData);
            setStep('capture');
        } catch (err) {
            setError(err.message);
            setStep('error');
        }
    };

    // Step 2: Capture evidence (camera only)
    const handleCapture = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setCapturedFile(file);
        const hash = await computeHash(file);
        setEvidenceHash(hash);
    };

    // Step 3: Submit evidence
    const handleSubmit = async () => {
        if (!token || !evidenceHash || !gpsPosition) return;

        if (geofenceStatus && !geofenceStatus.isInside) {
            setError(
                `You are ${geofenceStatus.distance}m from the grievance location. ` +
                `Please move within ${geofenceStatus.radius}m to submit evidence.`
            );
            return;
        }

        setStep('submitting');
        setError(null);

        try {
            const deviceFingerprint = await getDeviceFingerprint();

            await resolutionProofApi.submitEvidence({
                tokenId: token.token_id,
                evidenceHash,
                gpsLatitude: gpsPosition.latitude,
                gpsLongitude: gpsPosition.longitude,
                captureTimestamp: new Date().toISOString(),
                deviceFingerprintHash: deviceFingerprint,
            });

            setStep('done');
            if (onEvidenceSubmitted) onEvidenceSubmitted();
        } catch (err) {
            setError(err.message);
            setStep('error');
        }
    };

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 max-w-lg mx-auto">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">Resolution Proof Capture</h3>
                    <p className="text-sm text-gray-500">Cryptographic verification required</p>
                </div>
            </div>

            {/* Token Timer */}
            {token && timeLeft !== null && step !== 'done' && (
                <div className={`mb-4 p-3 rounded-lg text-sm font-medium flex items-center justify-between ${timeLeft > 300 ? 'bg-green-50 text-green-700' :
                        timeLeft > 60 ? 'bg-yellow-50 text-yellow-700' :
                            'bg-red-50 text-red-700'
                    }`}>
                    <span>⏱ Token expires in</span>
                    <span className="font-mono text-lg">{formatTime(timeLeft)}</span>
                </div>
            )}

            {/* GPS Status */}
            {step !== 'idle' && step !== 'done' && (
                <div className="mb-4">
                    {gpsError ? (
                        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                            📍 {gpsError}
                        </div>
                    ) : gpsPosition ? (
                        <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">
                            📍 GPS Active — {gpsPosition.latitude.toFixed(6)}, {gpsPosition.longitude.toFixed(6)}
                            <span className="ml-2 text-xs text-green-500">(±{Math.round(gpsPosition.accuracy)}m)</span>
                        </div>
                    ) : (
                        <div className="p-3 bg-yellow-50 text-yellow-700 rounded-lg text-sm animate-pulse">
                            📍 Acquiring GPS signal...
                        </div>
                    )}
                </div>
            )}

            {/* Geofence Status */}
            {geofenceStatus && step !== 'done' && (
                <div className={`mb-4 p-3 rounded-lg text-sm ${geofenceStatus.isInside
                        ? 'bg-green-50 text-green-700 border border-green-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                    {geofenceStatus.isInside ? (
                        <span>✅ Inside geofence — {geofenceStatus.distance}m / {geofenceStatus.radius}m radius</span>
                    ) : (
                        <span>❌ Outside geofence — {geofenceStatus.distance}m away (max: {geofenceStatus.radius}m)</span>
                    )}
                </div>
            )}

            {/* Step: Idle */}
            {step === 'idle' && (
                <button
                    onClick={handleGenerateToken}
                    className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                    🔐 Generate Resolution Proof Token
                </button>
            )}

            {/* Step: Token generated, ready to capture */}
            {step === 'capture' && (
                <div className="space-y-4">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*,video/*"
                        capture="environment"
                        className="hidden"
                        onChange={handleFileChange}
                    />

                    <button
                        onClick={handleCapture}
                        className="w-full py-3 px-4 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                    >
                        📸 Capture Evidence (Camera Only)
                    </button>

                    {capturedFile && (
                        <div className="p-3 bg-gray-50 rounded-lg text-sm">
                            <p className="font-medium text-gray-900">📄 {capturedFile.name}</p>
                            <p className="text-gray-500 text-xs mt-1">Size: {(capturedFile.size / 1024).toFixed(1)} KB</p>
                            {evidenceHash && (
                                <p className="text-gray-500 text-xs mt-1 font-mono break-all">
                                    SHA-256: {evidenceHash}
                                </p>
                            )}
                        </div>
                    )}

                    {capturedFile && evidenceHash && (
                        <button
                            onClick={handleSubmit}
                            disabled={geofenceStatus && !geofenceStatus.isInside}
                            className="w-full py-3 px-4 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            ✅ Submit Verified Evidence
                        </button>
                    )}
                </div>
            )}

            {/* Step: Submitting */}
            {step === 'submitting' && (
                <div className="text-center py-6">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-gray-600">Submitting and verifying evidence...</p>
                </div>
            )}

            {/* Step: Done */}
            {step === 'done' && (
                <div className="text-center py-6">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h4 className="text-lg font-semibold text-green-700 mb-1">Evidence Verified ✓</h4>
                    <p className="text-sm text-gray-500">
                        Cryptographic proof has been recorded. Citizens can now verify this resolution.
                    </p>
                    {evidenceHash && (
                        <p className="text-xs text-gray-400 font-mono mt-2 break-all">
                            Hash: {evidenceHash}
                        </p>
                    )}
                </div>
            )}

            {/* Step: Error */}
            {(step === 'error' || error) && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <p className="font-medium">⚠️ Error</p>
                    <p>{error}</p>
                    <button
                        onClick={() => { setStep('idle'); setError(null); setToken(null); }}
                        className="mt-2 text-red-600 underline text-xs"
                    >
                        Try again
                    </button>
                </div>
            )}
        </div>
    );
};

export default ResolutionProofCapture;
