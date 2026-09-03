## Goal
Register three new Needs Confirmation Inventory entries in
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 (next
available sequential IDs) for the three genuinely-unresolved questions this
Plan's front-matter finalization surfaces but does not itself resolve: whether
`adr`/`security` should be permanent `area` values, the `related`-field-vs-body-section
duality, and `schemas/doc_front_matter.json`'s `additionalProperties`
strictness.

## Scope
- **In-Scope**: `docs/00_governance_03_issue-and-uncertainty-management.md`
  Part 2 (`### Active Items`) only — adding three new `#### NC-XXX` entries and
  updating the closing "No other active items…" sentence.
- **Out-of-Scope**: `docs/00_governance_02_documentation-metadata.md` (seq 01),
  `schemas/doc_front_matter.json` (seq 02); resolving the three registered
  questions (explicitly this Plan's Out-of-Scope); Part 1 (Known Issues) and
  Part 2's other existing entries — unmodified by this row.

## Assumptions
- The current highest registered NC ID is `NC-029` (re-verified 2026-09-03 via
  `grep -n "^#### NC-"`, confirming no gap and no ID above 029) — so the next
  three available sequential IDs are `NC-030`, `NC-031`, `NC-032`. The Plan's
  own citation ("current highest ID NC-029, line 775") has a stale line number
  (actual: line 875, shifted by this session's separate, later addition of
  NC-022 through NC-025 under a different Plan) but the ID conclusion itself
  (`NC-029` highest, next IDs `030`-`032`) is unaffected and re-confirmed
  correct.
- `docs/00_governance_04_documentation-checks.md`'s `GV-020` row and
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s own
  `## Temporary Exception Process` section (both added by a separate,
  already-implemented Plan, `plans/done/20260903-090945_plan.md`) are unrelated
  to this row's three new entries — no cross-reference or naming collision
  exists between them.
- Part 2's `### Inventory Entry Fields` still requires exactly 15 fields
  (ID, Source File, Section, Line Number, Question, Evidence, Impact, Required
  Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution
  Target, Blocking) — re-verified by direct `Read`, matching every existing
  entry's structure (`NC-021` through `NC-029`) with no drift.

## Design decisions
- **ID assignment order follows REQ-007's own listed order**: `NC-030` = the
  `adr`/`security` permanence question (`UNK-01`), `NC-031` = the
  `related`-field duality question (`UNK-02`), `NC-032` = the
  `additionalProperties` strictness question (`UNK-03`) — a simple, traceable
  1:1 mapping to the Plan's own Unknowns table order.
- **`NC-032`'s `Source File` names `schemas/doc_front_matter.json`** rather
  than a `docs/*.md` file, and its `Section` field names the schema's
  `additionalProperties` top-level property rather than a Markdown heading —
  the 15-field template's `Source File`/`Section` fields are document-shaped by
  convention (every existing entry cites a `.md` file and a heading), but the
  template does not textually forbid citing a non-Markdown artifact, and no
  better-fitting field exists in the template for "which artifact does this
  question concern" — inventing a 16th field for this one entry would break
  the template's own fixed 15-field contract more than stretching `Source
  File`/`Section` slightly beyond their typical Markdown-heading usage.
- **Entries are inserted immediately after `NC-029`** (the current last entry),
  not before `NC-021`-`NC-029` or interleaved — this preserves strict ascending
  ID order with the simplest possible insertion (append), matching how
  `NC-026`-`NC-029` were themselves appended after `NC-021` in an earlier,
  unrelated addition this session.

## Alternatives considered
- **Cite `docs/00_governance_02_documentation-metadata.md`'s "Existing Metadata
  Fields" section as `NC-032`'s `Source File`/`Section` instead of the schema
  file itself**, since that document is where the `area` enum and `status`
  field are documented — considered, rejected: `UNK-03` is specifically about
  the *schema artifact's* `additionalProperties` strictness, a property that
  exists only in `schemas/doc_front_matter.json`, not in the governance
  document's prose; citing the governance document would misdirect a future
  reader trying to locate the actual property in question.
- **Defer registering `NC-032` until `schemas/doc_front_matter.json` (seq 02)
  is actually created**, to cite an exact line number within it — rejected:
  seq 02's own Details already fix the file's exact content in advance (this is
  a Frozen Plan's downstream procedure, not speculative), so the line number is
  already knowable without waiting; per this workflow's own Sequential Target
  Processing, each row is independently implementable once its own procedure
  document exists, and this row does not require seq 02 to be *applied* first,
  only for its *content* to be known (which it already is, from seq 02's own
  Details section).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Immediately before editing, re-read `## Part 2: Needs Confirmation
   Inventory` > `### Active Items` in full and re-run `grep -n "^#### NC-"` to
   re-confirm `NC-029` remains the highest registered ID (done above; no drift).
2. Insert the three new entries (Details below) immediately after `NC-029`'s
   last field (`- **Blocking**: No`) and its trailing blank line, and
   immediately before the closing "No other active items..." sentence.
3. Update the closing sentence to include the three new IDs.

### Method
Direct text edit (e.g. via the `Edit` tool): one edit inserting the three
entries as a single contiguous block after `NC-029`, and one separate edit
updating the closing sentence.

### Details

**Edit 1 — insert three new entries after `NC-029`**:

Before (anchor — the blank line between `NC-029`'s last field and the closing
sentence):
```
- **Blocking**: No

No other active items beyond NC-021 through NC-029 above.
```

After:
```
- **Blocking**: No

#### NC-030

- **Source File**: `00_governance_02_documentation-metadata.md`
- **Section**: Existing Metadata Fields (`area` enum)
- **Line Number**: ~21 (approximate; confirm against this document's content as
  edited by this Plan's seq 01 implementation-procedure)
- **Question**: Should `adr` and `security` be permanent `area` enum values, or
  folded into an existing area (e.g. `overview`)?
- **Evidence**: 11 real documents use `area: adr`, 2 use `area: security`, yet
  neither was part of the original 8-value enum; no stated design rationale
  was found for the omission
- **Impact**: If folded into another area instead, 13 documents' `area:`
  values would need migration; if kept permanent, no migration is needed but
  the enum grows to 10 values
- **Required Action**: Owner review of whether `adr` and `security` warrant
  their own top-level area, given their real, non-trivial adoption
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next governance area-taxonomy review
- **Blocking**: No

#### NC-031

- **Source File**: `00_governance_02_documentation-metadata.md`
- **Section**: Existing Metadata Fields (`related`)
- **Line Number**: ~24 (approximate; confirm against this document's content as
  edited by this Plan's seq 01 implementation-procedure)
- **Question**: Is the front-matter `related` field and the `## Related
  Documents` body-section heading an intentional duality (front matter for
  tooling, body section for human readers), or an unintentional drift where
  one should be removed?
- **Evidence**: Both exist in active use across the document set; no design
  rationale was found in `docs/00_governance_01_documentation-policy.md` or
  `docs/00_governance_02_documentation-metadata.md` explaining why both exist
- **Impact**: If unintentional drift, maintaining two parallel
  related-documents lists risks them diverging (one updated, the other left
  stale)
- **Required Action**: Owner decision on whether both should be kept (and if
  so, whether one should generate the other), or one should be deprecated
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance metadata review
- **Blocking**: No

#### NC-032

- **Source File**: `schemas/doc_front_matter.json`
- **Section**: `additionalProperties` (top-level schema property)
- **Line Number**: ~6 (per this Plan's seq 02 implementation-procedure's
  Details section)
- **Question**: Should `schemas/doc_front_matter.json` set
  `additionalProperties: false` (strict, matching `schemas/event_envelope.json`'s
  own convention) or remain permissive (`true`) to allow forward-compatible,
  area-specific extension fields?
- **Evidence**: `schemas/event_envelope.json` itself uses
  `additionalProperties: false`; however, this repository's actual `docs/*.md`
  front matter already carries area-specific extra keys in active use in some
  files (e.g. `source:` seen in several RAG documents)
- **Impact**: If later set to `false` without first auditing which documents
  carry extension keys, `docmeta03`'s CI enforcement would immediately fail on
  every file using one
- **Required Action**: Owner decision, informed by a survey of which documents
  currently use non-required front-matter keys, before `docmeta03`'s
  CI-enforcement implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Before `docmeta03`'s CI-enforcement implementation
  begins
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.
```

**Edit 2 — this is already included in Edit 1's replacement of the closing
sentence** (the "Before"/"After" blocks above already replace
"No other active items beyond NC-021 through NC-029 above." with the
NC-032-inclusive version) — no separate second edit is required, unlike this
Plan's sibling row-generation pattern in earlier Plans, since the anchor here
already spans both the insertion point and the closing sentence in one
contiguous block.

## Compatibility considerations
No other document references `NC-030` through `NC-032` yet (re-confirmed at
Procedure step 1). Depends conceptually on seq 01's applied content for
`NC-030`/`NC-031`'s exact line-number citations and on seq 02's applied content
for `NC-032`'s, but this row's own edit is syntactically valid regardless of
whether seq 01/02 have been applied yet (their content is already fixed in
their own Frozen implementation-procedure documents, so the citations are
accurate to what will exist, not speculative).

## Security considerations
None — documentation-only addition to a governance tracking inventory; no code,
credentials, or access-control content is affected.

## Rollback considerations
Single-file, one-contiguous-edit change to a Markdown document under version
control; revert via `git revert`. Removing these three entries later (once
resolved, per this document's own Status Values rule that resolved items are
removed rather than marked closed) is the document's normal lifecycle, not a
rollback.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Automated Needs Confirmation inventory check | `uv run python tools/check_needs_confirmation_inventory.py` | New `NC-030`-`NC-032` entries pass field validation; no new warnings beyond the pre-existing baseline set |
| docs/00_governance_03_issue-and-uncertainty-management.md | Automated doc structure/quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual review | Re-read the three new entries and the updated closing sentence | Each entry contains all 15 required fields; IDs appear in ascending order with no gaps or duplicates |

## Completion criteria
- `docs/00_governance_03_issue-and-uncertainty-management.md` contains new NC
  entries `NC-030` through `NC-032` for the three registered questions,
  using the full 15-field template and the next available sequential IDs
  (AC-6).
- `uv run python tools/check_needs_confirmation_inventory.py` and
  `uv run python tools/check_docs_quality.py` report no new errors.

## Out of scope
`docs/00_governance_02_documentation-metadata.md` (seq 01),
`schemas/doc_front_matter.json` (seq 02) — each has its own
implementation-procedure document per this Plan's Implementation Target Files
table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified NC-029 still highest (no drift) and governance_02's actual post-edit line numbers (area at line 22, related at line 24 — corrected from "~21"/"~24" approximations to exact values since seq 01 was already applied). Inserted NC-030 through NC-032 exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_needs_confirmation_inventory.py`: 8 warnings, identical to the pre-existing baseline (0 new). Diff confirmed scoped to exactly the 77 inserted lines. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260902-194021_docmeta01_finalize_canonical_documentation_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-124425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-154428
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
