// setup.ts — Vitest global test setup
//
// This file runs before every test file (configured via vite.config.ts
// `test.setupFiles`).
//
// LEARNING: @testing-library/jest-dom extends Vitest's `expect` with DOM-aware
// matchers: toBeInTheDocument(), toHaveClass(), toHaveValue(), etc.
// Without this import those matchers don't exist and tests that use them
// will throw "TypeError: expect(...).toBeInTheDocument is not a function".
import '@testing-library/jest-dom'
