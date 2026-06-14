import { apiClient, getApiUrl } from '../client';

// Mock fetch globally
global.fetch = jest.fn();

describe('apiClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment variable
    delete process.env.VITE_API_URL;
  });

  describe('getApiUrl', () => {
    it('should return empty string when VITE_API_URL is not set', () => {
      expect(getApiUrl()).toBe('');
    });

    it('should return the VITE_API_URL when set', () => {
      process.env.VITE_API_URL = 'https://api.example.com';
      expect(getApiUrl()).toBe('https://api.example.com');
    });
  });

  describe('get', () => {
    it('should make a GET request and return JSON data on success', async () => {
      const mockResponse = { data: 'test' };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const result = await apiClient.get('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith('/test-endpoint', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should throw an error when response is not ok', async () => {
      const mockFetchResponse = {
        ok: false,
        status: 404
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      await expect(apiClient.get('/test-endpoint')).rejects.toThrow('HTTP error! status: 404');
    });

    it('should use the API URL prefix when VITE_API_URL is set', async () => {
      process.env.VITE_API_URL = 'https://api.example.com';
      const mockResponse = { data: 'test' };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      await apiClient.get('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/test-endpoint', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
    });
  });

  describe('post', () => {
    it('should make a POST request with JSON data and return response', async () => {
      const mockResponse = { success: true };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const testData = { name: 'test' };
      const result = await apiClient.post('/test-endpoint', testData);

      expect(global.fetch).toHaveBeenCalledWith('/test-endpoint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('should throw an error when POST response is not ok', async () => {
      const mockFetchResponse = {
        ok: false,
        status: 500
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      await expect(apiClient.post('/test-endpoint', {})).rejects.toThrow('HTTP error! status: 500');
    });

    it('should use the API URL prefix for POST requests', async () => {
      process.env.VITE_API_URL = 'https://api.example.com';
      const mockResponse = { success: true };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      await apiClient.post('/test-endpoint', {});

      expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/test-endpoint', expect.any(Object));
    });
  });

  describe('postForm', () => {
    it('should make a POST request with FormData and return response', async () => {
      const mockResponse = { success: true };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'test.txt');

      const result = await apiClient.postForm('/upload-endpoint', formData);

      expect(global.fetch).toHaveBeenCalledWith('/upload-endpoint', {
        method: 'POST',
        body: formData,
      });
      expect(result).toEqual(mockResponse);
    });

    it('should throw an error when FormData POST response is not ok', async () => {
      const mockFetchResponse = {
        ok: false,
        status: 400
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const formData = new FormData();

      await expect(apiClient.postForm('/upload-endpoint', formData)).rejects.toThrow('HTTP error! status: 400');
    });

    it('should use the API URL prefix for FormData POST requests', async () => {
      process.env.VITE_API_URL = 'https://api.example.com';
      const mockResponse = { success: true };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const formData = new FormData();

      await apiClient.postForm('/upload-endpoint', formData);

      expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/upload-endpoint', expect.any(Object));
    });
  });
});