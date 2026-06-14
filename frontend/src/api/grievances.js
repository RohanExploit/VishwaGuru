// Grievance and Escalation API functions

const API_BASE = import.meta.env.VITE_API_URL || '';

export const grievancesApi = {
  // Get list of grievances with escalation history
  async getAll(params = {}) {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.category) queryParams.append('category', params.category);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.offset) queryParams.append('offset', params.offset);

    const response = await fetch(`${API_BASE}/api/grievances?${queryParams}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  // Get single grievance with escalation history
  async getById(grievanceId) {
    const response = await fetch(`${API_BASE}/api/grievances/${grievanceId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  // Get escalation statistics
  async getStats() {
    const response = await fetch(`${API_BASE}/api/escalation-stats`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  // Manually escalate a grievance
  async escalate(grievanceId, reason) {
    const response = await fetch(`${API_BASE}/api/grievances/${grievanceId}/escalate?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
};