## Goal
Align the guide's repair table and prose with the repair actions (REQ-003) and, after the recorded decision, its startup section (REQ-007).

## Scope
**Release unit**: rag-diagnostics
- The `Repair Decision Flow` table, the Degraded row of `Severity Classes`, and the closing repair paragraph; after the decision, the `Startup Warnings` bullets.
- Release unit: the failing-first tests stay red until procedure 02 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- Procedure 02 is done, so the table describes the code. The mapping is the Source plan default (UNK-02).
- ADR-005 names this guide as the owner of the startup policy; the decision is recorded in ADR-004, so the guide keeps describing the behavior and points to ADR-004 for the classification.

## Design decisions
- Describe what the code does; keep the policy statement in ADR-004 and refer to it.

## Alternatives considered
N/A: the guide follows the code and the recorded decision.

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
### Procedure
1. Repair table: the `orphan_vec_count > 0` row keeps `rebuild_vec` and says `Run /session rag-rebuild-vec` (it removes `chunks_vec` rows with no matching `chunks` row; the command is not per URL); the vector count, chunks-without-vector, documents-without-chunks, and URL-level rows use `reingest` with `Run ingester.py --force` for the affected URLs, chunks, or documents.
2. `Severity Classes`: the Degraded repair cell lists `rebuild_fts`, `rebuild_vec`, or `reingest`; the closing paragraph says `rebuild_fts` and `rebuild_vec` repair only the findings that name them, `reingest` findings need ingestion to run again, and fatal findings require restore-from-backup or re-ingest.
3. Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text. Then update the `Startup Warnings` bullets for degraded findings and for a failed or timed-out check so they describe the decided classification in one sentence and name ADR-004 as its owner; keep the description of what startup does.
### Method
Edit the table rows and bullets in place; keep the table structure and the code fence example.
### Details
- Do not copy concrete values (timeouts, ports) into the guide.
- Fatal rows already say to restore from a verified backup; leave them.

## Compatibility considerations
N/A: documentation follows the code.

## Security considerations
N/A: documentation-only change; no policy decision is written by the implementer.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain rag`

## Completion criteria
- The table and prose match the repair actions and messages (AC-3).
- The startup bullets follow the recorded decision (AC-7).

## Out of Scope
- Writing the policy decision.
- Changing the code or ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align the repair table and the severity class prose (REQ-003) | Completed | 20261118-130548 | 20261118-130556 | Repair table, severity class cell, and closing paragraph aligned with the repair actions (reingest, rebuild_vec for orphan rows only); changed: docs/21_rag/rag_05_07-rag-index-consistency-checks.md |
| 2 | Confirm the maintainer decision (UNK-01) | Completed | 20261118-130556 | 20261118-130556 | Maintainer decision UNK-01 recorded in session 2026-11-18 via AskUserQuestion: option A (availability failure) |
| 3 | Update the Startup Warnings bullets (REQ-007) | Completed | 20261118-130556 | 20261118-130556 | Startup Warnings bullets for degraded findings and for a failed or timed-out check say ADR-004 classifies them as availability failures (the ADR-004 text is the pending amendment of procedure 06) |
| 4 | Run the documentation checkers listed in Validation plan | Completed | 20261118-130556 | 20261118-130556 | docs quality/structure/content-policy/japanese and check_docs_consistency --domain rag: pass |

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
- **Requirement ID**: `REQ-003`: guide matches the repair actions; `REQ-007`: guide follows the decision
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
