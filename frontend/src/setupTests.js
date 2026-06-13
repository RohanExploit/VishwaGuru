import '@testing-library/jest-dom';

// Mock import.meta globally for Jest
global.import = global.import || {};
global.import.meta = {
  env: {
    VITE_API_URL: 'http://localhost:3000'
  }
};