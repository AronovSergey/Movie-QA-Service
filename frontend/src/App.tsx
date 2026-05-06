// App.tsx — Phase 0 skeleton
//
// This is a placeholder. Real application layout, routing, and feature
// components are added in Phase 4.
//
// LEARNING: We use a named export rather than a default export.
// Named exports make rename refactors safe (the import name must match),
// they show up correctly in IDE auto-imports, and they prevent the
// inconsistency of one file calling it "App" and another "MyApp".

export function App() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Movie QA
        </h1>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Phase 0 skeleton — real UI arrives in Phase 4.
        </p>
      </div>
    </div>
  )
}
