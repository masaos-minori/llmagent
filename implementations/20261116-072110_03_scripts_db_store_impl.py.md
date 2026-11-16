## Goal
- Make `SQLiteMemoryDeleteStore.delete_memories_before` return the ids its own `DELETE ... RETURNING` transaction removed via `MemoryDeleteResult(deleted_ids=tuple(deleted_ids))` (REQ-005).

## Scope
**Release unit**: maintenance-error-semantics (Phases 1-3 of the plan; lands with `20261116-072110_01`, `_02`, `_04`, `_05`)

- In scope: `delete_memories_before` (`scripts/db/store_impl.py:189-205`) result construction.
- Out of scope: the `deleted_ids` field itself (procedure `20261116-072110_02`); consuming it in `maintenance.py` (procedure `20261116-072110_01` step 5); the tests (procedure `20261116-072110_04`).

## Assumptions
- Verification finding (2026-11-16, HEAD `8fc337615`): `delete_memories_before` already collects `deleted_ids` from the `RETURNING` statement inside its `begin_immediate` transaction (`:196-205`) but discards them into a count-only `MemoryDeleteResult(deleted=len(deleted_ids))` at `:205` (plan row cites `store_impl.py:196-205`; the function spans `:189-205`).
- The fast path at `:186` returns `MemoryDeleteResult(deleted=0)` with no rows; with the field default `()` it needs no edit (Plan Assumptions).
- The internal fast-path SELECT + cross-table delete structure stays as-is; the store's own `BEGIN IMMEDIATE` is what keeps the delete atomic (Plan Design).

## Design decisions
- Return `tuple(deleted_ids)` from the existing RETURNING collection rather than a follow-up SELECT: zero extra queries, and the ids are exactly the rows the transaction deleted (AC-5).
- Keep `deleted=len(deleted_ids)` as before: the count consumers stay untouched (REQ-005).

## Alternatives considered
- Deriving ids in `maintenance.prune_old_memories` by diffing table state before/after: rejected — racy against the shared connection and not the transaction's own record (plan Problem statement).
- Wrapping `prune_old_memories` in an outer transaction: rejected — `delete_memories_before` already opens `BEGIN IMMEDIATE`; nesting raises `OperationalError` (Plan Design).

## Implementation
### Target file
`scripts/db/store_impl.py`

### Procedure
1. In `delete_memories_before`, change the success-path result construction at `:205` to `MemoryDeleteResult(deleted=len(deleted_ids), deleted_ids=tuple(deleted_ids))` (REQ-005). No other statement in the transaction changes.
2. Leave the fast path at `:186` (`MemoryDeleteResult(deleted=0)`) untouched — the field default `()` applies.

### Method
- Single-expression edit inside the existing transaction block; no new imports; no import-edge change (Plan Architecture check).

### Details
- Sequence dependency: `20261116-072110_02` (field addition) must land first; both are in the same release unit and the same commit batch.
- `delete_memories_before` has exactly one production caller (`maintenance.py:401`) plus `tests/db/test_db_store_impl.py` (REQ-005 blast radius confirmed 2026-11-16).
- Sequence context: Plan 008 later extends `store_impl.py` retention paths; it edits no region this document lands.

## Compatibility considerations
- Return type is the same class, extended; `MemoryDeleteStore` protocol signature unchanged (Plan Assumptions).
- `tests/db/test_db_store_impl.py` constructions/assertions of the result stay green: `deleted` semantics unchanged; `deleted_ids` is additive.

## Security considerations
- No new attack surface; the RETURNING statement is already parameterized (bandit baseline 45 low / 0 medium / 0 high unchanged).

## Rollback considerations
- `git checkout` revert of the unit commit. Part of release unit maintenance-error-semantics — revert together with `_01`, `_02`, `_04`, `_05`.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py tests/db/test_db_maintenance.py -v` → the AC-5 id-source test from `20261116-072110_04` asserts `sorted(data["pruned_ids"])` equals the ids removed from the `memories` table (post-run table state).
- `uv run pytest tests/ -n auto` → no regressions (store used by maintenance and agent memory commands).
- `uv run ruff check scripts/db/store_impl.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form), `uv run lint-imports` → clean.

## Completion criteria
- A successful `delete_memories_before` returns `deleted_ids` equal to the ids its `RETURNING` statement yielded, in transaction order, and `deleted == len(deleted_ids)`; the fast path still returns `deleted=0` with `deleted_ids == ()`; the full suite is green.

## Out of Scope
- The field declaration and protocol docstring (procedure `20261116-072110_02`).
- Dropping `collect_prunable_ids` from `prune_old_memories` (procedure `20261116-072110_01` step 5).
- Tests (procedure `20261116-072110_04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Populate `deleted_ids` in the result construction (plan Phase 2) | Pending | — | — | REQ-005; after `_02` lands |
| 2 | Add or update tests per Validation plan | N/A | — | — | tests land via `20261116-072110_04` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no doc in this row's scope |

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
- **Requirement ID**: REQ-005 (`deleted_ids` population from `DELETE ... RETURNING`)
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-072110
- **Related target files**: scripts/db/store_impl.py
