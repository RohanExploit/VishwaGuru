// Grievance and Escalation API functions

const API_BASE = import.meta.env.VITE_API_URL || '';

export const grievancesApi = {

  // Create grievance
  async create(data) {
    const response = await fetch(`${API_BASE}/api/grievances`,{
      method: 'POST',
      headers :{
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if(!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  //Get list of grievances
  async getAll(params = {}) {
    const queryParams = new URLSearchParams();
    if(params.status) queryParams.append('status', params.status);
    if(params.category) queryParams.append('category', params.category);
    if(params.limit) queryParams.append('limit', params.limit);
    if(params.offset) queryParams.append('offset', params.offset);

    const response = await fetch(`${API_BASE}/api/grievances?${queryParams}`);
    if(!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  //Get single grievance
  async getById(grievanceId) {
    const response = await fetch(`${API_BASE}/api/grievances/${grievanceId}`);
    if(!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  //Get map data
  async getMapData() {
    const response = await fetch(`${API_BASE}/api/grievances/map`);
    if(!response.ok) {
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
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
};