import { detectorsApi } from '../detectors';

// Mock the apiClient
jest.mock('../client', () => ({
  apiClient: {
    postForm: jest.fn()
  },
  getApiUrl: jest.fn(() => '')
}));

import { apiClient } from '../client';

describe('detectorsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const detectorTestCases = [
    { name: 'pothole', endpoint: '/detect-pothole' },
    { name: 'garbage', endpoint: '/detect-garbage' },
    { name: 'vandalism', endpoint: '/detect-vandalism' },
    { name: 'flooding', endpoint: '/detect-flooding' },
    { name: 'infrastructure', endpoint: '/detect-infrastructure' },
    { name: 'illegalParking', endpoint: '/detect-illegal-parking' },
    { name: 'streetLight', endpoint: '/detect-street-light' },
    { name: 'fire', endpoint: '/detect-fire' },
    { name: 'strayAnimal', endpoint: '/detect-stray-animal' },
    { name: 'blockedRoad', endpoint: '/detect-blocked-road' },
    { name: 'treeHazard', endpoint: '/detect-tree-hazard' },
    { name: 'pest', endpoint: '/detect-pest' }
  ];

  detectorTestCases.forEach(({ name, endpoint }) => {
    describe(name, () => {
      it(`should call apiClient.postForm with correct endpoint for ${name}`, async () => {
        const mockFormData = new FormData();
        mockFormData.append('file', new Blob(['test image']), 'test.jpg');

        const mockResponse = {
          detections: [
            { label: 'pothole', confidence: 0.95, box: [10, 20, 100, 120] }
          ]
        };

        apiClient.postForm.mockResolvedValue(mockResponse);

        const result = await detectorsApi[name](mockFormData);

        expect(apiClient.postForm).toHaveBeenCalledWith(endpoint, mockFormData);
        expect(result).toEqual(mockResponse);
      });

      it(`should handle successful detection response for ${name}`, async () => {
        const mockFormData = new FormData();
        const mockResponse = {
          detections: [
            { label: 'detected_object', confidence: 0.87, box: [5, 15, 95, 105] },
            { label: 'another_object', confidence: 0.92, box: [200, 150, 300, 250] }
          ]
        };

        apiClient.postForm.mockResolvedValue(mockResponse);

        const result = await detectorsApi[name](mockFormData);

        expect(result).toEqual(mockResponse);
      });

      it(`should handle empty detection response for ${name}`, async () => {
        const mockFormData = new FormData();
        const mockResponse = { detections: [] };

        apiClient.postForm.mockResolvedValue(mockResponse);

        const result = await detectorsApi[name](mockFormData);

        expect(result).toEqual(mockResponse);
      });

      it(`should propagate API errors for ${name}`, async () => {
        const mockFormData = new FormData();
        const error = new Error('Detection failed');

        apiClient.postForm.mockRejectedValue(error);

        await expect(detectorsApi[name](mockFormData)).rejects.toThrow('Detection failed');
      });

      it(`should handle network errors for ${name}`, async () => {
        const mockFormData = new FormData();
        const networkError = new TypeError('Failed to fetch');

        apiClient.postForm.mockRejectedValue(networkError);

        await expect(detectorsApi[name](mockFormData)).rejects.toThrow('Failed to fetch');
      });
    });
  });

  describe('FormData validation', () => {
    it('should handle FormData with different file types', async () => {
      const testCases = [
        { type: 'image/jpeg', filename: 'photo.jpg' },
        { type: 'image/png', filename: 'image.png' },
        { type: 'image/webp', filename: 'pic.webp' }
      ];

      for (const { type, filename } of testCases) {
        const mockFormData = new FormData();
        const blob = new Blob(['fake image data'], { type });
        mockFormData.append('file', blob, filename);

        apiClient.postForm.mockResolvedValue({ detections: [] });

        await detectorsApi.pothole(mockFormData);

        expect(apiClient.postForm).toHaveBeenCalledWith('/detect-pothole', mockFormData);
      }
    });

    it('should handle FormData with additional metadata', async () => {
      const mockFormData = new FormData();
      mockFormData.append('file', new Blob(['image']), 'test.jpg');
      mockFormData.append('location', 'Main Street');
      mockFormData.append('description', 'Issue description');
      mockFormData.append('timestamp', '2024-01-01T12:00:00Z');

      const mockResponse = { detections: [{ label: 'pothole', confidence: 0.9 }] };
      apiClient.postForm.mockResolvedValue(mockResponse);

      const result = await detectorsApi.pothole(mockFormData);

      expect(result).toEqual(mockResponse);
    });
  });

  describe('error handling edge cases', () => {
    it('should handle malformed FormData', async () => {
      // Create a FormData that might cause issues
      const mockFormData = new FormData();
      // Empty FormData
      const error = new Error('Invalid form data');

      apiClient.postForm.mockRejectedValue(error);

      await expect(detectorsApi.vandalism(mockFormData)).rejects.toThrow('Invalid form data');
    });

    it('should handle server errors with different status codes', async () => {
      const errorCases = [
        new Error('HTTP error! status: 400'),
        new Error('HTTP error! status: 500'),
        new Error('HTTP error! status: 503')
      ];

      for (const error of errorCases) {
        apiClient.postForm.mockRejectedValue(error);

        const mockFormData = new FormData();
        mockFormData.append('file', new Blob(['test']), 'test.jpg');

        await expect(detectorsApi.garbage(mockFormData)).rejects.toThrow(error.message);
      }
    });
  });
});