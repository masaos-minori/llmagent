# Remove obsolete lang field enforcement question (NC-033)

## Priority
Low

## Summary
Remove NC-033 from `governance_03`'s Needs Confirmation inventory — the `LanguageCode` enum it asks about no longer exists in the codebase, so the question has no remaining subject — and fix the stale documentation that still references it.

## Background
NC-033 asked whether `lang` field enforcement against `LanguageCode` values was intended, since the field accepted any non-empty string with the en/ja value set treated as convention only. A deep-dive investigation (2026-09-27) found `scripts/rag/enums.py`'s `LanguageCode` enum and its sole user `CrawlTarget` were already deleted as confirmed-dead code in commit batch `20260913-232503` (`implementations/done/20260913-232503_02_scripts_rag_enums_py.md`, `..._01_scripts_rag_models_data_py.md`). Current `lang` parsing (`pipeline_utils.py`) uses a generic `_validate_str` non-empty-string check with no enum reference whatsoever.

## Problem
NC-033's question ("is enforcement against `LanguageCode` intended?") no longer has a subject to enforce against — this is an obsolete item per `rules/coding.md`'s "Obsolete and removable" classification, not an open confirmation.

## Reason for Change
Per `rules/coding.md`'s Current-Specification-Only Policy and Documentation notes classification, an obsolete discrepancy should be deleted, not retained as if still open — leaving it risks a future reader investigating a non-existent enum.

## Implementation Intent
Remove the NC-033 entry from `governance_03`. Separately, fix `docs/21_rag/rag_05_5-constraints-reference.md:29`, which the deep-dive found still describes the stale `LanguageCode`-convention framing, so the doc matches current code (generic non-empty-string validation, no enum).

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (remove NC-033 entry)
- `docs/21_rag/rag_05_5-constraints-reference.md` (line ~29-30; fix stale `LanguageCode` framing)

## Required Changes
- Remove the `#### NC-033` block from `governance_03` Part 2.
- Update `rag_05_5-constraints-reference.md`'s `lang` field description to reflect the current, enum-free `_validate_str` non-empty-string check, removing the reference to a `LanguageCode` convention that no longer exists in code.

## Constraints
N/A: documentation-only change; `LanguageCode`'s removal itself is already-completed, out-of-scope prior work.

## Acceptance Criteria
- NC-033 no longer appears in `governance_03`.
- `rag_05_5-constraints-reference.md` no longer references `LanguageCode` as a convention governing the `lang` field; it accurately describes the current non-empty-string check.
- `tools/check_needs_confirmation_inventory.py` and `tools/check_docs_structure.py`/`check_docs_quality.py` pass on the edited files.

## Testing Expectations
Not required — documentation-only, no behavior change. Run the applicable doc validators listed above.

## Documentation Impact
Two documents updated: `governance_03` (remove stale NC-033 entry) and `rag_05_5-constraints-reference.md` (fix stale `LanguageCode` framing to match current code).

## Out of Scope
- Re-investigating whether `LanguageCode`'s removal itself was correct (already a settled, prior, separate change).
- NC-027, NC-028, NC-029, NC-034 (tracked as separate issues).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — this is a confirmed obsolete item per the 2026-09-27 deep-dive investigation, not an open question requiring further owner input.

## AI Implementation Instruction
Verify via `rg` that `LanguageCode` is genuinely absent from `scripts/rag/` before removing the entry (do not trust the investigation summary alone). Keep the doc fix to the specific stale sentence/paragraph the finding identifies — do not rewrite unrelated sections of `rag_05_5-constraints-reference.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211410
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/21_rag/rag_05_5-constraints-reference.md
