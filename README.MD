# Family Recipes - Local Development

This repository contains a Jekyll-based site, developed and tested locally using **Docker**, **nginx**, and **WSL** on Windows 11. The local setup is designed to closely resemble the GitHub Pages production environment while remaining stable on Windows.

## Repository structure

This repository contains two parts:
- **Website**: a static site built with Jekyll and served locally via **Docker/nginx** (no `jekyll serve`).
- **Recipe tooling (drafts-checker)**: Python scripts + unit tests used to validate/process recipe drafts.

## Python development & tests

See: `docs/dev-python.md`

Quick commands:

```bash
pip install openai python-dotenv
python -m unittest discover -s code/_Tests -p "test_*.py" -v
```

---

## Prerequisites

- Windows 11
- WSL2 (Ubuntu)
- Docker Desktop (with WSL backend)
- VS Code (recommended)

---

## Local Development Architecture

Local development **does not use `jekyll serve`**.

Instead:

- **Jekyll** is used only for:
  - `jekyll build`
  - `jekyll build --watch`
- **nginx** serves the generated static site (`_site/`)

### Why this approach

- Avoids WEBrick / Ruby server issues on Windows
- Stable file watching under WSL
- Same behavior as production (static files)
- CI-friendly

---

## Running the Site Locally

### Start the development environment

```bash
docker compose up --build
```

This will:

- Build the site with Jekyll
- Start a watch process for automatic rebuilds
- Serve the site via nginx

### Access the site

```
http://localhost:8080
```

Changes to content or layouts will trigger an automatic rebuild. Refresh the browser to see updates.

---

### Stop the environment

```bash
docker compose down
```

---

## VS Code Tasks (Recommended)

The repository includes VS Code tasks for convenience.

Available tasks:

- **Dev: Start (docker compose up)**
- **Dev: Stop (docker compose down)**
- **Dev: Logs (docker compose logs)**

Run via:

```
Ctrl+Shift+P -> Tasks: Run Task
```

---

## Repository Structure Notes

- `_site/` Generated build output (ignored by Git)
- `_recipes/`, `ingredients/` Site content
- `_layouts/` Custom layouts (`doc`, `ingredients`)
- `Dockerfile`, `docker-compose.yml` Local development infrastructure

---

## Git Notes

- `_site/` and other build artifacts are ignored via `.gitignore`
- SSH is used for GitHub authentication
- Infrastructure and content are committed separately

---

## Production

Production is handled by **GitHub Pages**. Local `_site/` output is **not** pushed to GitHub.

---

## Troubleshooting

View logs:

```bash
docker compose logs -f
```

Service-specific logs:

```bash
docker compose logs jekyll-watch
docker compose logs web
```

---

## Status

Local development environment is stable and ready for ongoing content and feature development.
