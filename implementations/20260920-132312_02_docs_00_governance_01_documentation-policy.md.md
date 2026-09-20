## Goal
Add the `GV-020`-related non-blocking-condition bullet (REQ-001) to
`docs/00_governance_01_documentation-policy.md`'s "## Merge Conditions"
Non-Blocking Conditions list, so the canonical copy gains the one piece of
content that was previously only in `documentation-checks.md`'s
non-canonical copy, before that copy is replaced with a summary+link by
the sibling procedure.

## Scope
In scope: exactly the "### Non-Blocking Conditions (Allow Merge with
Warning)" list (lines 402-405). Out of scope: every other part of the "##
Merge Conditions" section (Blocking Conditions, Merge Workflow) and every
other section of this file.

## Assumptions
Per Plan Design's "Byte-size interaction": this file is already 5219 bytes
over `check_docs_structure.py`'s 24576-byte limit before this edit; adding
one bullet (~150-200 bytes) does not create a new failure, since the check
was already failing — this is a pre-existing, unrelated condition, not
something this row fixes or worsens materially.

## Design decisions
Append the bullet as the 4th item in the existing 3-item Non-Blocking
Conditions list, copying the wording from `documentation-checks.md:271`
verbatim (word-for-word) so the relocated content's meaning is preserved
exactly, per Plan Constraints ("do not change any rule's actual meaning").

## Alternatives considered
Paraphrasing the bullet instead of copying it verbatim — rejected: Plan
Acceptance Criteria AC-4 requires no substantive meaning change; verbatim
copy is the only way to guarantee this for a relocation (as opposed to a
summary, which is appropriate for the *removed* copy in
`documentation-checks.md`, not for the *canonical* copy gaining new
content here).

## Implementation
### Target file
docs/00_governance_01_documentation-policy.md

### Procedure
Append a 4th bullet to the Non-Blocking Conditions list (after "Config
drift detected but no behavioral impact", line 405):
```
- Removed-name reintroduction detected by `check_compat_shims.py --check-removed-names` (`GV-020`), without an approved temporary exception (`docs/00_governance_03_issue-and-uncertainty-management.md`)
```

### Method
One `Edit` call (old_string = the existing 3-bullet list ending in "Config
drift detected but no behavioral impact"; new_string = the same 3 bullets
plus the new 4th bullet appended).

### Details
Do not alter the "### Blocking Conditions (Prevent Merge)" or "### Merge
Workflow" subsections, or any other part of this file. Copy the bullet
text exactly as it appears in `documentation-checks.md:271` — do not
reword, shorten, or add commentary.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting the single Edit — no data migration or state change is
involved.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md`
  (expect the pre-existing byte-size finding to remain present — this is
  not a new finding, per Plan Background/Design; confirm no *other* new
  finding appears)
- `grep -n "GV-020" docs/00_governance_01_documentation-policy.md` (confirm
  exactly one match, the newly added bullet)

## Completion criteria
The Non-Blocking Conditions list contains exactly 4 bullets, the 4th being
the `GV-020`-related bullet copied verbatim from
`documentation-checks.md:271`; every other section of this file is
unchanged; `check_docs_quality.py` reports no new finding;
`check_docs_structure.py`'s pre-existing byte-size finding remains (not a
regression this row introduces) and no other new finding appears.

## Out of scope
- `docs/00_governance_04_documentation-checks.md` (the sibling procedure,
  `seq` 01, removes the non-canonical copy of this bullet there).
- Any other section of this file.
- Reducing this file's overall byte size below
  `check_docs_structure.py`'s limit (a pre-existing condition, out of
  scope per Plan Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 1 Edit per Procedure/Method | Completed | 20260920 | 20260920 | 4th bullet appended verbatim, matching `documentation-checks.md:271`'s wording exactly (confirmed by Read before editing). |
| 2 | N/A: no test suite applies to a documentation content change | N/A | — | — | |
| 3 | Run the 3 commands in Validation plan | Completed | 20260920 | 20260920 | `check_docs_quality.py`: 10 pre-existing within-file warnings (RAG/MCP/Agent/EventBus sections, lines 209-227), unrelated to and unchanged by this edit — no new finding. `check_docs_structure.py`: pre-existing byte-size finding remains (29997 bytes, up from the ~29795-byte pre-edit baseline — consistent with the ~150-200 byte bullet addition), no other new finding. `grep -n "GV-020"`: exactly 1 match, the newly added bullet. |
| 4 | N/A: no further documentation update needed beyond this file itself | N/A | — | — | |

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
- **Requirement ID**: `REQ-001` — relocate GV-020 bullet to the canonical Merge Conditions list
- **Source issue**: issues/20260920-115634_docdup01val_deduplicate-governance-rule-text-between-policy-and-checks-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-121848_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-132312
- **Related target files**: docs/00_governance_01_documentation-policy.md
