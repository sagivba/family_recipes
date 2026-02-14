# Contributing

This repository contains two parts:
1) **Website** - a Jekyll-based static site, served locally via Docker/nginx (no `jekyll serve`)
2) **Recipe tooling (drafts-checker)** - Python scripts + unit tests used to validate/process recipe drafts

## Quick start

### Website (local)
Run:

```bash
docker compose up --build
```

Browse:

```text
http://localhost:8080
```

Stop:

```bash
docker compose down
```

### Python tooling (local)
See the full setup guide here:

- `docs/dev-python.md`

Quick test command:

```bash
python -m unittest discover -s code/_Tests -p "test_*.py" -v
```

## Branch and PR workflow

- Do not commit directly to `main`.
- Create a branch per change (feature/fix/docs).
- Keep PRs small and focused (avoid mixing website + python changes unless necessary).
- Include in the PR description:
  - What changed and why
  - How to test (commands you ran)


## Code style and safety

- Prefer minimal diffs (no unrelated refactors).
- Do not commit secrets (e.g. `.env`, `OPENAI_API_KEY`).

### Testing approach
- Prefer **TDD** when practical: write/adjust tests first (or alongside the change), then implement.
- Every behavior change **must** be covered by unit tests.

### Python guidelines
- Prefer **small, cohesive classes** when it improves maintainability (avoid large “utility modules” of unrelated functions).
- Use **standard library `unittest` only** (do not introduce `pytest`).
- Keep changes focused and avoid introducing new dependencies unless necessary.

### Documentation and rationale
- Every non-trivial class **must** include a docstring explaining what it does and its responsibilities.
- Comments should explain **why** we chose a solution (trade-offs), not restate code.
- For non-trivial algorithms, document the approach, alternatives considered, and complexity at a high level.

### PR definition of done
- [ ] Tests added/updated (unittest)
- [ ] New/changed classes have docstrings
- [ ] Non-trivial choices include a short “why” note (code comment or PR description)
