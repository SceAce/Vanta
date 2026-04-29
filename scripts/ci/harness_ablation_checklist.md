# Harness Ablation Checklist

Use this checklist when modifying CI harness scripts, lint rules, or
verification tooling in this project. The goal is to ensure that
removing or weakening a check is deliberate and documented.

## Before disabling or removing a check

- [ ] Identify the check by name and file path (e.g., `scripts/lint/taste_t001_no_unwrap.py`)
- [ ] Document **why** the check is being removed or weakened
- [ ] Confirm the change is not masking a real defect
- [ ] Search for any other checks that depend on the one being removed
- [ ] Verify that `scripts/verify.sh` still passes after the change

## Before adding a new exemption

- [ ] Confirm the exemption is scoped as narrowly as possible
- [ ] Add an inline comment explaining the exemption
- [ ] If the exemption is in `_EXEMPT` lists (e.g., `check_dep_docs.py`), document why
- [ ] Set a reminder or TODO to revisit the exemption

## Before modifying threshold values

- [ ] Record the old and new values in the commit message
- [ ] Update `state/benchmark-baseline.json` if performance thresholds change
- [ ] Update `state/quality-scores.json` if quality thresholds change
- [ ] Confirm the new threshold is based on measured data, not convenience

## Before changing CI workflow files

- [ ] Test the workflow locally if possible (e.g., `act` for GitHub Actions)
- [ ] Ensure secrets and environment variables are not exposed in logs
- [ ] Verify that required status checks in branch protection still reference the correct job names
- [ ] Update `docs/policies/tdd.md` or `docs/policies/ci-policy.md` if the change affects documented processes

## After any harness change

- [ ] Run `./scripts/verify.sh` end-to-end
- [ ] Run `./scripts/bootstrap.sh` to confirm the dev environment still sets up correctly
- [ ] Confirm all lint scripts exit 0 on the current codebase
- [ ] Update `CHANGELOG.md` with the harness change
- [ ] Update `state/progress.json` if the change affects milestone criteria

## Rollback plan

If a harness change causes unexpected failures:

1. Revert the commit
2. Open an issue documenting the failure
3. Reproduce locally before attempting a fix
4. Re-apply with the fix included in the same PR
