## Goal
Remove ADR-004's redundant file/class/config/test list from `## Implementation Notes`
once reconciled into `### Implementation References`, per `REQ-004`, while leaving
this ADR's two non-list caveat bullets untouched.

## Scope
- In scope: verify and add the 2 cited test files to References; delete only the
  4-item list from Notes.
- Out of scope: the two caveat bullets (memory-only `StartupValidationResult`
  aggregate; fixed-delay single-retry health check) — already classified as
  "Accepted current specification" (no design/decision requirement violated) in
  this session's earlier `plans/done/20260915-145322_plan.md` REQ-007 — survive
  unchanged. The `## Known Deviations` section this ADR now has (added in that
  same earlier Plan) is also untouched.

## Assumptions
- No pointer line is needed — the section remains non-empty (the two caveat
  bullets survive).
- ADR-004 was restructured earlier this session (a `## Known Deviations` section
  was added, moving what used to be a duplicate `## Alignment with INV-01/INV-02`
  heading). Line numbers recorded in the Plan (450-453 for the Notes list, 580-585
  for References) reflect that restructured state as of Plan creation — re-confirm
  via `grep` before editing, since this is the ADR most recently touched in this
  session's history and most likely to have drifted further.

## Design decisions
- Files/symbols in Notes already match References exactly (confirmed during Plan
  creation) — this row requires only test-citation reconciliation.

## Alternatives considered
- Re-open the REQ-007 classification of the two caveat bullets while this file is
  open — rejected; that classification was already made and validated in
  `plans/done/20260915-145322_plan.md`, re-litigating it is out of this Plan's
  scope (Plan Scope explicitly cross-references that completed work).

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
1. Re-verify current line numbers via `grep -n "^## Implementation Notes\|^### Implementation References\|^## Known Deviations"` — confirm the Notes list, the two caveat bullets, and References' current positions before editing.
2. Verify the 2 cited test files exist via `ls`; correct paths if stale.
3. Add the verified test files to `### Implementation References` as a new bullet.
4. Delete only the 4-item bulleted list from `## Implementation Notes` — do not touch the two caveat bullets that follow it, or the `## Known Deviations` section.

### Method
Use `Edit` (exact-string replacement) — one call for step 3, one for step 4.

### Details
- The two caveat bullets ("StartupOrchestratorが構築する... メモリ上の集約
  オブジェクトであり..." and "MCPサーバー到達不能時の現行の再試行は、固定遅延...")
  must remain byte-for-byte unchanged.
- No pointer line is inserted — section stays non-empty via the two caveats.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-004-environment-failure-handling-policy.md` if
validation fails. Note this file already carries this session's earlier,
already-committed `## Known Deviations` restructuring — a rollback here must not
revert that unrelated, already-landed change; scope any revert to only this
procedure's own edit.

## Validation plan
- `ls <the 2 test files>` — must resolve before adding.
- Manual diff: confirm Notes list removed, both caveat bullets and `## Known Deviations` unchanged.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-004-environment-failure-handling-policy.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md` — record the known 9-finding pre-existing baseline (per `plans/done/20260915-145322_plan.md` Design), confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- `## Implementation Notes` contains only the two caveat bullets plus boilerplate (no list).
- `### Implementation References` includes both test files.
- All Validation plan checks pass (or no new finding beyond the 9-finding baseline).

## Out of scope
- The two caveat bullets, `## Known Deviations`, and any other ADR-004 section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162609 | Added 2 tests to References; deleted Notes list only (2 caveat bullets preserved, no pointer inserted per procedure) |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162609 | 20260915-162609 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162609 | 20260915-162609 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 9 pre-existing findings matching the already-established ADR-004 baseline from plans/done/20260915-145322_plan.md |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162609 | 20260915-162609 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-004 — reconcile test citations, delete Notes list only
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md