import { apiClient } from './client';

// Helper to create a detector API function
const createDetectorApi = (endpoint) => async (data) => {
    // If data is a FormData object (checking if it has append method is a heuristic)
    if (data instanceof FormData) {
         return await apiClient.postForm(endpoint, data);
    }
    // If data contains an image property that is a base64 string,
    // the current backend implementation for infrastructure/vandalism/etc expects BYTES.
    // However, sending JSON with base64 encoded image is standard for JSON APIs.
    // BUT the backend endpoint defines `image: UploadFile = File(...)`.
    // This means it EXPECTS multipart/form-data.

    // So if the input is NOT FormData, we should probably wrap it or assume the caller creates FormData.
    // To be safe and consistent, let's assume the caller passes FormData or we convert it if possible.
    // If the caller passes { image: base64 }, we can't easily convert to File without logic.

    // Let's enforce that the caller must pass FormData for file upload endpoints.
    // Or we provide a helper to convert base64 to FormData.

    // But wait, my previous implementation of createDetectorApi was:
    // apiClient.post(endpoint, { image: imageSrc });
    // This sends JSON.
    // The backend `UploadFile = File(...)` will fail with 422 Unprocessable Entity if it receives JSON.

    // So createDetectorApi MUST use postForm and the caller MUST provide FormData.
    // OR we convert here.

    // Let's change createDetectorApi to expect FormData.
    return await apiClient.postForm(endpoint, data);
};

export const detectorsApi = {
  pothole: async (formData) => {
      return await apiClient.postForm('/api/detect-pothole', formData);
  },
  garbage: async (formData) => {
      return await apiClient.postForm('/api/detect-garbage', formData);
  },
  vandalism: createDetectorApi('/api/detect-vandalism'),
  flooding: createDetectorApi('/api/detect-flooding'),
  infrastructure: createDetectorApi('/api/detect-infrastructure'),
  illegalParking: createDetectorApi('/api/detect-illegal-parking'),
  streetLight: createDetectorApi('/api/detect-street-light'),
  fire: createDetectorApi('/api/detect-fire'),
  strayAnimal: createDetectorApi('/api/detect-stray-animal'),
  blockedRoad: createDetectorApi('/api/detect-blocked-road'),
  treeHazard: createDetectorApi('/api/detect-tree-hazard'),
  pest: createDetectorApi('/api/detect-pest'),
  depth: createDetectorApi('/api/analyze-depth'),
  smartScan: createDetectorApi('/api/detect-smart-scan'),
  severity: createDetectorApi('/api/detect-severity'),
  waste: createDetectorApi('/api/detect-waste'),
  civicEye: createDetectorApi('/api/detect-civic-eye'),
  transcribe: async (formData) => {
      return await apiClient.postForm('/api/transcribe-audio', formData);
  },
};
