## Goal
Satisfy `REQ-001` (ptip001): add a one-time-per-pass instruction to
`skills/plan-to-implementation-procedure/workflow.md`'s Procedure-Specific Guidance for Step 3,
so the `implementations/`/`implementations/done/` directory listing is captured once per pass
and updated in-memory rather than re-scanned per row.

## Scope
Modify exactly the first bullet of the `## Procedure-Specific Guidance` section (current lines
311-315) of `skills/plan-to-implementation-procedure/workflow.md`. No other line in this file
is touched.

## Assumptions
- Re-verified 2026-09-02: lines 311-315 still read exactly as the Plan's evidence describes —
  no drift since Plan creation.

## Design decisions
Add both a caching rule (capture the listing once at the start of the row-processing loop) and
an explicit invalidation rule (update the in-memory listing, not by re-scanning, when this same
pass writes a new file for an earlier row), mirroring `itp008`'s general "repeated identical
command" finding applied to this concrete case (Plan `Design`).

## Alternatives considered
Leaving the per-row scan as-is and relying on `rules/ai-execution.md` Tool Usage's general
"do not repeat a command when neither its input nor the environment has changed" — rejected:
the Plan's Problem notes that rule alone does not state how to handle the one case where the
environment *does* change mid-pass (this same pass writing a new file for an earlier row), so
an explicit invalidation rule is still needed here.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Reword the first Procedure-Specific Guidance bullet to add the caching and invalidation
instruction.

### Method
1. Locate lines 311-315 (current):
   ```
   - In Step 3, check "already implemented" status by first matching `target_file_slug`
     against file names under `implementations/` and `implementations/done/` as a cheap
     filter; only when a name matches, read that matched file's content (not the full
     target source file) to confirm its stated scope actually covers the current row
     before deciding to skip.
   ```
2. Append to the same bullet (or as an immediately-following bullet):
   ```
     Capture the `implementations/` and `implementations/done/` directory listing once at
     the start of Step 3's row-processing loop, and reuse it for every row's filter check
     rather than re-scanning the filesystem per row. If this same pass writes a new file for
     an earlier row, update the in-memory listing to include it (do not re-scan the
     filesystem) before checking any later row against it.
   ```

### Details
This does not change the classification criteria themselves (`Already implemented` /
`Partially implemented` / `Not implemented`, Plan Scope Out-of-Scope) — only how many
filesystem scans are performed and how the in-pass cache is kept current.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure efficiency clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added instruction does not change the classification outcome for any row, only how many filesystem scans are performed (Plan `Tests`).

## Completion criteria
The Procedure-Specific Guidance states the directory listing is captured once per Step 3 pass,
with an explicit invalidation rule for files the same pass writes.

## Out of scope
Changing the `Already implemented` / `Partially implemented` / `Not implemented`
classification criteria themselves (Plan Scope Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add caching/invalidation instruction per Method | Completed | 2026-09-02 | 2026-09-02 | Target sentence found at line 317-321 (shift from cited 311-315 due to prior edits in this cycle, within tolerance); content matched exactly |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed classification criteria (Already/Partially/Not implemented) unchanged; only scan cadence affected |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001 (one-time-per-pass directory listing with invalidation rule)
- **Source issue**: `issues/20260901-171500_ptip001_already_implemented_check_repeats_directory_scan.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212811_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152708
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
