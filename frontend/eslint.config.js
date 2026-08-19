import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'dev-dist', 'coverage', 'node_modules', 'public/sw.js']),

  // Application source: browser environment.
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': [
        'error',
        {
          varsIgnorePattern: '^[A-Z_]',
          argsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
    },
  },

  // Tests, mocks and setup run under Jest/jsdom with node globals available.
  // Without this block eslint reported ~300 no-undef errors for `describe`,
  // `it`, `expect`, `jest`, `global` and `process`.
  {
    files: [
      '**/__tests__/**/*.{js,jsx}',
      '**/__mocks__/**/*.{js,jsx}',
      '**/*.{test,spec}.{js,jsx}',
      'src/setupTests.js',
    ],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
      },
    },
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },

  // Build/tooling config files run in Node.
  {
    files: ['*.config.js', 'jest.transform.js', 'babel.config.js'],
    languageOptions: {
      globals: { ...globals.node },
      sourceType: 'module',
    },
  },
])
