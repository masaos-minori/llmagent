## Goal
- Extend the frozen `MemoryDeleteResult` dataclass in `scripts/db/store_protocols.py` with `deleted_ids: tuple[str, ...] = ()` so the delete transaction's ids can become the single source of reported prune ids (REQ-005).

## Scope
**Release unit**: maintenance-error-semantics (Phases 1-3 of the plan; lands with `20261116-072110_01`, `_03`..`_05`)

- In scope: the `MemoryDeleteResult` field addition and the protocol docstring statement that `deleted_ids` is the authoritative report.
- Out of scope: populating the field (`scripts/db/store_impl.py`, own procedure `20261116-072110_03`); consuming it (`scripts/db/maintenance.py`, procedure `20261116-072110_01` step 5); the tests (own procedure `20261116-072110_04`).

## Assumptions
- Verification finding (2026-11-16, HEAD `8fc337615`): `MemoryDeleteResult` is the frozen dataclass at `store_protocols.py:144-148` with the single field `deleted: int` (plan row cites `:145-149`; the class body binds at `:144-148` — no functional difference).
- A defaulted field breaks no existing construction: constructions exist only at `store_impl.py:186` (fast path `MemoryDeleteResult(deleted=0)`) and `:205`, plus the `scripts/db/__init__.py` re-export (Plan Assumptions, grep this cycle).
- `MemoryDeleteStore` protocol method signature stays unchanged — the return type is the same class, extended.

## Design decisions
- Default `()` rather than a required argument: keeps the fast path (`store_impl.py:186`) and any external constructor valid without edits (Plan Design).
- Type `tuple[str, ...]`: immutable result data per the repo's immutability default (`skills/python-design` Design for immutability); `maintenance` converts to `list[str]` when building `data["pruned_ids"]` so the consumer shape stays identical.

## Alternatives considered
- Replacing `deleted: int` with `deleted_ids` only: rejected — all current consumers read `deleted` (`maintenance.py`, `memory_data_ops.py` count paths); the plan keeps both fields (REQ-005).
- Making the field required: rejected — breaks the fast-path construction and any third-party implementation of the protocol (Plan Design).

## Implementation
### Target file
`scripts/db/store_protocols.py`

### Procedure
1. Add `deleted_ids: tuple[str, ...] = ()` to `MemoryDeleteResult` (`:144-148`), after `deleted: int` (REQ-005).
2. State in the `MemoryDeleteStore.delete_memories_before` docstring (or the dataclass docstring) that `deleted_ids` is the authoritative record of rows removed by the delete transaction, and that a store which does not populate it reports an empty tuple (Plan Risks mitigation for third-party stores).

### Method
- Two-line-scale edit in the existing dataclass; no new imports; no import-edge change (Plan Architecture check).

### Details
- Frozen dataclass semantics unchanged: `deleted_ids` is a tuple, so the instance stays hashable/immutable.
- The fast path (`store_impl.py:186`) and `scripts/db/__init__.py` re-export need no change in this document.

## Compatibility considerations
- Default value keeps every existing `MemoryDeleteResult(...)` construction valid (grep this cycle: `store_impl.py:186,205` are the only constructions).
- basedpyright/mypy: the extension is additive; consumers that only read `.deleted` are unaffected.

## Security considerations
- No new attack surface; bandit baseline 45 low / 0 medium / 0 high unchanged.

## Rollback considerations
- `git checkout` revert of the unit commit. Part of release unit maintenance-error-semantics — revert together with `_01`, `_03`..`_05`; reverting this field alone would break `_03`/`_01` step 5.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py tests/db/test_db_maintenance.py -v` → constructions and the new `deleted_ids` assertions from `20261116-072110_04` pass (AC-5).
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form per `rules/toolchain.md`) → no new errors in `store_protocols.py`.
- `uv run ruff check scripts/db/store_protocols.py`, `uv run lint-imports` → clean.

## Completion criteria
- `MemoryDeleteResult` has `deleted_ids: tuple[str, ...] = ()`; all existing constructions compile unchanged; the protocol/datastring names `deleted_ids` as the authoritative report; `uv run pytest tests/ -n auto` green.

## Out of Scope
- Population of `deleted_ids` from `DELETE ... RETURNING` (procedure `20261116-072110_03`).
- Consumption in `prune_old_memories` (procedure `20261116-072110_01` step 5).
- Tests (procedure `20261116-072110_04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `deleted_ids` field + docstring statement (plan Phase 2) | Pending | — | — | REQ-005 |
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
- **Requirement ID**: REQ-005 (`MemoryDeleteResult.deleted_ids` field)
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-072110
- **Related target files**: scripts/db/store_protocols.py
