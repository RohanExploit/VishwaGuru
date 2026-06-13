import '@testing-library/jest-dom';

// Mock import.meta globally for Jest
// Jest doesn't natively support import.meta in CommonJS environments (which is the default without experimental flags).
// However, the test failures due to import.meta in src/api/grievances.js indicate babel isn't transforming it properly.
// The easiest fix without changing Jest config is just avoiding global.import.meta and mocking it in the test environment if needed.