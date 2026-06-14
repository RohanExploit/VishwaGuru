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
        return await apiClient.postForm('/detect-pothole', formData);
    },
    garbage: async (formData) => {
        return await apiClient.postForm('/detect-garbage', formData);
    },
    vandalism: createDetectorApi('/detect-vandalism'),
    flooding: createDetectorApi('/detect-flooding'),
    infrastructure: createDetectorApi('/detect-infrastructure'),
    illegalParking: createDetectorApi('/detect-illegal-parking'),
    streetLight: createDetectorApi('/detect-street-light'),
    fire: createDetectorApi('/detect-fire'),
    strayAnimal: createDetectorApi('/detect-stray-animal'),
    blockedRoad: createDetectorApi('/detect-blocked-road'),
    treeHazard: createDetectorApi('/detect-tree-hazard'),
    pest: createDetectorApi('/detect-pest'),
    depth: createDetectorApi('/analyze-depth'),
    smartScan: createDetectorApi('/detect-smart-scan'),
    severity: createDetectorApi('/detect-severity'),
    waste: createDetectorApi('/detect-waste'),
    civicEye: createDetectorApi('/detect-civic-eye'),
    transcribe: async (formData) => {
        return await apiClient.postForm('/transcribe-audio', formData);
    },
};
