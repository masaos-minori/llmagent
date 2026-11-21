## Goal

Update the `mcp_dedup.sqlite` section of `docs/41_db/db_08_active_databases.md` with identity, lease columns, start-state semantics, and the operator-resolution runbook (REQ-007, REQ-011, REQ-012; AC-10, AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Rows 01/08 have landed: the store is initialized at deploy time and carries identity; the runbook documents the implemented operation.
- Current section (verified 2026-11-21): :65-85 documents the store as `CREATE TABLE IF NOT EXISTS tool_call_state` with no identity or operator procedure; `rg` confirms neither `resolve_lost_store` nor the sentinel is documented anywhere in `docs/` — a confirmed documentation gap this row closes.

## Design decisions
- The operator runbook follows the ADR-008 archive-and-recreate idiom already used for the other databases in this file (archive `<path>.corrupt-<ts>`, then new generation), keeping one consistent operator vocabulary.
- The schema-authority line is updated to the new tables (`dedup_call_state`, `store_meta`, `call_attempt_history`) and the `user_version = 1` stamp.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/41_db/db_08_active_databases.md`
### Procedure
Rewrite the `mcp_dedup.sqlite` section and add the runbook entry.
### Method
- Lifecycle bullets: deploy-time creation (row 08), identity row + marker + stamp, lease columns, `pending`/terminal semantics.
- New runbook sub-section: detecting `lost`/`replaced`/`legacy_or_unverified`/`schema_mismatch` from logs, invoking operator resolution (generation rollover, decision log line), sentinel/marker handling, and the empty-file-alone non-resolution rule.
- Keep this file's per-database bullet format (Config source / Schema authority / Rebuild / etc.).
### Details
- The "rebuild from Markdown source" phrasing used by derived stores (mdq) must not be reused for dedup: dedup evidence is archive-only, never auto-rebuilt.

## Compatibility considerations
- Deploy operators are the audience; init_db.sh's abort messages (row 08) must match the runbook wording.

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-10/AC-11: the store section documents identity, lease columns, start states, and a complete operator-resolution runbook.

## Out of Scope
- The resolution implementation (row 01), init_db.sh behavior (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Completed | — | 20261121-125822 | mcp_dedup section rewritten: three-table schema authority (mcp_dedup_schema.py) + identity stamp, deploy-time lifecycle (init_db.sh), lease columns and terminal immutability row semantics, archive-only rebuild wording, and new operator resolution runbook subsection (start-state refusals, resolve_store 4-step rollover, empty-file-alone non-resolution rule). Deviation from Method: no sentinel handling documented (sentinel dropped, marker+generation is the only handshake). |
| 2 | Run the docs checkers (routing.md Tools) | Completed | — | 20261121-125822 | check_docs_quality.py and check_docs_structure.py both pass. |

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
- **Requirement ID**: REQ-007, REQ-011, REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/41_db/db_08_active_databases.md`