const API_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = {
  get: async (endpoint) => {
    const response = await fetch(`${API_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  post: async (endpoint, data) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
    // For file uploads (FormData)
  postForm: async (endpoint, formData) => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            body: formData, // fetch automatically sets Content-Type to multipart/form-data with boundary
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
  }
};

export const getApiUrl = () => API_URL;
