## Goal
- Remove the duplicate `hashlib` import and the duplicate fingerprint helper from `auth.py` (REQ-004: one import, one helper, identical values).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: the nested `_fingerprint` helper and its calls inside `_build_principal_map` in `scripts/eventbus/auth.py`.

## Assumptions
- Module-level `_derive_token_fingerprint` and the nested `_fingerprint` both return the first 16 hex characters of the SHA-256 of the token, so replacing one with the other changes no value (verified in Step 3a).
- The nested helper is called three times: the shared `auth_token`, each per-role token, and the `admin_token` (verified in Step 3a).

## Design decisions
- Keep `_derive_token_fingerprint` (it also serves `resolve_principal`) and delete the nested helper with its inner `import hashlib`.

## Alternatives considered
N/A: a duplicate removal inside one function.

## Implementation
### Target file
`scripts/eventbus/auth.py`

### Procedure
1. Delete the nested `_fingerprint` definition, including its `import hashlib`, from `_build_principal_map`.
2. Replace its three call sites with `_derive_token_fingerprint`.

### Method
- Leave the module-level `import hashlib` and every other line of the function unchanged.

### Details
- `_build_principal_map` is C(15) by radon; the grade does not rise and drops slightly.

## Compatibility considerations
N/A: private helper; fingerprint values are unchanged.

## Security considerations
- Audit records keep the same non-secret token fingerprints (ADR-013 INV-05).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format --check scripts/eventbus/auth.py` and `uv run ruff check scripts/eventbus/auth.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit scripts/eventbus/auth.py -c pyproject.toml -ll`.
- `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_config.py -q`.
- `rg "import hashlib" scripts/eventbus/auth.py` shows one line.

## Completion criteria
- `auth.py` has one `import hashlib` and one fingerprint helper, and the auth and config suites pass.

## Out of Scope
- Any other cleanup in `auth.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the nested helper and update the three calls | Completed | 20261119-120025 | 20261119-120114 | Step 2 stale check clean; Step 3a: nested _fingerprint and its three calls plus module-level helper verified; file clean at baseline Changed: scripts/eventbus/auth.py (nested _fingerprint and its inner hashlib import removed; three calls use _derive_token_fingerprint). 99 passed; radon _build_principal_map stays C(15) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-120114 | 20261119-121150 | ruff, bandit pass; mypy: only the seq 23 allowed red remains; full suite once at end of unit End of unit: full suite 12918 passed 7 skipped 0 failed (not integration/production_paths_allowed/repo_scan); diff-cover 100% (37 lines); ADR-cited tests 52 passed; validation gates pass; ruff, mypy (571 files), lint-imports (6 kept), bandit, radon, vulture, suppression, compat shims, db separation clean |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (remove the duplicate import and helper)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `scripts/eventbus/auth.py`