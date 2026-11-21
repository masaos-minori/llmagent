## Goal

Update `tests/db/test_schema_validation_per_database.py` so the `mcp_dedup` drift-harness entries validate the new multi-table canonical shape and the identity stamp (REQ-004, REQ-008, REQ-009; AC-9).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 01 provides the new `_CANONICAL_DDL` (`dedup_call_state`, `store_meta`, `call_attempt_history`) and the `user_version = 1` stamp; the file's existing per-domain drift matrix (missing CHECK, extra legacy table, extra column, missing index; substitute rules where a domain lacks CHECK/index) is the pattern to extend.
- The file already covers `mcp_dedup` as a domain (docstring lists rag, session, workflow, eventbus, mcp_dedup, mdq; `dedup_canonical_ddl` import at :42-43, `_entry_dedup` at :161-166, matrix entry `name="mcp_dedup"` near :217 — verified 2026-11-21): this row updates expectations, not the harness architecture.

## Design decisions
- For the new multi-table shape, the drift cases target the richest table (ledger CHECKs and indexes) and keep the baseline-vs-mutant fingerprint guard intact so no mutation degrades to a no-op.
- Add a stamp expectation: the clean baseline entry for `mcp_dedup` must reflect `user_version = 1` and a present `store_meta` row (identity is part of the canonical shape under REQ-005/REQ-006).

## Alternatives considered
- N/A: the harness structure is fixed by the file's existing matrix design.

## Implementation
### Target file
`tests/db/test_schema_validation_per_database.py`
### Procedure
Update the dedup entry's canonical source pin, drift cases, and baseline construction for the new shape.
### Method
1. Re-pin the canonical DDL expectations to the new three-table `_CANONICAL_DDL` exported by row 01.
2. Rebuild the dedup baseline construction (`_entry_dedup`) so the clean baseline is created through the store's creation path (identity + stamp) rather than raw table creation.
3. Adjust the four drift cases for `mcp_dedup` to the new shape: missing CHECK (ledger), extra legacy table (`tool_call_state` planted as the extra table), extra column, missing index; keep the documented substitute rule if any case lacks a real CHECK/index.
4. Add (or fold into the baseline case) the identity-stamp mismatch: a store missing `store_meta` or the stamp must refuse with the archive-and-recreate error.
### Details
- Current pins (verified 2026-11-21): imports `shared.mcp_dedup._CANONICAL_DDL` and `DedupStore`; `_entry_dedup` opens `DedupStore(str(path))`; entry `name="mcp_dedup"` sits in the per-database matrix around :217.
- Executed 2026-11-21: `_Domain` gained `post_build` (identity stamping for DDL-built dedup files: store_meta row + `PRAGMA user_version = 1` + installation marker) and `extra_table_ddl` (per-domain extra-table mutant; mcp_dedup plants the real pre-change `tool_call_state` table). `primary_table`/`index_snippet` re-pinned to `dedup_call_state`/`idx_dcs_updated`; `_refusal` also catches `DedupStoreError`. New `TestIdentityMismatch` covers the unstamped and identity-row-less refusals with `REFUSAL_MESSAGE` and byte-identity guards.
- Production-side deviation (row 01 file): the `schema_mismatch` stamp-drift and identity-row-less refusal messages now carry the full `REFUSAL_MESSAGE` archive-and-recreate guidance, so identity mismatches match the same operator vocabulary as fingerprint refusals.

## Compatibility considerations
- Other domains' entries are untouched; the shared fingerprint/refusal vocabulary (`REFUSAL_MESSAGE`) is unchanged.

## Security considerations
- N/A: test suite.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/db/test_schema_validation_per_database.py` (Plan Validation plan: new multi-table canonical shape validated for `mcp_dedup`).

## Completion criteria
- AC-9 (drift side): all dedup drift cases refuse with the explicit archive-and-recreate error leaving the file unchanged; the clean baseline passes.

## Out of Scope
- Canonical DDL itself (row 01), the shared fingerprint module (Reference File only), other domains.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the dedup harness entries per Implementation > Method | Completed | — | 20261121-125315 | Lands in Phase 3 Dedup domain re-pinned (dedup_call_state/idx_dcs_updated, three-table canonical), extra legacy-table mutant plants the real pre-change tool_call_state via new per-domain extra_table_ddl, post_build stamps the identity the store open requires, new TestIdentityMismatch covers stamp-missing and identity-row-less refusals. Deviation from Method 2: baseline is built from the canonical DDL text plus explicit identity stamping instead of a live store open, keeping baseline-vs-mutant fingerprint symmetry; identity requirements are asserted directly. Deviation recorded: row 01 refusal messages for stamp drift and missing identity row now embed REFUSAL_MESSAGE. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-125315 | tests/db/test_schema_validation_per_database.py 33 passed; tests/shared/ + tests/db/ 1838 passed; ruff check/format and mypy green. |

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
- **Requirement ID**: REQ-004, REQ-008, REQ-009
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tests/db/test_schema_validation_per_database.py`