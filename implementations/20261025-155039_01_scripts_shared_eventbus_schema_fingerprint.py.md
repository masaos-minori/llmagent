## Goal

Create one canonical EventBus schema fingerprint validator at `scripts/shared/eventbus_schema_fingerprint.py` (new) that derives the schema fingerprint (tables; columns as name/type/nullability/default/pk-flag; indexes; table-level UNIQUE/PK/CHECK constraints; foreign keys via `PRAGMA foreign_key_list`; triggers if any) from `scripts/eventbus/schema.sql` by applying the DDL to a fresh in-memory database and reading `PRAGMA` metadata, then compares that fingerprint against a target connection and raises on any mismatch — even when `PRAGMA user_version` already matches (`REQ-001`).

## Scope

- Create `scripts/shared/eventbus_schema_fingerprint.py` (new) only: a stdlib-`sqlite3` module exposing a fingerprint builder and a shape-comparison entry point.
- Do not modify `scripts/eventbus/schema.py`, `scripts/db/create_schema.py`, or `deploy/init_db.sh` here — those are the sibling procedures for the runtime, DDL, and deployment gates (`REQ-002`, `REQ-003`).

## Assumptions

- `scripts/eventbus/schema.sql` currently defines tables and indexes only (no triggers), so the trigger leg of the fingerprint is a no-op today but MUST still be implemented so a future trigger is caught.
- The validator uses stdlib `sqlite3` only and reads `schema.sql` as text, so `shared-is-leaf` and `eventbus-is-isolated` stay KEPT and `.importlinter` needs no change.
- `shared` is the only root package both `eventbus` and `db` may import (per `.importlinter`), which is why the validator lives in `scripts/shared/` rather than `scripts/db/`.
- The fingerprint composition is sufficient to reject the malformed-stamped-DB case; this resolves `UNK-02`.

## Design decisions

- **Location in `scripts/shared/`.** `.importlinter` forbids `shared` importing `db` and `eventbus` importing `db`; only `shared` is reachable by both callers, so the shared validator belongs here and reads `schema.sql` as text (the same DDL source `create_schema.py`'s DDL builder reads) instead of importing `db`.
- **Derive via `PRAGMA` on a fresh in-memory apply, not by parsing SQL text.** Applying `schema.sql` to an in-memory database and reading `PRAGMA table_info`, `PRAGMA index_info`, `PRAGMA foreign_key_list`, `PRAGMA trigger_list` yields canonicalized object metadata (resolved column type, notnull, dflt_value, pk), so the fingerprint stays correct even if `schema.sql` formatting changes; the same routine runs against the target connection for an apples-to-apples comparison.

## Alternatives considered

- **Parse `schema.sql` text directly.** Rejected: text parsing must replicate SQLite's canonicalization of defaults/nullability/types and is brittle to DDL formatting.
- **Place the validator in `scripts/db/`.** Rejected: `shared-is-leaf` forbids `shared` importing `db`, and `eventbus-is-isolated` forbids `eventbus` importing `db`; only `shared` is importable by both callers.

## Implementation

### Target file

`scripts/shared/eventbus_schema_fingerprint.py` (new)

### Procedure

1. Replace the placeholder bodies below in the scaffolded module.
2. Add a constant holding the absolute path to `scripts/eventbus/schema.sql` (resolved relative to this module's package) plus a helper that applies the DDL to a fresh in-memory database.
3. Implement the fingerprint builder that returns a structured, comparable fingerprint (tables → columns → indexes; table-level constraints; FKs; triggers).
4. Implement the expected-fingerprint builder and the shape-comparison entry point that raises on any deviation.
5. Add unit tests (equivalence + rejection) and run the validation sequence.

### Method

- `apply_schema_in_memory` (new) opens an in-memory database and runs `schema.sql` via `executescript`.
- `build_fingerprint` (new) walks `sqlite_master` for tables and indexes, then for each table reads `PRAGMA table_info` (name, type, notnull, dflt_value, pk), `PRAGMA foreign_key_list` (FKs), table-level constraints, and `PRAGMA trigger_list` (triggers); returns a frozen, hashable structure.
- `expected_fingerprint` (new) calls `apply_schema_in_memory` (new) then `build_fingerprint` (new).
- `assert_matches` (new) compares `expected_fingerprint` (new) against `build_fingerprint` (new) of the target connection and raises `RuntimeError` on any mismatch.

### Details

- Column tuple per column: `(name, type.lower(), notnull, dflt_value, pk)`; normalize column-type case for stability.
- Index tuple per index: `(name, unique, expr)` from `PRAGMA index_info` / `sqlite_master`.
- Table-level constraints capture UNIQUE/PK/CHECK; FKs come from `PRAGMA foreign_key_list`.
- Triggers are `(name, sql)` from `PRAGMA trigger_list`; skipped when `schema.sql` has none.
- Comparison deep-compares the structures; the first differing object raises `RuntimeError` naming the table/column/index so operators get an actionable message.

## Compatibility considerations

- Pure addition: no existing symbol, import, or public-API change. `shared-is-leaf` and `eventbus-is-isolated` stay KEPT because the module imports only stdlib `sqlite3` and reads `schema.sql` as text.

## Security considerations

- Fail-closed: a malformed database raises before startup or deployment proceeds. Only object metadata is compared; no secrets or token values are read or logged.

## Rollback considerations

- New file: revert by deleting `scripts/shared/eventbus_schema_fingerprint.py` (or `git checkout` the parent commit).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/shared/eventbus_schema_fingerprint.py` (new) | Unit: equivalence + rejection | add fingerprint cases to `uv run pytest tests/db/test_create_schema.py` | identical fingerprint for a canonical DB; raises on a missing column/index/constraint/FK |

## Completion criteria

- `build_fingerprint` (new) returns an identical structure for a fresh in-memory apply of `schema.sql` and a canonical database opened from the same DDL.
- A database missing a column, index, table-level constraint, or FK — or with a changed column type/nullability/default/pk — makes `assert_matches` (new) raise `RuntimeError`.
- `ruff`, `mypy`, `bandit`, and `lint-imports` pass with all contracts KEPT.

## Out of Scope

- The runtime gate in `scripts/eventbus/schema.py` (`REQ-002`), the DDL fail-closed gate in `scripts/db/create_schema.py` and `deploy/init_db.sh` (`REQ-003`), and the deploy readiness/config gates (`REQ-004`, `REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the shared fingerprint validator | Pending | — | — | |
| 2 | Add fingerprint equivalence + rejection tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: new module |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `scripts/shared/eventbus_schema_fingerprint.py` (new)
