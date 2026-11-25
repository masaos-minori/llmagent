## Goal
Add `args_hash` to the `tool_call_state` column contract in the DB schema-reference sub-document.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The document names `scripts/db/schema_sql.py::build_workflow_schema_sql` as the canonical source, so the entry
  states the column and points to that source rather than restating the DDL.

## Design decisions
- One column entry in the existing contract list; no new section.

## Alternatives considered
- Documenting the column in the Agent-side persistence sub-document — rejected: the column contract has one
  normative home, the DB schema-reference sub-document.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
Add the `args_hash` column to the `tool_call_state` column definitions.

### Method
State the column as `TEXT NOT NULL`, populated by the write path, and note that it is the value replay-directive
reconstruction reads at turn entry.

### Details
- Keep the existing paragraph about the retired `execution_snapshots` table and the fingerprint gate unchanged; the
  new column does not change the gate's behavior, only the shape it compares.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain db`
- `uv run python tools/check_db_separation.py` — table ownership unchanged (`rules/tool-gates.md`)

## Completion criteria
The column contract lists `args_hash` and the docs gates pass.

## Out of Scope
No change to the retired-table paragraph or to the `mcp_dedup.sqlite` sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `args_hash` to the column contract | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (the persisted column contract)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
