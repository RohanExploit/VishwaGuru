export default {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/src/__mocks__/fileMock.js',
    // No global redirect for ./client. It pointed every importer at
    // src/__mocks__/client.js, so api/__tests__/client.test.js asserted
    // against a hand-written fixture instead of the real client -- eleven
    // tests that could not fail if the client broke. Suites that do want a
    // stub call jest.mock('../client', ...) with their own factory, and
    // import.meta.env is handled by babel-plugin-transform-vite-meta-env.
    '^\\./location$': '<rootDir>/src/__mocks__/location.js',
    '^../location$': '<rootDir>/src/__mocks__/location.js'
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.(js|jsx)',
    '<rootDir>/src/**/*.(test|spec).(js|jsx)'
  ],
  collectCoverageFrom: [
    'src/api/**/*.{js,jsx}',
    '!src/api/__tests__/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};