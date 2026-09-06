## Goal
Mark `GV-003` (Unique ADR ID) "Existing" and add a new Governance Verification
Matrix row for `tools/check_canonical_source_conflicts.py`'s remaining REQ-001 gap —
only after seq 05's CI wiring is confirmed active (REQ-011).

## Scope
- In scope: the `GV-003` row (currently line 300, status "Missing") and adding one
  new row after `GV-022` (currently line 316).
- Out of scope: `GV-022` itself (already exists, already cites
  `check_canonical_source_conflicts.py`, `Status: Existing`) — not modified by this
  row, but see Assumptions for a significant discrepancy found regarding it.

## Assumptions
- **Significant discrepancy found this cycle (2026-09-06)**: `GV-022` ("Canonical
  source conflict routing and deduplication", line 316) already states `Status:
  Existing` — but row 01 and seq 05 (this Plan's own procedure documents, generated
  this same cycle) confirm `tools/check_canonical_source_conflicts.py` is **not**
  fully functional yet (REQ-001's registry-wrapping is dead code; the tool silently
  finds zero conflicts against the real registry due to a parsing failure) and is
  **not yet wired into CI** (seq 05 confirms `governance-docs-consistency.yml` has
  no reference to it). `GV-022`'s current "Existing" status therefore appears to be
  exactly the kind of premature claim `GV-016` ("No unimplemented auto-checks
  documented as implemented") exists to catch — likely written by whichever
  concurrent session created the tool, before its own remaining gaps (this Plan's
  REQ-001/REQ-010) were discovered. This row does not correct `GV-022` itself (it is
  not one of this Plan's Implementation Target Files — correcting it would be an
  additional-target-file discovery requiring its own Plan amendment per
  `rules/workflow-lifecycle.md`), but flags it prominently for a human/coordinator
  decision, since leaving a self-contradictory Matrix (one row "Existing" for a tool
  this Plan's own new row calls "not yet CI-wired") would itself be a fresh
  documentation-governance inconsistency.
- This row's own new entry must not repeat `GV-022`'s premature-status mistake —
  its `Status` column reflects the **actual** state (CI wiring pending on row 01),
  not an aspirational one.

## Design decisions
- Use `GV-024` for the new row (not `GV-023`) — confirmed via `grep -n "GV-[0-9]"
  docs/00_governance_04_documentation-checks.md` this cycle that the highest
  existing number is `GV-022`, and a sibling Plan's own already-generated procedure
  document (`implementations/20260906-150039_05_docs_00_governance_04_documentation-checks.md.md`,
  `M-01-04`'s Plan) already proposes `GV-023` for its own new row — using `GV-024`
  here avoids a collision; re-confirm both numbers are still free at implementation
  time in case a third concurrent session has claimed one.

## Alternatives considered
- Reuse `GV-022` for this Plan's own status update instead of adding a new row:
  rejected — `GV-022` is not this Plan's target file/row to modify (Scope), and its
  own content already describes the tool generically; this Plan's new row instead
  tracks specifically the REQ-001/REQ-010 gap this Plan closes, which is a narrower,
  more precise concern than `GV-022`'s broad "routing and deduplication" framing.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Confirm seq 05's CI wiring is actually active (re-run a workflow trigger, or at
   minimum confirm the step exists in the merged workflow file and ran successfully
   at least once) before making any edit in this row — per REQ-011's explicit
   ordering requirement.
2. Update `GV-003`'s row (line 300): change `Status` from "Missing" to "Existing",
   `Follow-up` from "Implement" to "None".
3. Add a new row after `GV-022` (line 316):
   `| GV-024 | Canonical source registry schema wrapping (missing/invalid source,
   unknown claim type, Draft/Proposed normative source) | Pol | Auto |
   check_canonical_source_conflicts.py | PR | Blocking | Existing | None |` —
   adjust `Status` to "Existing" only if step 1's confirmation actually passed;
   otherwise this row's own Execution Status must remain `Blocked`, not silently
   proceed.
4. Update the "Follow-up Work Needed" numbered list (around line 322-345): remove
   or update item 2 ("GV-003: Implement Unique ADR ID enforcement") since it is now
   resolved.
5. Flag `GV-022`'s premature "Existing" status (Assumptions) in this row's own
   completion report as a candidate correction for a human/coordinator to action —
   do not edit `GV-022` itself in this row.

### Method
Confirmed this cycle (2026-09-06) via direct read: `GV-003` at line 300 ("Missing"/
"Implement"); `GV-022` at line 316 ("Existing"/"None", citing
`check_canonical_source_conflicts.py`); highest existing `GV-` number is 022; a
sibling Plan's own procedure document already proposes `GV-023` (confirmed via
direct read of
`implementations/20260906-150039_05_docs_00_governance_04_documentation-checks.md.md`,
this same session).

### Details
No change to any other Matrix row.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py` flags an
issue, or if step 1's CI-active confirmation later turns out to have been
premature (re-open `GV-003`/the new row back to "Missing"/appropriate status rather
than leaving a false "Existing" claim standing).

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
- Manual re-confirmation that the CI step (seq 05) actually ran and passed before
  this row's edit is made — not merely that the workflow file contains the step.

## Completion criteria
- `GV-003`'s status is "Existing" only if genuinely implemented (row 02 of this
  Plan, `tools/check_docs_structure.py`'s ADR-ID check) — re-verify against that
  row's own completion, not assumed from this row alone.
- A new `GV-024` row exists, accurately reflecting whether CI wiring (seq 05) is
  actually active at the time of this edit.
- `GV-022`'s discrepancy is flagged in this row's completion report, not silently
  absorbed or auto-corrected.

## Out of scope
- `GV-022` itself — not this Plan's target file; flagged for separate
  human/coordinator action.
- Any other Matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked — depends on seq 05's CI wiring being confirmed active first |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on seq 05 (CI wiring), which itself depends on row 01 (schema reconciliation) — neither has landed as of 2026-09-06 | No | — |
| 2 | `GV-022` already states `Status: Existing` for a tool this Plan's own investigation found is not yet fully functional or CI-wired — a likely premature status claim outside this row's own target scope to fix, flagged for human/coordinator review | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: issues/20260903-103028_m0105_implement-canonical-source-validation-and-ci-enforcement.md
- **Source plan**: plans/20260905-165817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150421
- **Related target files**: docs/00_governance_04_documentation-checks.md
