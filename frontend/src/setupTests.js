import '@testing-library/jest-dom';

// jsdom does not implement TextEncoder/TextDecoder, but react-router v7 needs
// them at import time -- without these, any test that renders a routed
// component dies with "ReferenceError: TextEncoder is not defined" before a
// single assertion runs. This is why the views had no component tests.
import { TextDecoder, TextEncoder } from 'node:util';

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}

// Mock import.meta globally for Jest
global.import = global.import || {};
global.import.meta = {
  env: {
    VITE_API_URL: 'http://localhost:3000'
  }
};