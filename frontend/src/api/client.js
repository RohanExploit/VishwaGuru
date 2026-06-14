const API_URL = import.meta.env.VITE_API_URL || '';

let authToken = localStorage.getItem('token');

const getHeaders = (headers = {}) => {
  const authHeaders = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
  return {
    ...authHeaders,
    'Content-Type': 'application/json',
    ...headers
  };
};

export const apiClient = {
  setToken: (token) => {
    if (!token) {
      authToken = null;
      localStorage.removeItem('token');
    } else {
      authToken = token;
      localStorage.setItem('token', token);
    }
  },
  removeToken: () => {
    authToken = null;
    localStorage.removeItem('token');
  },
  get: async (endpoint, options = {}) => {
    let url = `${API_URL}${endpoint}`;
    if (options.params) {
      const queryString = new URLSearchParams(options.params).toString();
      url += `?${queryString}`;
    }
    const response = await fetch(url, {
      headers: getHeaders(options.headers)
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return null;
  },
  post: async (endpoint, data) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return null;
  },
  // For file uploads (FormData)
  postForm: async (endpoint, formData) => {
    const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
    // Do NOT set Content-Type for FormData, browser does it with boundary
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return null;
  }
};

export const getApiUrl = () => API_URL;
