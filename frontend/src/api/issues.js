import { apiClient } from './client';
import { fakeRecentIssues } from '../fakeData';

export const issuesApi = {
  getRecent: async (limit = 10, offset = 0) => {
    try {
      return await apiClient.get('/api/issues/recent', {
        params: { limit, offset }
      });
    } catch (error) {
      console.warn('Failed to fetch recent issues, using fake data', error);
      return fakeRecentIssues;
    }
  },

  create: async (formData) => {
    // formData is expected to be a FormData object containing 'file', 'description', etc.
    return await apiClient.postForm('/api/issues', formData);
  },

  vote: async (id) => {
    return await apiClient.post(`/api/issues/${id}/vote`, {}); // The backend endpoint might not require a body for upvote
  }
};
