import '@testing-library/jest-dom';

// Mock import.meta globally for Jest
globalThis.import = globalThis.import || {};
globalThis.import.meta = {
  env: {
    VITE_API_URL: 'http://localhost:3000'
  }
};