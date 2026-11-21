## Goal

Register `mcp_dedup` in `tools/check_db_separation.py`: table ownership for the new ledger tables and coverage of the `db_path` key in `config/mcp_dedup.toml` (REQ-009, AC-9).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 01 lands in the same release unit and renames the ledger to `dedup_call_state` (Plan D-6), which removes the ownership-name collision with the workflow database's `tool_call_state`.
- The dedup config key is `db_path` (no per-database name prefix), so it cannot match the current `_DB_PATH_KEY_RE = ^(rag|session|workflow|eventbus)_db_path$` pattern; an explicit registration is the chosen route.

## Design decisions
- Add `mcp_dedup` to `TABLE_OWNERSHIP` with `frozenset({"dedup_call_state", "store_meta", "call_attempt_history"})`.
- Extend the path-key logic with an explicit `(config file, key) -> database` registration for `config/mcp_dedup.toml` `db_path` instead of loosening the regex into a prefix-agnostic pattern (keeps the ADR-008 name contract tight).

## Alternatives considered
- Loosening `_DB_PATH_KEY_RE` to also accept a bare `db_path`: rejected — it would match `db_path` keys in unrelated config files and weaken the separation check.

## Implementation
### Target file
`tools/check_db_separation.py`
### Procedure
Extend the canonical registration tables and the config-path-key scan for the dedup database.
### Method
1. Add the `mcp_dedup` entry to `TABLE_OWNERSHIP` (current shape: four databases only, verified 2026-11-21).
2. Add the explicit path-key registration for `config/mcp_dedup.toml` `db_path` alongside the regex-driven `*_db_path` keys; keep the ADR-008 header comment updated with the new database.
3. Confirm the name-lookup helpers (used by the D-6 collision rule) resolve the new table names to `mcp_dedup` and no longer see `tool_call_state` from two databases once row 01 lands.
### Details
- The comment at the top of `TABLE_OWNERSHIP` requires updating together with the ADR when a database is added: ADR-008 already governs `mcp_dedup` as a disposable store (no ADR edit in this Plan; note the registration in the commit message).

### Companion test files
- `tests/tools/test_check_db_separation.py`
  - Procedure: Add registration cases: `mcp_dedup` path-key check for `config/mcp_dedup.toml` `db_path` and ownership of `dedup_call_state`/`store_meta`/`call_attempt_history`.
  - Validation: `uv run pytest tests/tools/test_check_db_separation.py` passes.

## Compatibility considerations
- `workflow` keeps ownership of `tool_call_state` (workflow DB table, untouched); the dedup rename makes each table name map to exactly one database.

## Security considerations
- N/A: validator registration only.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run python tools/check_db_separation.py` exits 0 with `mcp_dedup` registered.
- `uv run pytest tests/tools/test_check_db_separation.py`.

## Completion criteria
- AC-9 (first half): the checker reports ownership and path-key coverage for `mcp_dedup`.

## Out of Scope
- Manifest generation (row 06), the manifest itself (row 07), store DDL (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Update companion test file per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`
