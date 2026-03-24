// ts-jest was bumped from ^29.1.2 to ^29.4.6 (not newly added) to align with jest ^29.7.0
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.ts'],
};
