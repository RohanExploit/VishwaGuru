// Resolution Proof API functions (Issue #292)

const API_BASE = import.meta.env.VITE_API_URL || '';

export const resolutionProofApi = {
    // Generate a Resolution Proof Token for a grievance
    async generateToken(grievanceId, authorityEmail, geofenceRadius = 200) {
        const response = await fetch(`${API_BASE}/api/resolution-proof/generate-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grievance_id: grievanceId,
                authority_email: authorityEmail,
                geofence_radius_meters: geofenceRadius,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    // Submit resolution evidence with cryptographic proof
    async submitEvidence(data) {
        const response = await fetch(`${API_BASE}/api/resolution-proof/submit-evidence`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token_id: data.tokenId,
                evidence_hash: data.evidenceHash,
                gps_latitude: data.gpsLatitude,
                gps_longitude: data.gpsLongitude,
                capture_timestamp: data.captureTimestamp,
                device_fingerprint_hash: data.deviceFingerprintHash || null,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    // Get verification status for a grievance (public)
    async getVerification(grievanceId) {
        const response = await fetch(`${API_BASE}/api/resolution-proof/verify/${grievanceId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    // Get evidence details for a grievance (public)
    async getEvidence(grievanceId) {
        const response = await fetch(`${API_BASE}/api/resolution-proof/evidence/${grievanceId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    // Get audit trail for a grievance (public)
    async getAuditLog(grievanceId) {
        const response = await fetch(`${API_BASE}/api/resolution-proof/audit-log/${grievanceId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    },
};
