# Contributing

Thanks for contributing! This repository contains **two parts**:

- **The website** (family recipes site) served via GitHub Pages / Jekyll.
- **The Python toolchain** under `code/` (lint/check/pipeline/tests) used to process and validate recipe drafts.

Please keep changes focused and easy to review.

## Quick start

### Website
- Edit markdown content and site assets.
- GitHub Pages build/deploy is handled by the Pages workflow.

### Python toolchain
From the repo root:

```bash
python -m pip install -r code/requirements.in
python -m unittest discover -s code/_Tests -p "test_*.py" -v
```

## Code style and safety

- Prefer **minimal diffs** (no unrelated refactors).
- Keep commits **small and scoped** (one purpose per PR).
- Do **not** commit secrets (e.g. `.env`, tokens, API keys).
- If AI features are used (e.g. `--use-ai`), document behavior changes and add/adjust tests.

## Development principles

### TDD (Test-Driven Development)
- For any behavior change or bug fix, add/adjust **tests first**, then implement.
- A PR should not reduce coverage for changed behavior.

### Prefer OOP where it improves clarity
- Prefer **small, cohesive classes** with clear responsibilities over large free-function scripts.
- Keep I/O and orchestration separated from pure logic when practical.

### Testing framework
- Use **`unittest`** (not `pytest`).
- Put tests under `code/_Tests/` and name them `test_*.py`.
- Prefer deterministic tests; avoid network/API calls.
- Use `code/_testcases/` fixtures for table-driven tests when possible.

## Documentation expectations

- Every public class should have a short docstring explaining **what it does**.
- In-code comments should focus on **why** a solution was chosen (not what the code obviously does).
- If a change requires non-trivial algorithmic decisions, document the reasoning (and alternatives) in:
  - the PR description and/or
  - a short section in the relevant module docstring/comment

## Pull requests

- Branch naming: use descriptive names (e.g. `docs/...`, `ci/...`, `codex/...`).
- Ensure CI is green before requesting review.
- Include in the PR description:
  - What changed
  - Why it changed
  - How to test locally (exact commands)

Recommended merge strategy: **Squash merge** for a clean history.



