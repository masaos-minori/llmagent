## Goal
Remove ADR-002's redundant file/class/config/test list from `## Implementation Notes`
once reconciled into `### Implementation References`, per `REQ-002`, while leaving
the section's non-standard `### CI-001` Known Issue block untouched.

## Scope
- In scope: verify and add the 2 cited test files to References; delete only the
  4-item list from Notes.
- Out of scope: the lead-in sentence ("ADRと現行実装、設定、テスト、文書に差異が
  ある場合に記載する。"), the `### CI-001` block, and the boilerplate lines — all
  survive unchanged. Restructuring ADR-002 to have a separate `## Known Deviations`
  heading (its `### CI-001` currently lives directly inside `## Implementation
  Notes`) is `UNK-01` in the Plan — out of scope for this document.

## Assumptions
- No pointer line is needed — the section remains non-empty after deletion (the
  lead-in sentence and `### CI-001` block survive).
- The 2 test file paths (`tests/shared/test_config_loader.py`,
  `tests/agent/test_config_permission_cross_server.py`) were not independently
  `ls`-verified during Plan creation (`UNK-02`) — verify them in this procedure
  before adding to References.

## Design decisions
- Files/symbols in Notes already match References exactly (confirmed during Plan
  creation) — this row requires only test-citation reconciliation, no
  file/symbol correction.

## Alternatives considered
- Restructure `### CI-001` into a proper `## Known Deviations` heading while this
  file is open — rejected as scope creep; `UNK-01` explicitly defers this to a
  separate, narrowly-scoped issue.

## Implementation
### Target file
`docs/adr/ADR-002-config-isolation.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   352-355 and the lead-in sentence / `### CI-001` block follow at 357+ (content
   may have shifted since this procedure was generated).
2. Verify `tests/shared/test_config_loader.py` and
   `tests/agent/test_config_permission_cross_server.py` both exist via `ls` — if
   either path is stale, locate the correct current path via `find`/`rg` before
   proceeding (do not add an unverified path to References).
3. Add the verified test file(s) to `### Implementation References` as a new
   bullet (References currently has no test citation for this ADR).
4. Delete only the 4-item bulleted list (実装ファイル / 主要ClassまたはFunction /
   設定ファイル、設定Key / 対応するテスト) from `## Implementation Notes` — do
   not touch the lead-in sentence or the `### CI-001` block that follow it.

### Method
Use `Edit` (exact-string replacement) — one call for step 3, one for step 4.

### Details
- Do not insert a one-line pointer — the section is non-empty after this edit
  (lead-in sentence + `### CI-001` remain), so no placeholder is needed per the
  Plan's Assumptions.
- Preserve the `### CI-001` block's every field (Known Issue, Type, Summary,
  Conflicting Source, Expected Design, Observed Implementation, Impact,
  Recommended Action, Owner, Status, Resolution Target) exactly as-is.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-002-config-isolation.md` if validation fails.

## Validation plan
- `ls tests/shared/test_config_loader.py tests/agent/test_config_permission_cross_server.py` — both must resolve before adding to References.
- Manual diff: confirm `## Implementation Notes` no longer contains the 4-item list but retains the lead-in sentence and `### CI-001` block unchanged.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-002-config-isolation.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-002-config-isolation.md` — record pre-existing baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — expect zero findings.

## Completion criteria
- `## Implementation Notes` no longer contains the file/class/config/test list;
  lead-in sentence and `### CI-001` block are unchanged.
- `### Implementation References` includes both verified test files.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Restructuring `### CI-001` into a `## Known Deviations` heading (`UNK-01`).
- Any other section of ADR-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162340 | Verified 2 test paths exist, added to References; deleted Notes list only (lead-in sentence + CI-001 block preserved, no pointer inserted) |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162340 | 20260915-162340 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162340 | 20260915-162340 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 6 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162340 | 20260915-162340 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-002 — reconcile test citations, delete Notes list only
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-002-config-isolation.md