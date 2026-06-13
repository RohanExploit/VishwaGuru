import React, { useState, useEffect } from 'react';
import { resolutionProofApi } from '../api/resolutionProof';

/**
 * ResolutionVerification - Citizen-facing component showing
 * cryptographic verification status of a grievance resolution.
 *
 * Features:
 * - "Verified by System" badge
 * - Location match indicator
 * - Evidence integrity status
 * - Hash fingerprint for transparency
 * - Audit trail viewer
 */
const ResolutionVerification = ({ grievanceId, compact = false }) => {
    const [verification, setVerification] = useState(null);
    const [auditLog, setAuditLog] = useState(null);
    const [showAudit, setShowAudit] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!grievanceId) return;

        const fetchVerification = async () => {
            try {
                setLoading(true);
                const data = await resolutionProofApi.getVerification(grievanceId);
                setVerification(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchVerification();
    }, [grievanceId]);

    const fetchAuditLog = async () => {
        try {
            const data = await resolutionProofApi.getAuditLog(grievanceId);
            setAuditLog(data);
            setShowAudit(true);
        } catch (err) {
            console.error('Failed to fetch audit log:', err);
        }
    };

    if (loading) {
        return (
            <div className="animate-pulse flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-200 rounded-full"></div>
                <div className="w-24 h-4 bg-gray-200 rounded"></div>
            </div>
        );
    }

    if (error || !verification) return null;

    // No evidence submitted yet
    if (verification.evidence_count === 0) {
        if (compact) return null;
        return (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                No Proof Submitted
            </div>
        );
    }

    const statusConfig = {
        verified: {
            bg: 'bg-green-50 border-green-200',
            badge: 'bg-green-100 text-green-700',
            dot: 'bg-green-500',
            icon: '✓',
            label: 'Verified by System',
        },
        pending: {
            bg: 'bg-yellow-50 border-yellow-200',
            badge: 'bg-yellow-100 text-yellow-700',
            dot: 'bg-yellow-500',
            icon: '⏳',
            label: 'Verification Pending',
        },
        flagged: {
            bg: 'bg-orange-50 border-orange-200',
            badge: 'bg-orange-100 text-orange-700',
            dot: 'bg-orange-500',
            icon: '⚠',
            label: 'Flagged for Review',
        },
        fraud_detected: {
            bg: 'bg-red-50 border-red-200',
            badge: 'bg-red-100 text-red-700',
            dot: 'bg-red-500',
            icon: '✕',
            label: 'Fraud Detected',
        },
    };

    const config = statusConfig[verification.verification_status] || statusConfig.pending;

    // Compact badge mode
    if (compact) {
        return (
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.badge}`}>
                <span className={`w-2 h-2 rounded-full ${config.dot}`}></span>
                {config.label}
            </span>
        );
    }

    // Full verification card
    return (
        <div className={`rounded-xl border p-4 ${config.bg}`}>
            {/* Header Badge */}
            <div className="flex items-center justify-between mb-3">
                <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${config.badge}`}>
                    <span className="text-base">{config.icon}</span>
                    {config.label}
                </span>
                {verification.evidence_count > 0 && (
                    <span className="text-xs text-gray-500">
                        {verification.evidence_count} evidence record{verification.evidence_count !== 1 ? 's' : ''}
                    </span>
                )}
            </div>

            {/* Verification Details */}
            <div className="space-y-2 mb-3">
                <div className="flex items-center gap-2 text-sm">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${verification.location_match ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'
                        }`}>
                        {verification.location_match ? '✓' : '✕'}
                    </span>
                    <span className="text-gray-700">
                        Location Match: {verification.location_match ? 'Confirmed' : 'Mismatch'}
                    </span>
                </div>

                <div className="flex items-center gap-2 text-sm">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${verification.evidence_integrity ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'
                        }`}>
                        {verification.evidence_integrity ? '✓' : '✕'}
                    </span>
                    <span className="text-gray-700">
                        Evidence Integrity: {verification.evidence_integrity ? 'Intact' : 'Compromised'}
                    </span>
                </div>

                {verification.resolution_timestamp && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="w-5 h-5 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs">🕐</span>
                        <span className="text-gray-700">
                            Resolved: {new Date(verification.resolution_timestamp).toLocaleString()}
                        </span>
                    </div>
                )}
            </div>

            {/* Hash Fingerprint */}
            {verification.evidence_hash && (
                <div className="p-2.5 bg-white bg-opacity-60 rounded-lg mb-3">
                    <p className="text-xs text-gray-500 mb-1">Evidence Hash Fingerprint</p>
                    <p className="text-xs font-mono text-gray-700 break-all select-all">
                        {verification.evidence_hash}
                    </p>
                </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
                <button
                    onClick={fetchAuditLog}
                    className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                    View Audit Trail
                </button>
            </div>

            {/* Audit Trail Modal */}
            {showAudit && auditLog && (
                <div className="mt-3 border-t pt-3">
                    <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-semibold text-gray-700">Audit Trail</h5>
                        <button
                            onClick={() => setShowAudit(false)}
                            className="text-gray-400 hover:text-gray-600 text-xs"
                        >
                            Close
                        </button>
                    </div>
                    {auditLog.audit_entries.length === 0 ? (
                        <p className="text-xs text-gray-500">No audit entries</p>
                    ) : (
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                            {auditLog.audit_entries.map((entry) => (
                                <div key={entry.id} className="flex items-start gap-2 text-xs">
                                    <span className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${entry.action === 'verified' ? 'bg-green-500' :
                                            entry.action === 'created' ? 'bg-blue-500' :
                                                entry.action === 'flagged' ? 'bg-orange-500' :
                                                    'bg-red-500'
                                        }`}></span>
                                    <div>
                                        <span className="font-medium text-gray-700 capitalize">{entry.action}</span>
                                        <span className="text-gray-400 ml-1">
                                            {new Date(entry.timestamp).toLocaleString()}
                                        </span>
                                        {entry.details && (
                                            <p className="text-gray-500 mt-0.5">{entry.details}</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ResolutionVerification;
