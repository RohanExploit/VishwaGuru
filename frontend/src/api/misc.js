import { apiClient } from './client';
import { fakeResponsibilityMap } from '../fakeData';

export const miscApi = {
  getResponsibilityMap: async () => {
    try {
      return await apiClient.get('/api/responsibility-map');
    } catch (error) {
      console.warn('Failed to fetch responsibility map, using fake data', error);
      return fakeResponsibilityMap;
    }
  },

  chat: async (message) => {
      return await apiClient.post('/api/chat', { query: message });
  },

  getRepContact: async (pincode) => {
      return await apiClient.get(`/api/mh/rep-contacts?pincode=${pincode}`);
  },

  getStats: async () => {
      return await apiClient.get('/api/stats');
  },

  getLeaderboard: async () => {
      return await apiClient.get('/api/leaderboard');
  }
};
