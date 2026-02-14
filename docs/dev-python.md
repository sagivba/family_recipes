# Python development & tests (drafts-checker)

This repository contains two main parts:
1) A static website (built with Jekyll and served locally via Docker/nginx)
2) Python tooling (drafts-checker) used to validate/process recipe drafts and related automation

## Environment (WSL + VS Code + Conda)

Create and activate a conda environment:

```bash
conda create -n family_recipes python=3.12
conda activate family_recipes
```

Install Python dependencies:

```bash
pip install openai python-dotenv
```

## Repo .env

Create a `.env` file in the repository root with:

```env
PYTHONPATH=code
```

If you use AI features (e.g. `--use-ai`), also set:

```env
OPENAI_API_KEY=...   # do not commit secrets
```

## Running unit tests

```bash
python -m unittest discover -s code/_Tests -p "test_*.py" -v
```

## VS Code workspace files

This repo includes a `.vscode/` directory with editor settings, launch configurations and tasks
to make local development (WSL/conda + docker compose) consistent.

## Further reading

- VS Code + WSL + Conda + unittest setup:
  https://www.sagiv-barhoom.me/python/2026/02/13/vscode_wsl_conda_unittest_setup.html
