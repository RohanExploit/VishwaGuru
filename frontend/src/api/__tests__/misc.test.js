import { miscApi } from '../misc';
import { fakeResponsibilityMap } from '../../fakeData';

// Mock the apiClient
jest.mock('../client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn()
  }
}));

// Mock fakeData
jest.mock('../../fakeData', () => ({
  fakeResponsibilityMap: {
    'pothole': { department: 'Roads', contact: 'roads@example.com' },
    'garbage': { department: 'Sanitation', contact: 'sanitation@example.com' }
  }
}));

import { apiClient } from '../client';

describe('miscApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getResponsibilityMap', () => {
    it('should return responsibility map from API on success', async () => {
      const mockMap = {
        'pothole': { department: 'PWD', contact: 'pwd@maharashtra.gov.in' },
        'garbage': { department: 'Municipal', contact: 'municipal@city.gov.in' }
      };

      apiClient.get.mockResolvedValue(mockMap);

      const result = await miscApi.getResponsibilityMap();

      expect(apiClient.get).toHaveBeenCalledWith('/api/responsibility-map');
      expect(result).toEqual(mockMap);
    });

    it('should return fake data when API call fails', async () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const error = new Error('Network error');

      apiClient.get.mockRejectedValue(error);

      const result = await miscApi.getResponsibilityMap();

      expect(apiClient.get).toHaveBeenCalledWith('/api/responsibility-map');
      expect(result).toEqual(fakeResponsibilityMap);
      expect(consoleWarnSpy).toHaveBeenCalledWith('Failed to fetch responsibility map, using fake data', error);

      consoleWarnSpy.mockRestore();
    });

    it('should handle different types of API errors', async () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

      apiClient.get.mockRejectedValue(new TypeError('Connection timeout'));

      const result = await miscApi.getResponsibilityMap();

      expect(result).toEqual(fakeResponsibilityMap);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });
  });

  describe('chat', () => {
    it('should call apiClient.post with correct parameters', async () => {
      const message = 'Hello, how can I report a pothole?';
      const mockResponse = {
        response: 'You can report potholes through our app or website.'
      };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await miscApi.chat(message);

      expect(apiClient.post).toHaveBeenCalledWith('/api/chat', { query: message });
      expect(result).toEqual(mockResponse);
    });

    it('should handle different message types', async () => {
      const testMessages = [
        'Simple question',
        'What is the process for reporting issues?',
        'Can you help me find my MLA?',
        'Long message with multiple sentences and questions about civic issues.'
      ];

      for (const message of testMessages) {
        apiClient.post.mockResolvedValue({ response: 'Mock response' });

        await miscApi.chat(message);

        expect(apiClient.post).toHaveBeenCalledWith('/api/chat', { query: message });
      }
    });

    it('should propagate API errors', async () => {
      const message = 'Test message';
      const error = new Error('Chat service unavailable');

      apiClient.post.mockRejectedValue(error);

      await expect(miscApi.chat(message)).rejects.toThrow('Chat service unavailable');
    });

    it('should handle empty messages', async () => {
      const message = '';
      const mockResponse = { response: 'Please ask a question.' };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await miscApi.chat(message);

      expect(apiClient.post).toHaveBeenCalledWith('/api/chat', { query: message });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getRepContact', () => {
    it('should call apiClient.get with correct pincode parameter', async () => {
      const pincode = '400001';
      const mockResponse = {
        mla: 'John Doe',
        mp: 'Jane Smith',
        contact: '+91-1234567890'
      };

      apiClient.get.mockResolvedValue(mockResponse);

      const result = await miscApi.getRepContact(pincode);

      expect(apiClient.get).toHaveBeenCalledWith('/api/mh/rep-contacts?pincode=400001');
      expect(result).toEqual(mockResponse);
    });

    it('should handle different pincode formats', async () => {
      const testPincodes = ['400001', '411001', '500001'];

      for (const pincode of testPincodes) {
        apiClient.get.mockResolvedValue({ success: true });

        await miscApi.getRepContact(pincode);

        expect(apiClient.get).toHaveBeenCalledWith(`/api/mh/rep-contacts?pincode=${pincode}`);
      }
    });

    it('should propagate API errors', async () => {
      const pincode = '400001';
      const error = new Error('Representative lookup failed');

      apiClient.get.mockRejectedValue(error);

      await expect(miscApi.getRepContact(pincode)).rejects.toThrow('Representative lookup failed');
    });

    it('should handle invalid pincode responses', async () => {
      const pincode = '999999';
      const mockResponse = { error: 'Invalid pincode' };

      apiClient.get.mockResolvedValue(mockResponse);

      const result = await miscApi.getRepContact(pincode);

      expect(result).toEqual(mockResponse);
    });
  });

  describe('getStats', () => {
    it('should call apiClient.get with correct endpoint', async () => {
      const mockStats = {
        totalIssues: 1250,
        resolvedIssues: 980,
        pendingIssues: 270,
        categories: {
          pothole: 450,
          garbage: 320,
          infrastructure: 200
        }
      };

      apiClient.get.mockResolvedValue(mockStats);

      const result = await miscApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/stats');
      expect(result).toEqual(mockStats);
    });

    it('should handle empty stats response', async () => {
      const mockStats = {
        totalIssues: 0,
        resolvedIssues: 0,
        pendingIssues: 0,
        categories: {}
      };

      apiClient.get.mockResolvedValue(mockStats);

      const result = await miscApi.getStats();

      expect(result).toEqual(mockStats);
    });

    it('should propagate API errors', async () => {
      const error = new Error('Statistics service unavailable');

      apiClient.get.mockRejectedValue(error);

      await expect(miscApi.getStats()).rejects.toThrow('Statistics service unavailable');
    });

    it('should handle network timeouts', async () => {
      const timeoutError = new Error('Request timeout');

      apiClient.get.mockRejectedValue(timeoutError);

      await expect(miscApi.getStats()).rejects.toThrow('Request timeout');
    });
  });
});