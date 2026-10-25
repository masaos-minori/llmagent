## Goal

Make `scripts/eventbus/schema.py::_init_schema()` validate the EventBus schema shape against the shared fingerprint when `PRAGMA user_version` already matches, so a correctly stamped but malformed database is refused at startup (`REQ-002`).

## Scope

- Modify `scripts/eventbus/schema.py::_init_schema()` only: insert the shared-validator shape check after the version-equal early return.
- Do not touch `scripts/db/create_schema.py`, `deploy/init_db.sh`, or the shared validator here — those are the sibling procedures for the DDL and deployment gates (`REQ-003`) and the validator itself (`REQ-001`).

## Assumptions

- The shared validator (`scripts/shared/eventbus_schema_fingerprint.py`, created by the sibling procedure) exposes a fingerprint builder and a shape-comparison entry point that raises on any deviation, even when `user_version` matches.
- `_init_schema()` runs on every DB open via `open_db`; rejecting only MALFORMED schemas leaves canonical test databases (provisioned through the real `create_eventbus_schema()`) passing unchanged.
- Unstamped v0 behavior is unchanged: the legacy repair path stamps only after its tables match `schema.sql`.

## Design decisions

- **Insert the check after the version-equal early return.** `_init_schema()` returns at the `found == expected` branch (lines 82-83) today without any shape check, and `_matches_current_schema()` (line 54) runs only for the v0 branch (line 84). Placing the shared-validator call immediately after line 83 refuses a correctly stamped but malformed database while leaving the v0 repair path (lines 84-86) intact.
- **Reuse the shared validator rather than re-implementing a shape check.** The runtime and `init_db.sh` share one definition of a valid schema, so `_init_schema()` calls the same validator the deployment path uses instead of a second, columns-only comparison.

## Alternatives considered

- **Leave the version-equal branch returning early.** Rejected: this is the defect — a matching version stamp does not prove tables/columns/indexes exist, so a malformed database starts and fails only when a route touches a missing object.
- **Extend `_matches_current_schema()` to run for every version.** Rejected: it is columns-only and tied to the v0 repair flow; the shared fingerprint (tables/indexes/constraints/FKs/triggers) is the canonical comparison and belongs in one place.

## Implementation

### Target file

`scripts/eventbus/schema.py`

### Procedure

1. Open `_init_schema()` (line 66) and locate the version-equal early return at lines 82-83.
2. Insert the shared-validator shape check between the early return (line 83) and the v0 branch (line 84), so a stamped database is validated before `_init_schema()` returns.
3. Add startup rejection + canonical-pass tests (`tests/eventbus/test_eventbus_startup.py`).

### Method

- After `if found == expected:` / `return` (lines 82-83), call the shared validator's shape-comparison entry point against `conn` and let it raise `RuntimeError` on any deviation. The import of the shared validator and the call sit inside `_init_schema()`, not at module import time, so `shared-is-leaf` and `eventbus-is-isolated` stay KEPT.
- Keep the v0 repair branch (lines 84-86) unchanged: an unstamped database is still stamped only after `_matches_current_schema()` confirms its columns.

### Details

- The shared validator reads `scripts/eventbus/schema.sql` as text and derives the fingerprint via `PRAGMA` on a fresh in-memory apply, so the runtime comparison is apples-to-apples with the deployment path.
- The first differing table/column/index raises `RuntimeError` naming the offending object, giving operators an actionable message at startup.
- No new module-level symbol is introduced here; the only change is the inserted call within `_init_schema()`.

## Compatibility considerations

- `_init_schema()` runs on every DB open; the validator rejects only MALFORMED schemas, so the ~16 test files that open DBs pass unchanged for canonical databases. Run `tests/db` and `tests/eventbus` post-implementation to confirm.
- Pure behavioral addition: no public-API, import, or signature change.

## Security considerations

- Fail-closed: a malformed, correctly-stamped database raises before the service proceeds. Only object metadata is compared; no secrets or token values are read.

## Rollback considerations

- Revert the single inserted call inside `_init_schema()` (or `git checkout` the parent commit); the v0 path and module imports are untouched.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/schema.py` | Unit: malformed stamped DB rejected when version matches; canonical passes | `uv run pytest tests/eventbus/test_eventbus_startup.py` | malformed refused; canonical passes |

## Completion criteria

- A database stamped with the current version but missing a column, index, constraint, or FK raises `RuntimeError` from `_init_schema()` even though `PRAGMA user_version` matches.
- A canonical database (matching `schema.sql`) passes `_init_schema()` unchanged.
- `ruff`, `mypy`, `bandit`, and `lint-imports` pass with all contracts KEPT.

## Out of Scope

- The DDL fail-closed gate in `scripts/db/create_schema.py` and `deploy/init_db.sh` (`REQ-003`), the deploy readiness/config gates (`REQ-004`, `REQ-005`), and the shared validator itself (`REQ-001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the shared-validator shape check into `_init_schema()` after the version-equal early return | Pending | — | — | REQ-002 |
| 2 | Add startup rejection + canonical-pass tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: runtime only |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `scripts/eventbus/schema.py`
