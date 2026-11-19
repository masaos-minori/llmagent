# Make MDQ write transactions and deletion atomic and classify MDQ writes as non-retryable until proven safe

## Priority
High

## Summary
Unify transaction ownership for document, chunk, FTS5, state, and deletion changes, delete state by exact key, and make MDQ writes fail closed with a temporary non-retryable classification, using the shared dedup mechanics defined elsewhere.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 5). The shared durable-dedup redesign in this backlog item (atomic ownership, lease, heartbeat, immutable terminal rows, `review_required`, `replay_unavailable`) is already covered by `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, and required-key rejection and explicit classification by `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md`; they are not repeated here.

Evidence (`Explicit in code`, by `rg`): `index_delete.py:31` runs `DELETE FROM index_state WHERE key LIKE ?`; `config/mcp_dedup.toml:43-44` classifies `index_paths` and `refresh_index` as `retryable`; `index_write.py` writes document and chunk rows (lines 66-117) with `index_state` updated elsewhere (`Needs confirmation`). Internal commits in delete helpers, forced-refresh state, and fail-open on store failure are backlog claims and `Needs confirmation`.

## Problem
A file operation can leave partial state, deleting one filename can delete another filename's state (prefix `LIKE`), forced refresh can leave stale state, and retryable MDQ writes continue when the dedup store fails.

## Reason for Change
Data integrity and retry safety; a retry contract cannot be safe over partial database operations.

## Implementation Intent
One caller or repository layer owns the connection and transaction. One file operation is atomic across documents, chunks, trigger-driven FTS5 changes, and `index_state`. Writes are non-retryable and fail closed on dedup-store failure until operation-specific reconciliation is proven.

## Target Files or Areas
- `scripts/mcp_servers/mdq/index_write.py`, `index_delete.py`, `indexer.py`
- `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py` (classification only)
- Tests: `tests/mcp_servers/mdq/test_index_delete.py`, `test_mdq_index_serialization.py`, `test_mdq_incremental_refresh.py`; new `test_mdq_transaction_atomicity.py` and `test_mdq_index_state_consistency.py` (absent)

## Required Changes
- Remove internal commits from lower-level delete helpers; centralize connection and transaction ownership; include document, chunks, FTS5 trigger effects, and `index_state` in one file transaction; update state during forced refresh.
- Delete state by exact canonical key; define directory deletion atomicity or structured partial success; check document, chunk, FTS5, and state postconditions before success.
- Classify `index_paths` and `refresh_index` as non-retryable in the constants and the TOML together; fail closed when durable deduplication is unavailable; reconsider retryability only after operation-specific reconciliation is proven.

## Constraints
- Classification changes keep `RETRYABLE_TOOLS` and `config/mcp_dedup.toml` consistent (CI check). An ADR decision change needs a maintainer approval record (governance_01, governance_05); do not write or simulate it.
- Do not reimplement lease or ownership logic (`mcpai001`).

## Acceptance Criteria
- [ ] A failed file operation leaves no partial state.
- [ ] Deleting `a.md` cannot delete `a.md.bak` state; forced refresh leaves correct incremental state.
- [ ] MDQ writes are non-retryable and are rejected when the dedup store is unavailable.
- [ ] Postconditions are checked before success.

## Testing Expectations
- Commit, trigger, state-update, and mid-delete fault injection; shared-prefix, `%`, and `_` filenames; forced refresh then incremental refresh.
- Store-failure rejection for both write tools; retry-class consistency check.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Transaction ownership and postconditions; the temporary non-retryable classification and why.

## Out of Scope
- Dedup ownership, lease, and terminal-state mechanics (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); keyless rejection (`issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md`).

## Dependencies
- Depends on `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md` and `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`; related to `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` and `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` (shared dedup behavior this MDQ change relies on; implement MDQ transaction work independently of them).
- Blocks `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`, `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`, and `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`.

## Unresolved Questions
- `不明`: whether directory deletion should be one transaction or structured partial success.
- `不明`: where the repository layer for connection ownership should live.

## AI Implementation Instruction
Write fault-injection tests first and confirm partial state on current code. Do not touch the shared dedup state machine. Stop and report if one transaction cannot cover FTS5 trigger effects.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142127
- **Related target files**: `scripts/mcp_servers/mdq/index_write.py`, `scripts/mcp_servers/mdq/index_delete.py`, `scripts/mcp_servers/mdq/indexer.py`, `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`
