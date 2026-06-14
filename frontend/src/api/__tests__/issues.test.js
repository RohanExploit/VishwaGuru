import { issuesApi } from '../issues';
import { fakeRecentIssues } from '../../fakeData';

// Mock the apiClient
jest.mock('../client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    postForm: jest.fn()
  }
}));

// Mock fakeData
jest.mock('../../fakeData', () => ({
  fakeRecentIssues: [
    { id: 1, title: 'Fake Issue 1' },
    { id: 2, title: 'Fake Issue 2' }
  ]
}));

import { apiClient } from '../client';

describe('issuesApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getRecent', () => {
    it('should return issues from API on success', async () => {
      const mockIssues = [
        { id: 1, title: 'Real Issue 1' },
        { id: 2, title: 'Real Issue 2' }
      ];

      apiClient.get.mockResolvedValue(mockIssues);

      const result = await issuesApi.getRecent();

      expect(apiClient.get).toHaveBeenCalledWith('/api/issues/recent');
      expect(result).toEqual(mockIssues);
    });

    it('should return fake data when API call fails', async () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const error = new Error('Network error');

      apiClient.get.mockRejectedValue(error);

      const result = await issuesApi.getRecent();

      expect(apiClient.get).toHaveBeenCalledWith('/api/issues/recent');
      expect(result).toEqual(fakeRecentIssues);
      expect(consoleWarnSpy).toHaveBeenCalledWith('Failed to fetch recent issues, using fake data', error);

      consoleWarnSpy.mockRestore();
    });

    it('should handle different types of API errors', async () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

      // Test with different error types
      apiClient.get.mockRejectedValue(new TypeError('Network timeout'));

      const result = await issuesApi.getRecent();

      expect(result).toEqual(fakeRecentIssues);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });
  });

  describe('create', () => {
    it('should call apiClient.postForm with correct parameters', async () => {
      const mockFormData = new FormData();
      mockFormData.append('file', new Blob(['test']), 'test.jpg');
      mockFormData.append('description', 'Test issue');

      const mockResponse = { id: 123, status: 'created' };
      apiClient.postForm.mockResolvedValue(mockResponse);

      const result = await issuesApi.create(mockFormData);

      expect(apiClient.postForm).toHaveBeenCalledWith('/api/issues', mockFormData);
      expect(result).toEqual(mockResponse);
    });

    it('should propagate API errors', async () => {
      const mockFormData = new FormData();
      const error = new Error('Upload failed');

      apiClient.postForm.mockRejectedValue(error);

      await expect(issuesApi.create(mockFormData)).rejects.toThrow('Upload failed');
    });

    it('should handle different FormData configurations', async () => {
      const mockFormData = new FormData();
      mockFormData.append('file', new Blob(['image data']), 'photo.png');
      mockFormData.append('description', 'Pothole on main road');
      mockFormData.append('category', 'infrastructure');
      mockFormData.append('location', 'Main Street');

      const mockResponse = { id: 456, status: 'created' };
      apiClient.postForm.mockResolvedValue(mockResponse);

      const result = await issuesApi.create(mockFormData);

      expect(apiClient.postForm).toHaveBeenCalledWith('/api/issues', mockFormData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('vote', () => {
    it('should call apiClient.post with correct parameters', async () => {
      const issueId = 123;
      const mockResponse = { votes: 5, status: 'voted' };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await issuesApi.vote(issueId);

      expect(apiClient.post).toHaveBeenCalledWith('/api/issues/123/vote', {});
      expect(result).toEqual(mockResponse);
    });

    it('should handle different issue IDs', async () => {
      const testCases = [1, 999, 'abc123'];

      for (const issueId of testCases) {
        apiClient.post.mockResolvedValue({ success: true });

        await issuesApi.vote(issueId);

        expect(apiClient.post).toHaveBeenCalledWith(`/api/issues/${issueId}/vote`, {});
      }
    });

    it('should propagate API errors', async () => {
      const issueId = 123;
      const error = new Error('Vote failed');

      apiClient.post.mockRejectedValue(error);

      await expect(issuesApi.vote(issueId)).rejects.toThrow('Vote failed');
    });
  });
});