import { apiClient as client } from './client';

export const authApi = {
  login: async (email, password) => {
    const response = await client.post('/auth/login', { email, password });
    return response;
  },

  signup: async (userData) => {
    const response = await client.post('/auth/signup', userData);
    return response;
  },

  me: async () => {
    const response = await client.get('/auth/me');
    return response;
  }
};
