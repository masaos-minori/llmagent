## Goal
Resolve `REQ-001`/`REQ-002` for ADR-001: remove the contradictory `pending`
Approval Record placeholder (and, for ADR-001/ADR-004, an existing disclaimer
sentence that directly contradicted the newly amended governance policy) and
replace it with wording consistent with the amended
`docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard.

## Scope
Modify exactly `docs/adr/ADR-001-workflow-engine-mandatory.md`'s `## Approval` > `### Approval Record` section. No other
section of this file is touched.

## Assumptions
- The governance policy amendment (target file row 11 of this Plan,
  `docs/00_governance_01_documentation-policy.md`) is applied in the same cycle,
  so this ADR's new Approval Record wording has a defined policy basis to point to.

## Design decisions
Use one fixed replacement block, identical across all 10 affected ADRs (per this
Plan's Risks section: "use one consistent replacement phrasing across all 10 files,
derived directly from the amended policy text"), to avoid per-ADR wording drift.

## Alternatives considered
Option (a) (fabricate or collect a real named Approval Record for this ADR) —
rejected at the Plan level (`REQ-003` forbids fabrication; no RACI reviewer mapping
exists to obtain a real one) — see Plan `Design` section.

## Implementation
### Target file
docs/adr/ADR-001-workflow-engine-mandatory.md

### Procedure
Replace the `### Approval Record` section's `pending` placeholder fields (and, where
present, the trailing Japanese disclaimer sentence asserting a task-level decision is
NOT acceptance evidence — now superseded by the amended policy) with a standardized
task-level-approval-decision statement.

### Method
1. Locate `### Approval Record` in `docs/adr/ADR-001-workflow-engine-mandatory.md`.
2. Replace the block through the end of the `pending` fields (and any trailing
   disclaimer sentence immediately following, up to the next `##`/`###` heading)
   with:
   ```
   ### Approval Record

   - **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
   - **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
   - **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

   本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。
   ```
3. Confirm exactly one blank line separates the new block from the following
   heading (no double blank line introduced).

### Details
ADR-001 previously had `Approved By: pending` / `Approval Date: pending` /
`Approval Reference: pending`
and a trailing disclaimer sentence stating the task-level Accepted decision must NOT be treated as a substitute for the approval record — directly contradicting Option (b)'s new standard, so this sentence is replaced, not merely appended to.

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in an Approval Record section.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `grep -c "pending" docs/adr/ADR-001-workflow-engine-mandatory.md` → the `### Approval Record` section must show zero
  `pending` occurrences (other unrelated `pending` mentions elsewhere in the file,
  if any, are out of scope).
- `.venv/bin/python tools/check_docs_quality.py docs/adr/ADR-001-workflow-engine-mandatory.md` → no new issues.

## Completion criteria
`docs/adr/ADR-001-workflow-engine-mandatory.md`'s Approval Record section no longer contains `pending` or the superseded
disclaimer sentence, and matches the standardized wording above.

## Out of scope
The other 9 ADRs and `docs/00_governance_01_documentation-policy.md` — each covered
by its own implementation procedure document for this same Plan (seq 01-10, 11).

## Documentation
This file is itself a `docs/adr/*.md` file; no separate `docs/00_index.md`
task-scope mapping applies to Approval Record content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `### Approval Record` section per Method | Completed | 2026-09-02 | 2026-09-02 | Applied via scripted replacement across all 10 ADRs, individually verified |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Run validation sequence | Completed | 2026-09-02 | 2026-09-02 | `check_docs_quality.py` reported no issues for this file (via `.venv/bin/python` fallback — `uv run` hit a transient `UnknownIssuer` TLS error reaching pypi.org) |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no separate doc |

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
- **Requirement ID**: REQ-001 (acceptance-evidence standard consistency), REQ-002 (no unresolved contradictory pending note)
- **Source issue**: `issues/20260831-191101_govdocs003_missing_approval_record_across_adrs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-223351_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-133930
- **Related target files**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
