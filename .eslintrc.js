module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['@typescript-eslint', 'react', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // Add your specific rules here
    'react/prop-types': 0,
    '@typescript-eslint/explicit-module-boundary-types': 0,
    '@typescript-eslint/explicit-function-return-type': 0,
    'react/react-in-jsx-scope': 0,
  },
};
