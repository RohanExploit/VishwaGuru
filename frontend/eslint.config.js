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

      // eslint-plugin-react-hooks v7 ships the React Compiler ruleset. The four
      // rules below are compiler-readiness checks, not correctness failures:
      // they fire on the ref-access and fetch-in-effect patterns used
      // throughout the twenty detector components. Clearing them means
      // restructuring those components, which is the consolidation work
      // deliberately deferred until after the first mobile release, so they are
      // warnings rather than errors and remain visible in every lint run.
      //
      // react-hooks/rules-of-hooks stays an error on purpose. It caught a real
      // crash: views/ActionView.jsx called useEffect after an early return, so
      // the hook count changed with props.
      'react-hooks/immutability': 'warn',
      'react-hooks/exhaustive-deps': 'warn',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/static-components': 'warn',
      'react-hooks/rules-of-hooks': 'error',
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
