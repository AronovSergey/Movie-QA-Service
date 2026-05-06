# Cursor Rules — How they're organized

This project uses Cursor's `.cursor/rules/*.mdc` format to encode project conventions.

## Files in this set

```
.
└── .cursor/
    └── rules/
        ├── 00-core.mdc                          # alwaysApply: dual mandate, repo layout, universal rules
        ├── 10-java-spring-boot.mdc              # Scoped to services/auth, chat, catalog, scheduler, gateway, *.java
        ├── 20-python-fastapi.mdc                # Scoped to services/rag, services/ingestion, *.py
        ├── 30-frontend-react.mdc                # Scoped to frontend/, *.tsx, *.ts
        ├── 40-rag-engineering.mdc               # Scoped to RAG service, ingestion, eval/
        ├── 50-event-driven.mdc                  # Scoped to scheduler, ingestion, messaging code
        ├── 60-testing.mdc                       # Scoped to test files
        └── 70-process-and-discipline.mdc        # alwaysApply: ADRs, git, secrets, learning notes
```

## How they activate

- **`alwaysApply: true`** rules (`00-core.mdc`, `70-process-and-discipline.mdc`) are loaded into every Cursor request.
- **Glob-scoped rules** activate only when you're editing a file matching the glob. So when you open a `.tsx` file, the React rules load. When you open a `.java` file, the Spring Boot rules load.

## How to extend or adjust

- Treat rules as **living documentation.** As you discover patterns Cursor consistently gets wrong, add a rule.
- Keep each `.mdc` file focused. Under ~500 lines is the sweet spot.
- Use `// LEARNING:` (or `# LEARNING:` in Python) to mark teaching comments — these are deliberate, not noise.
- When you make a significant decision, write an ADR in `docs/adr/` and reference it from the rule that governs the area.

## Personal overrides (gitignored)

If you want personal preferences that aren't part of the project standard:

```bash
echo ".cursor/rules/personal.mdc" >> .gitignore
```

Create `.cursor/rules/personal.mdc` with your local-only preferences. It loads alongside the others but isn't shared.

## Verifying rules are loaded

In Cursor, open the Agent sidebar — active rules show up there. If you don't see your rules, check:

1. The file is at the right path (`.cursor/rules/*.mdc`).
2. The frontmatter syntax is correct (`---` delimiters, valid YAML).
3. The globs match the file you have open (for scoped rules).
4. Restart Cursor if you just added the files.

## Philosophy

The rules encode the project's two main commitments:

1. **Code quality at a senior level.** Strict typing, real tests, idempotency, error handling, layered architecture. No "it's just a learning project" shortcuts in code.

2. **Generous learning context.** ADRs, `// LEARNING:` comments, references to docs. Future-you should understand every non-obvious choice.

These are deliberately not in tension. The rules push for both at once.
