## Goal
Add new Known Issues (Part 1) and/or Needs Confirmation (Part 2) entries to
`docs/00_governance_03_issue-and-uncertainty-management.md` for any bullet the other 20
rows of this Plan classify as `Move to Known Issues` or `Move to Needs Confirmation`
(REQ-004, REQ-005). This row's own action is entirely conditional on those other rows'
outcomes.

## Scope
In scope: adding new entries to Part 1/Part 2 of this file, one per bullet routed here by
another row. Out of scope: this file's other sections (Part 3 Canonical Source Conflict,
Part 4 Configuration Drift, Resolution Rules, Temporary Exception Process); editing or
removing any existing Known Issues/Needs Confirmation entry not related to this Plan.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's Part 1
`### Entry Template` (line 19) and Part 2 `### Inventory Entry Fields` (line 522) both
exist as expected. Based on the other 20 rows' content read during this same pass, at
least 2 rows are expected to route content here:
- `docs/03_rag_04_04_dto-models_config.md` (row 16) — likely `Move to Known Issues`, a
  documented-vs-actual-runtime-contract mismatch.
- `docs/03_rag_05_4-error-handling-reference.md` (row 19) — likely `Move to Known
  Issues`, an acknowledged undocumented exception-hierarchy fragmentation.
`docs/03_rag_05_3-logging.md` (row 18) may also route a `Needs Confirmation` entry here
depending on that row's own step 1 finding. This list is provisional — the actual
determinant is each source row's own classification outcome, not this row's advance
guess; do not add an entry here for a bullet whose source row did not, in fact, resolve
to `Move to Known Issues`/`Move to Needs Confirmation`.

## Design decisions
This row has no classification decision of its own to make — it only receives the
outcome of other rows' classification (REQ-001/REQ-002's own Decision Categories
application happens in each source file's own procedure document). Per
`skills/python-design/SKILL.md`'s "Validate only at system boundaries": this document
validates that an incoming entry actually follows the Entry Template/Inventory Entry
Fields shape before accepting it — it does not re-derive or second-guess the source
row's classification choice.

## Alternatives considered
N/A: this row's action (add entries per the Entry Template) is fixed by REQ-004/REQ-005
— no alternative destination applies.

## Implementation
### Target file
docs/00_governance_03_issue-and-uncertainty-management.md

### Procedure
1. Process rows 1-20 of this Plan first (in their own table order) — this row's content
   depends entirely on their outcomes, so it must be processed last among the 21 rows.
2. For each bullet another row classified `Move to Known Issues`, add one new entry to
   Part 1 following the `### Entry Template` (line 19) exactly — Status/Type/Severity/
   Owner/Area values per that section's own enumerated Status/Type/Severity/Owner/Area
   Values subsections.
3. For each bullet another row classified `Move to Needs Confirmation`, add one new
   entry to Part 2 following `### Inventory Entry Fields` (line 522) exactly.
4. Before adding any entry, check whether an equivalent entry already exists (e.g. for
   `docs/adr/ADR-015-reference-document-class-disposition.md`'s Memory `UNK-01`
   cross-reference, row 14) — cross-reference an existing entry instead of filing a
   duplicate.
5. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within Part 1's `### Active Items` and/or Part 2's
`### Active Items` subsections (append new rows/entries; do not restructure existing
ones).

### Details
Each new entry must be traceable back to its source file (e.g. cite
`docs/03_rag_04_04_dto-models_config.md` as the Source File field) so a reader can find
where the original finding came from.

## Compatibility considerations
This file's Part 1/Part 2 `### Active Items` grow additively. No existing entry is
modified or removed. Part 3/Part 4 and the rest of the document are untouched.

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/00_governance_03_issue-and-uncertainty-management.md` reverts this
row independently. If this row added entries after several other rows already committed
their own edits, reverting this file alone does not affect those other files.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — confirm any new Needs
  Confirmation entry stays in sync with its source doc's marker (per that tool's own
  sync-check purpose).
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.

## Completion criteria
Every bullet routed here by another row (rows 1-20) has exactly one corresponding entry
in Part 1 or Part 2, correctly following that Part's own template; no duplicate entry is
filed for a finding already tracked; the checkers above report no new finding. If no
row ultimately routes anything here (e.g. every real bullet across the 20 files turns out
`Delete`/`Compress`/`Retain` instead), this row's Completion criteria is met by making no
edit at all — do not invent an entry to justify this row's existence.

## Out of scope
This file's Part 3 (Canonical Source Conflict), Part 4 (Configuration Drift), Resolution
Rules, and Temporary Exception Process sections; any existing entry unrelated to this
Plan's findings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-220940 | 20260919-220940 | Conditional on rows 1-20's outcomes; process last Processed last, after rows 1-20. Added 2 Known Issues entries (CI-017 from row 16, CI-018 from row 19) to Part 1 Active Items, and 3 Needs Confirmation entries (NC-037 from row 04, NC-038 from row 14, NC-039 from row 18) to Part 2 Active Items -- checked for duplicates first (UNK-01 was not previously tracked here). Updated the closing 'No other active items' line from NC-036 to NC-039. |
| 2 | Add or update tests per Validation plan | Completed | 20260919-220940 | 20260919-220940 | N/A: documentation-only, no test to add N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-220940 | 20260919-220940 | check_needs_confirmation_inventory.py, check_docs_quality.py, check_docs_structure.py check_needs_confirmation_inventory.py: same 11 pre-existing untracked-marker warnings, none involving the 5 new entries; check_docs_quality.py: 0 error/4 pre-existing warnings (none referencing new entries); check_docs_structure.py: 1 pre-existing finding (file size limit, out of scope) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-220940 | 20260919-220940 | N/A: this document's own Target file IS the documentation being updated Edited Part 1/Part 2 Active Items only, additive |

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
- **Requirement ID**: REQ-004, REQ-005 (add Known Issues/Needs Confirmation entries as routed by other rows)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md