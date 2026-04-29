# Release Policy

## Branches

- `main`: stable-only; merged from `dev` via squash merge PR after all gates pass
- `dev`: integration branch; all feature work merges here first
- `feature/*`: ordinary development; branched from `dev`
- `fix/*`: bug fixes; branched from `dev`
- `refactor/*`: code restructuring; branched from `dev`
- `docs/*`: documentation only; branched from `dev`
- `release/*`: release preparation; branched from `dev`, merged to `main` and `dev`
- `hotfix/*`: emergency fixes; branched from `main`, merged to `main` and `dev`

## Versioning

Use [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

Rules:

- `MAJOR` -- breaking public API or protocol change; requires explicit approval and migration documentation
- `MINOR` -- new backward-compatible functionality
- `PATCH` -- backward-compatible fixes, docs, refactoring, CI, or chore changes
- Early project development (`0.x.y`) must not inflate major versions casually
- Autonomous systems must not bump major versions without explicit human approval
- Tags must be signed: `git tag -s vX.Y.Z`

## Conventional Commits and changelog groups

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>[optional scope]: <description>
```

Supported types and their CHANGELOG section:

| Type                                   | Section          | SemVer impact    |
| -------------------------------------- | ---------------- | ---------------- |
| `feat`                                 | Features         | MINOR            |
| `fix`                                  | Bug Fixes        | PATCH            |
| `perf`                                 | Performance      | PATCH            |
| `security`                             | Security         | PATCH (or MINOR) |
| `refactor`                             | Refactoring      | PATCH            |
| `revert`                               | Reverts          | PATCH            |
| `test`                                 | Tests            | PATCH            |
| `build`                                | Build            | PATCH            |
| `ci`                                   | CI               | PATCH            |
| `chore`                                | Chores           | PATCH            |
| `style`                                | Style            | PATCH            |
| `docs`                                 | Documentation    | PATCH            |
| `BREAKING CHANGE` footer or `!` suffix | Breaking Changes | MAJOR            |

## Merge strategy

**Squash merge** is the only allowed merge strategy for all PRs.

## Release gates

Before tagging a release, ensure:

- `bash scripts/verify.sh` exits 0
- docs are current
- `CHANGELOG.md` is freshly compiled
- relevant completion states are `verified_complete` in `state/feature-manifest.json`
- security review is complete where required

## Tagging

```bash
git tag -s vX.Y.Z <sha> -m "vX.Y.Z: short description"
PATH="$HOME/.cargo/bin:$PATH" git-cliff --output CHANGELOG.md
```

## Signed history

All autonomous commits must be signed: `git commit -S`.
All release tags must be signed: `git tag -s vX.Y.Z`.
