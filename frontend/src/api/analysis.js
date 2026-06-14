import { apiClient } from './client';

export const analysisApi = {
    suggestCategoryText: async (text) => {
        return await apiClient.post('/api/suggest-category-text', { text });
    }
};
