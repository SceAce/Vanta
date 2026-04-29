# Repository Hygiene and Source-of-Truth Rules

## Goal

Keep Trellis explainable to both humans and agents.

## Branch workflow

All development work happens on the `dev` integration branch. Direct commits to `main` are prohibited except by the release process.

- Start every session by pulling the latest `dev`.
- Create feature branches off `dev` for isolated work.
- Merge feature branches back into `dev` via **squash merge** PR.
- Only the release process promotes `dev` into `main` via **squash merge** PR.
- After merge, the source branch is **automatically deleted** (GitHub setting).

## Branch naming convention

| Pattern             | Purpose             | Base branch | Merge target   |
| ------------------- | ------------------- | ----------- | -------------- |
| `feature/<name>`    | New functionality   | `dev`       | `dev`          |
| `fix/<name>`        | Bug fixes           | `dev`       | `dev`          |
| `refactor/<name>`   | Code restructuring  | `dev`       | `dev`          |
| `docs/<name>`       | Documentation only  | `dev`       | `dev`          |
| `release/<version>` | Release preparation | `dev`       | `main` + `dev` |
| `hotfix/<name>`     | Emergency fix       | `main`      | `main` + `dev` |

## Merge strategy

**Squash merge** is the only allowed merge strategy for all PRs.

## Session hooks

Seven hooks enforce hygiene automatically (Claude + Codex compatible):

| Hook                            | Trigger                   | Effect                                                             |
| ------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| `auto_sync_check.py`            | `UserPromptSubmit`        | Fetches `origin --prune`; blocks if local branch is behind remote. |
| `block_unsafe_git_commit.py`    | `PreToolUse` (Bash)       | Blocks any `git commit` that omits the `-S` signing flag.          |
| `block_protected_bash_write.py` | `PreToolUse` (Bash)       | Blocks Bash writes to protected files (CLAUDE.md/CODEX.md, hooks). |
| `block_protected_file_write.py` | `PreToolUse` (Write/Edit) | Blocks Write/Edit to protected files.                              |
| `block_dirty_stop.py`           | `Stop` / `SubagentStop`   | Blocks session stop when the working tree is dirty.                |
| `auto_push.py`                  | `Stop`                    | Pushes current branch and reachable annotated tags to origin.      |
| `pre_compact_state_save.py`     | `PreCompact`              | Saves session state snapshot before context compression.           |

Hooks live in `scripts/hooks/` and are wired in `.claude/settings.json` and `.codex`.

## Module documentation (docs/modules/)

Every crate, app, and tool must have a corresponding module doc:

```text
docs/modules/
  crates/<name>.md
  apps/<name>.md
  tools/<name>.md
```

Enforced by **invariant 4** in `scripts/ci/check_doc_freshness.py`.

## Why docs/specs/state belong in Git

This is a long-running engineering system. Durable planning, completion state,
policy, and evidence must survive session boundaries and be reviewable in pull requests.
