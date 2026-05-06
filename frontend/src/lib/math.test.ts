// math.test.ts — Phase 0 smoke test
//
// Goal: prove the Vitest runner is wired up and runs in CI.
// This test is intentionally trivial — it has no application logic.
// Real tests for components, hooks, and the API client are added in Phase 4.
//
// LEARNING: Vitest with `globals: true` makes `describe`, `it`, and `expect`
// available without imports — the same API Jest users will recognise.
// This is configured in vite.config.ts test.globals and reflected in
// tsconfig.app.json via the "vitest/globals" types entry.

describe('smoke test', () => {
  it('arithmetic works', () => {
    expect(1 + 1).toBe(2)
  })

  it('string concatenation works', () => {
    expect('Movie' + ' QA').toBe('Movie QA')
  })
})
