# Implementation Procedure: docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md

## Goal

Create the DB-domain doc for the new stores: both workflow lifecycle tables, the standalone
`mcp_dedup.sqlite` bootstrap and retention, and the replay decision table (REQ-002 store
contract documented; REQ-007 tables documented; plan AC-2).

## Scope

**In scope:**
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (new).

**Out of scope:**
- Transport/agent-facing docs (rows 11, 13).

## Assumptions

- Needs Confirmation (naming): `docs/41_db/` currently uses a flat `db_NN_<category>-<slug>`
  scheme (`db_01` … `db_08`); `db_03_07_...` is the frozen path from the plan and does not
  match that scheme. Keep the frozen path (the batch does not amend frozen tables silently);
  if the docs index checker or the owner rejects the name, rename in the same commit and
  update the plan's table row + this doc's Traceability together.
- Registration: check whether `docs/00_index.md` requires an entry for new files under
  `41_db/` (existing 41_db docs appear there as task-mapping rows); if so, add the entry
  in this row's edit — it is part of the same target-file family only if the checker
  demands it; otherwise leave the index untouched (frozen table has no index row).

## Design decisions

- Sections: (1) `mcp_dedup.sqlite` — standalone-file decision (UNK-02), `PRAGMA
  user_version` bootstrap, WAL/busy-timeout concurrency contract, result size cap +
  result-hash rule, retention sweep semantics (REQ-002/REQ-009); (2) `tool_call_state` (new) +
  `execution_snapshots` (new) DDL contract summary and their workflow.sqlite ownership
  (REQ-007); (3) replay decision table — the four REQ-005 outcomes
  (completed+match / completed+mismatch / interrupted+retryable /
  interrupted+non_retryable) with the resulting action and audit tag; (4) future dbmig001
  adoption path note (UNK-02 record).
- Operational/failure semantics only (`skills/DESIGN.md` Docs content policy) — no code
  listings beyond one DDL block.

## Alternatives considered

- Folding this content into `db_02` (schema reference) — rejected: the frozen plan
  specifies a dedicated doc; `db_02` stays a per-DB inventory.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (new)

### Procedure
1. Write the four sections above against the landed contracts of rows 02, 04, 06.
2. Cross-link rows 11 and 13 docs and `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
   for the standalone-file rule.

### Method
Docs prose + one DDL block matching row 06 exactly (copy columns verbatim after landing).

### Details
- The replay decision table is the doc's anchor artifact — it is what ops reads when a
  call "wasn't re-run".

## Compatibility considerations

- Must not contradict `db_01` overview or `db_08` active-databases list: if `db_08`
  enumerates live DB files, its update belongs to whichever row owns it — Needs
  Confirmation (no frozen row covers `db_08`; flag at implementation time).

## Security considerations

- N/A: schema/ops documentation only.

## Rollback considerations

- N/A: revert the commit (file deletion, single file).

## Validation plan

- Docs checkers per `routing.md` Tools (index/structure + stale detector) after rows
  02/04/06 land.

## Completion criteria

- The doc exists at the frozen path (or the confirmed rename), describes both stores and
  the four-outcome replay table matching shipped code, and passes the docs checkers.

## Out of Scope

- Transport semantics (row 11), agent turn semantics (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the new doc after rows 02/04/06 land | Pending | — | — | Naming + index registration per Assumptions |
| 2 | Run the docs validation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (dedup store contract), `REQ-007` (workflow tables), `REQ-009` (retention)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md
