// Mock version of client.js for testing
const getApiUrl = () => {
  return process.env.VITE_API_URL || '';
};

const makeRequest = async (url, options = {}) => {
  const apiUrl = getApiUrl();
  const fullUrl = apiUrl ? `${apiUrl}${url}` : url;
  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const apiClient = {
  get: (url) => makeRequest(url),
  post: (url, data) => makeRequest(url, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  put: (url, data) => makeRequest(url, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  delete: (url) => makeRequest(url, {
    method: 'DELETE'
  }),
  postForm: (url, formData) => {
    const apiUrl = getApiUrl();
    const fullUrl = apiUrl ? `${apiUrl}${url}` : url;
    return fetch(fullUrl, {
      method: 'POST',
      body: formData
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    });
  }
};

export { getApiUrl };