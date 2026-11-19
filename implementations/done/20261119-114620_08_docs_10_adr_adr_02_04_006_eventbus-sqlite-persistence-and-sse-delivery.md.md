## Goal
- Add the authorization sweep task state and its two health reasons to the ADR-006 Runtime Monitoring bullets (REQ-007: the monitoring list matches the health contract), without changing any decision.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the "Health Check" and "Alert conditions" bullets of the Runtime Monitoring section in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`. Depends on the seq 02 document.

## Assumptions
- A wording or evidence edit does not reopen ADR approval (`docs/00_governance/governance_01_documentation-policy.md`); Decision Details, Invariants, Approval, and Known Deviations stay unchanged (Plan UNK-03).
- The file is 31126 bytes against a 32768-byte limit, so the edit MUST add well under 1000 bytes (the ADR-013 edit of the previous Plan hit the limit by 39 bytes).

## Design decisions
- Extend the two existing bullets in place; add no new section.

## Alternatives considered
N/A: a two-bullet wording update.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. In the "Health Check" bullet, add "authorization sweep task state" after "DLQ task state".
2. In the "Alert conditions" bullet, add `authz_sweep_task_stopped` and `authz_sweep_failing` after `dlq_task_stopped`.

### Method
- One short insertion per bullet; keep the list punctuation and the surrounding bullets byte-identical.

### Details
- Run `uv run python tools/check_adr_preservation.py` after the edit: expect at most a wording warning on the monitoring text, and no change to a Decision Detail, Invariant, Approval, or Known Deviations entry; if it reports one, undo and ask.
- Run `wc -c` on the file; it MUST stay below 32768 bytes.

## Compatibility considerations
N/A: documentation only; the Invariant matrix is unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_preservation.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`; `check_docs_quality.py`, `check_docs_structure.py docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.

## Completion criteria
- Both bullets name the sweep task and reasons, no decision text changed, the file is within the size limit, and all checkers pass.

## Out of Scope
- Decision Details, Invariants, and any other section of the ADR.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the two Runtime Monitoring bullets | Completed | 20261119-120306 | 20261119-120328 | Step 2 stale check clean; Step 3a: Runtime Monitoring bullets verified; file 31126 bytes (limit 32768); clean at baseline Changed: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md (two Runtime Monitoring bullets; 31126 to 31209 bytes, limit 32768) |
| 2 | Run the documentation and ADR checkers named in `routing.md` Tools | Completed | 20261119-120328 | 20261119-120328 | adr structure/preservation/matrix/reference/authority and docs quality/structure/content-policy strict/japanese/consistency eventbus all pass; check_adr_preservation: no issues, so no approval record needed (Plan UNK-03 resolved) |

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
- **Requirement ID**: `REQ-007` (monitoring list matches the health contract)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`