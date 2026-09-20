## Goal
Replace `docs/00_governance_04_documentation-checks.md`'s 3 near-verbatim
duplicate rule sections (REQ-001, REQ-002, REQ-003) with a short summary
plus a link to `docs/00_governance_01_documentation-policy.md`'s
corresponding canonical section, while retaining the one piece of
Checks-specific operational content (the `GV-020` finding-handling
paragraph) that is not itself duplicated rule text.

## Scope
In scope: exactly the 3 sections' body content (lines 259-282, 385-409,
413-418). Out of scope: the 3 section headings themselves (kept per Plan
Implementation intent), the numbered check-list numbering, and every other
section of this file.

## Assumptions
Per Plan Assumptions: the exact summary wording is an editorial judgment
call, not prescribed verbatim by the Plan — this document's own Method
below supplies concrete proposed text, consistent with how the sibling RAG
config-value procedures handled the same kind of decision.

## Design decisions
- For the Merge Condition Validation section: replace only the 3
  duplicated lists (Blocking conditions, Non-blocking conditions, Merge
  workflow) with a single summary sentence and a link. Retain the
  paragraph starting "A `GV-020` finding is not itself blocking..."
  unchanged — this explains the checker's own operational handling of a
  `GV-020` finding, which is legitimate Checks-doc content (`documentation-checks.md`'s
  stated purpose is "what to verify with which tool"), not a restatement of
  a Policy rule.
- For the Change Impact Assessment/Matrix sections: replace both with one
  summary sentence and a link, since neither section has any
  Checks-specific content distinct from Policy's copy (confirmed
  word-for-word identical during Plan verification).
- For the Review Gate Conditions section: replace the 4-bullet list with
  one summary sentence and a link.
- Link anchors use the standard GitHub-flavored-Markdown slug convention
  (lowercase, spaces→hyphens, non-alphanumeric characters removed) already
  used elsewhere in this file (e.g. existing anchor-style cross-references
  in this document's other sections) — `#merge-conditions`,
  `#change-impact-rule`, `#review-rule`. Visually spot-check each rendered
  link during Step 3e validation, since no automated tool in this
  repository verifies Markdown anchor correctness end-to-end.

## Alternatives considered
- Removing the `GV-020` paragraph along with the 3 lists — rejected: this
  paragraph is not duplicated rule text; it is the Checks document's own
  explanation of how the checker enforces a Policy rule, which is exactly
  the kind of content this document should retain per its stated purpose.
- Removing the 3 section headings entirely — rejected: no anchor-breakage
  risk was found (Plan Background), but there is also no independent
  reason to remove them; the numbered check-list (in which "13. Merge
  Condition Validation" is an entry) still benefits from having a
  navigable heading, per Plan Implementation intent.

## Implementation
### Target file
docs/00_governance_04_documentation-checks.md

### Procedure
1. Replace lines 259-282 (from "Before merging any change:" through the
   "5. Verify test suite passes before merging" line) with:
   ```
   Merge is gated on [Policy's Merge Conditions](00_governance_01_documentation-policy.md#merge-conditions)
   (Blocking/Non-Blocking conditions and the Merge Workflow) — see that
   section for the full list, including the `GV-020`-specific
   removed-name-reintroduction condition this checker enforces.

   A `GV-020` finding is not itself blocking, but every finding must be resolved or
   covered by an approved temporary exception before merge — an unexplained finding
   left neither fixed nor excepted is treated as incomplete review, not a passing PR.
   ```
2. Replace lines 385-409 (from "To determine which documents are affected
   by a change:" through the Change-Impact Matrix's last data row) with:
   ```
   See [Policy's Change Impact Rule and Change-Impact Matrix](00_governance_01_documentation-policy.md#change-impact-rule)
   for the full procedure and matrix determining which documents are
   affected by a change.
   ```
3. Replace lines 413-418 (from "The following conditions require review
   before merging:" through the last bullet) with:
   ```
   See [Policy's Review Rule](00_governance_01_documentation-policy.md#review-rule)
   for the conditions that require review before merging.
   ```

### Method
Three separate `Edit` calls (old_string/new_string), one per section, in
the order listed — each is independently revertable.

### Details
Preserve the `### 13. Merge Condition Validation`, `## Change Impact
Assessment`, `### Change-Impact Matrix`, and `## Review Gate Conditions`
headings exactly as-is. Do not renumber the surrounding numbered check
list (`### 12. ...`, `### 14. ...` are unaffected since only body content
under heading 13 changes, not the heading itself).

**Sequencing note**: the Plan's own Implementation steps (Phase 1)
describe relocating the `GV-020` bullet to `documentation-policy.md`
*before* removing it here ("relocate, then remove"), but
`plan-to-implementation-procedure`'s row-order convention assigned this
file `seq` 01 and `documentation-policy.md` `seq` 02 (matching the Plan's
Implementation Target Files table order). If `code-implementation`
executes procedure documents strictly in `seq` order, apply the sibling
`seq` 02 procedure's Edit either first or in the same commit as this one —
a transient state where the `GV-020` condition exists in neither canonical
location is undesirable, even if brief and never independently deployed or
read in isolation.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting each Edit — no data migration or state change is involved. Each
of the 3 Method edits is independently revertable.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_04_documentation-checks.md`
- `grep -rn "documentation-checks.md#" docs/` (confirm still zero matches
  — Plan AC-5)
- Manual: visually confirm the 3 new links render correctly and their
  target anchors exist in `docs/00_governance_01_documentation-policy.md`
  once the sibling procedure (`seq` 02) has landed.

## Completion criteria
All 3 sections' duplicated lists/tables no longer exist, each replaced by
the summary+link text in Procedure; the `GV-020` paragraph, all 3 headings,
and every other section are unchanged; `check_docs_quality.py`/
`check_docs_structure.py` report no new finding on this file relative to
the Plan's baseline (0 findings on both, unchanged); the file's byte size
decreases (from 24573 bytes).

## Out of scope
- `docs/00_governance_01_documentation-policy.md` (the sibling procedure,
  `seq` 02, adds the relocated `GV-020` bullet there).
- Any other section of this file, and the numbered check list's numbering.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 3 Edits per Procedure/Method | Pending | — | — | |
| 2 | N/A: no test suite applies to a documentation content change | Pending | — | — | |
| 3 | Run the 3 commands in Validation plan | Pending | — | — | |
| 4 | N/A: no further documentation update needed beyond this file itself | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` — deduplicate 3 governance rule sections
- **Source issue**: issues/20260920-115634_docdup01val_deduplicate-governance-rule-text-between-policy-and-checks-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-121848_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-132312
- **Related target files**: docs/00_governance_04_documentation-checks.md
