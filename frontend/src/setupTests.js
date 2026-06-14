import '@testing-library/jest-dom';

// Mock import.meta globally for Jest
window.import = window.import || {};
window.import.meta = {
  env: {
    VITE_API_URL: 'http://localhost:3000'
  }
};