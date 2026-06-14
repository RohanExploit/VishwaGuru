import { apiClient } from './client';

export const adminApi = {
    getUsers: async (skip = 0, limit = 100) => {
        return await apiClient.get('/admin/users', { params: { skip, limit } });
    },

    getStats: async () => {
        return await apiClient.get('/admin/stats');
    }
};
