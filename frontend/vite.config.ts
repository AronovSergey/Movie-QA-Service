// LEARNING: We import defineConfig from 'vitest/config' rather than 'vite'
// because vitest/config re-exports Vite's defineConfig extended with the
// `test` property types. Using plain 'vite' gives TypeScript errors on the
// test block. Both produce identical runtime behaviour.
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [
    react(),
    // LEARNING: Tailwind v4 ships as a Vite plugin — no postcss.config.js
    // or tailwind.config.ts needed. The plugin reads from index.css and
    // processes utility classes at build time. See the Tailwind v4 migration
    // guide if upgrading a v3 project.
    tailwindcss(),
  ],

  test: {
    // `globals: true` makes Vitest inject `describe`, `it`, `test`, `expect`,
    // etc. globally — same API as Jest. Combined with the tsconfig types entry,
    // TypeScript knows about them without explicit imports in every test file.
    globals: true,
    environment: 'jsdom',
    // setup.ts runs before every test file; it imports @testing-library/jest-dom
    // which extends expect with matchers like toBeInTheDocument(), toHaveClass().
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
