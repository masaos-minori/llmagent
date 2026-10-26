## Goal

Make `scripts/db/create_schema.py::create_eventbus_schema()` fail closed on a malformed database already stamped with the current version, so a malformed EventBus database is rejected at deployment time even though `PRAGMA user_version` matches (`REQ-003`).

## Scope

- Modify `scripts/db/create_schema.py::create_eventbus_schema()` only: insert the shared-validator shape check after DDL execution and before commit.
- Do not touch `deploy/init_db.sh`, `deploy/setup_services.sh`, `scripts/eventbus/schema.py`, or the shared validator here — those are the sibling deployment, readiness, runtime, and fingerprint procedures (`REQ-001`, `REQ-003`, `REQ-002`).

## Assumptions

- The shared validator (`scripts/shared/eventbus_schema_fingerprint.py`, created by the sibling procedure) exposes a fingerprint builder and a shape-comparison entry point that raises on any deviation, even when `user_version` matches.
- The v0 legacy repair path (lines 121-124) is kept: an unstamped v0 database is still left unstamped, never reset to a wrong version.
- Only a malformed database already stamped with the current version raises; a fresh canonical creation passes unchanged.

## Design decisions

- **Insert the check as an `elif existing:` branch after the v0 branch, before `commit`.** `create_eventbus_schema()` runs `db.executescript(build_eventbus_schema_sql())` at line 117 inside the try/except at lines 116-120, then commits at line 125. Verified 2026-10-26: an unconditional validator call between line 120 and line 125 would also run on the v0 repair path and raise on malformed unstamped legacy databases — breaking the repair path the Assumptions protect. The check therefore runs only when the database already existed and is stamped with the current version (`elif existing:` — the earlier guard at lines 111-115 guarantees `before == eventbus_schema_version()` in that case), so the v0 branch (lines 121-124) is reached unchanged.
- **Keep the v0 branch (lines 121-124) unchanged.** The legacy repair path that leaves an unstamped v0 database unstamped must survive; the shape check only runs for a database that already exists and is stamped with the current version.

## Alternatives considered

- **Validate before running the DDL.** Rejected: the defect is a malformed database that already passed a version-only check; the shape must be validated after the DDL produces the tables.
- **Reuse the columns-only `_matches_current_schema()`.** Rejected: it is columns-only and tied to the v0 repair flow; the shared fingerprint (tables/indexes/constraints/FKs/triggers) is the canonical comparison and belongs in one place.

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Open `create_eventbus_schema()` (line 104) and locate the DDL block (lines 116-125).
2. After the v0 repair branch (lines 121-124) and before `db.commit()` (line 125), add an `elif existing and db.conn is not None:` branch that calls the shared validator's shape-comparison entry point on `db.conn` — the still-open connection whose uncommitted DDL results must be visible to the `PRAGMA` reads — so a malformed, already-stamped database raises.
3. Leave the v0 repair branch (lines 121-124) untouched.

### Method

- Import the shared validator at module level (`from shared.eventbus_schema_fingerprint import assert_matches`), the same way `scripts/db/config.py` imports `shared`. Importing `shared` from the `db` package is permitted by `.importlinter`: `shared-is-leaf` forbids `shared` importing `db`, never `db` importing `shared`.
- On any deviation the shared validator raises `RuntimeError`; let it propagate past `db.commit()` (the `open()` context manager rolls back, so partial DDL repairs of the malformed database are not persisted).
- Keep the `existing and before == 0` branch (lines 121-124) exactly as-is so the v0 legacy repair path is preserved; the validator never runs for unstamped or freshly created databases.

### Details

- The shared validator reads `scripts/eventbus/schema.sql` as text and derives the fingerprint via `PRAGMA` on a fresh in-memory apply, so the deployment comparison is apples-to-apples with the runtime path.
- A malformed database is one whose tables/columns/indexes/constraints/FKs/triggers deviate from `schema.sql`; the first differing object raises `RuntimeError` naming it.
- No new module-level symbol is introduced here; the only change is the inserted call within `create_eventbus_schema()`.

## Compatibility considerations

- `create_eventbus_schema()` is called by `create_schema()` and by `deploy/init_db.sh`; only a malformed, already-stamped database now raises, so fresh canonical creation and the v0 repair path are unaffected.
- Importing `shared` from the `db` package does not violate `.importlinter`; `shared-is-leaf` and `eventbus-is-isolated` stay KEPT.

## Security considerations

- Fail-closed: a malformed, correctly-stamped database raises before deployment proceeds. Only object metadata is compared; no secrets or token values are read.

## Rollback considerations

- Revert the single inserted call inside `create_eventbus_schema()` (or `git checkout` the parent commit); the v0 path, the DDL block, and the module imports are untouched.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/db/create_schema.py` | Unit: fail-closed on malformed stamped DB; v0 repair kept; fresh canonical passes | `uv run pytest tests/db/test_create_schema.py` | malformed raises `RuntimeError`; v0 left unstamped; fresh creation stamps current version |

## Completion criteria

- A malformed database already stamped with the current version makes the shared validator raise `RuntimeError` from `create_eventbus_schema()` after DDL, before commit.
- A fresh database still ends in the current shape and is stamped with `eventbus_schema_version()`.
- The v0 legacy repair path is preserved: an unstamped v0 database is left unstamped.
- `ruff`, `mypy`, `bandit`, and `lint-imports` pass with all contracts KEPT.

## Out of Scope

- The `deploy/init_db.sh` shape gate (`REQ-003`), the deploy readiness/config gates (`REQ-004`, `REQ-005`), the runtime startup gate in `scripts/eventbus/schema.py` (`REQ-002`), and the shared validator itself (`REQ-001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the shared-validator shape check into `create_eventbus_schema()` after DDL, before commit | Completed | 20261026-131358 | 20261026-132358 | REQ-003 validator call in elif existing branch; corrected from after-DDL placement |
| 2 | Add fail-closed + v0-repair tests to `tests/db/test_create_schema.py` | Completed | 20261026-132358 | 20261026-132358 | fail-closed test added; v0-repair kept via existing tests; 67 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261026-132942 | 20261026-132942 | ruff/mypy/bandit/lint-imports 6 KEPT/fast gates pass; full suite 10128 passed 9 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261026-132942 | N/A: runtime only N/A: runtime only, no docs in scope |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `scripts/db/create_schema.py`