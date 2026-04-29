# Contributing to Trellis

## Core requirements

- License: MIT
- Rust: `1.92.0`
- Python: `>=3.13` (target `3.13.11`) managed with `uv`
- Node package manager: `pnpm`
- Signed commits are required; use `git commit -S`

## Git setup

```bash
git config core.hooksPath .githooks
git config commit.gpgsign true
```

If you use SSH-based signing, ensure your signing key is configured in Git and GitHub.

## Commit format

Use concise, imperative commit subjects and signed commits.

Examples:

- `feat(core): add initial type definitions`
- `fix(server): correct request parsing error`
- `docs(policies): update coding style guide`

## Before opening a pull request

Run:

```bash
./scripts/bootstrap.sh
./scripts/verify.sh
```

Ensure you updated:

- tests
- docs
- `state/progress.json`
- changelog (via Conventional Commits)

## Branch strategy

- `main`: stable only
- `dev`: integration
- `feature/*`: ordinary development
- `release/*`: release preparation
- `hotfix/*`: emergency fixes from `main`
