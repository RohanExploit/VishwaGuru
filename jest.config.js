// ts-jest preset provides TypeScript compilation support for jest ^29 tests
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.ts'],
};
