# Extend duplicate-heading detection to alphabetic-suffix numbering and add a merge-boundary check

## Priority
Medium

### Priority Justification
Adversarial verification confirmed that the alphabetic-suffix gap is actively causing undetected defects: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` contains two `## 7c.` headings (lines 54 and 87) with different content — a true duplicate that the current tool misses entirely. Additionally, 28 alphabetic-suffix headings exist across the docs tree, all invisible to the current check. The previously-cited RagPipeline Class duplicate has been resolved, but the structural vulnerability remains unaddressed.

## Summary
`tools/check_docs_quality.py`'s `check_duplicate_heading_numbers` already detects duplicate purely-numeric headings (e.g. two `## 2.` headings at the same level), but its regex (`\d[\d.]*\.`) does not match alphabetic-suffix numbering (e.g. `## 2.`, `## 2a.`, `## 2b.` as three near-duplicate sections) — the exact pattern found and fixed in several prior RAG documentation issues (e.g. `plans/done/20260913-202039_plan.md`'s "RagPipeline Class" sections). Adversarial verification confirms this gap is actively causing undetected defects: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` contains two `## 7c.` headings (lines 54 and 87) with different content, and 28 alphabetic-suffix headings exist across the docs tree, all invisible to the current check. No existing tool checks for content duplication introduced at a document's section-merge boundaries (where content from two source documents/issues was concatenated).

## Background
N/A: covered by Summary — this is a direct gap-analysis finding against `tools/check_docs_quality.py`'s existing `check_duplicate_heading_numbers` function, informed by the concrete alphabetic-suffix duplicate pattern this batch's earlier RAG documentation work (e.g. `20260913-202039_plan.md`) had to fix manually because no automated check caught it.

## Problem
`check_duplicate_heading_numbers`'s regex `^(#{1,6})\s+(\d[\d.]*\.)\s+` only matches a heading number consisting purely of digits and dots — `## 2. RagPipeline Class` matches, but `## 2a. RagPipeline Class` and `## 2b. RagPipeline Class` do not, because `a`/`b` are not digits. This means the exact class of near-duplicate section that this project's own RAG documentation work has already found and fixed by hand at least once would not be caught automatically if it recurred. Adversarial verification confirms this is not theoretical: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` currently contains two `## 7c.` headings (lines 54 and 87) with different content, and running `uv run python tools/check_docs_quality.py --only duplicate_heading_numbers` reports zero issues despite this clear duplicate. Additionally, 28 alphabetic-suffix headings exist across the docs tree, all invisible to the current check. Separately, no tool checks whether content merged at a document's section boundary (e.g. two Implementation Notes sections concatenated from separate edits) introduces duplicated prose, as distinct from duplicated headings.

## Reason for Change
An automated check that only catches the purely-numeric case leaves the alphabetic-suffix case (already proven to occur in this codebase's own history) undetected until manual review happens to notice it — as it did for the RagPipeline Class sections. A merge-boundary duplication check would catch the underlying failure mode (repeated content from independent edits landing in the same document) before it needs a manual fix.

## Implementation Intent
Extend `check_duplicate_heading_numbers`'s pattern matching to also flag alphabetic-suffix numbering that shares the same base number at the same heading level (e.g. `2.`, `2a.`, `2b.` at `##` level) as a probable near-duplicate needing review — this is a broader "same base number, same level" check, not merely a wider regex, since `2a`/`2b` are a different suffix shape than `2.1`/`2.2` (which are legitimately non-duplicate subsections and must not be flagged). Separately, add a lightweight content-similarity check (e.g. comparing section body text with a similarity threshold, not just headings) that flags two sections in the same document whose prose overlaps heavily — a proxy for the section-merge-boundary duplication this issue also targets.

## Target Files or Areas
- `tools/check_docs_quality.py`
- `tools/_docs_consistency_lib.py`
- `tests/tools/test_check_docs_quality.py` (new file — no existing test file for `check_docs_quality.py` was found under `tests/tools/`; confirmed via search)

## Required Changes
- Extend `check_duplicate_heading_numbers` (or add a new check function) to detect same-base-number, same-level headings with differing alphabetic suffixes (e.g. `2.`/`2a.`/`2b.`) as a probable near-duplicate, distinct from legitimate numeric subsections (`2.1`, `2.2`). Concrete example: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` has two `## 7c.` headings (lines 54 and 87) with different content.
- Add a lightweight content-similarity check that flags two sections within the same document whose body text overlaps above a defined threshold, as a proxy for merge-boundary duplication — define the threshold and comparison granularity (paragraph-level, not whole-section) conservatively enough to avoid false positives on legitimately similar (but not duplicate) content.
- Add tests covering: the alphabetic-suffix duplicate case (should flag), legitimate numeric subsections like `2.1`/`2.2` (should not flag), the concrete `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` (should flag), and a content-similarity true positive/false positive pair.
- Register both checks with the existing `@register_core_check` mechanism so they run as part of the standard `check_docs_quality.py` invocation.

## Constraints
The content-similarity check must not flag legitimately repeated boilerplate (e.g. this project's own "Add or update unit, integration, and regression tests..." Verification-section pattern repeated across many issue/plan documents by design) — scope it to prose within a single document's own sections, not cross-document boilerplate, and tune the threshold to avoid noise on short, intentionally-templated sections.

## Acceptance Criteria
- The extended check flags a `2.`/`2a.`/`2b.` alphabetic-suffix duplicate pattern (the exact shape found in prior RAG documentation work) as an issue.
- The extended check flags the known `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` (lines 54 and 87) as an issue.
- The extended check does not flag legitimate numeric subsections (`2.1`, `2.2`, etc.) as duplicates.
- The new content-similarity check flags a constructed near-duplicate-section test case and does not flag two intentionally-templated-but-distinct sections (e.g. two issues' near-identical Verification sections, which is expected structure, not a merge-boundary defect).
- Both checks run as part of `tools/check_docs_quality.py`'s standard invocation with no changes to how the tool is called.

## Testing Expectations
Add unit tests for both new/extended checks covering the true-positive and false-positive cases listed in Acceptance Criteria, including a test for the known `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`. Run `uv run pytest` on the new test file(s), plus `uv run python tools/check_docs_quality.py` against the full `docs/` tree to confirm no new false-positive noise on existing, legitimate documents.

## Documentation Impact
N/A: this issue modifies a `tools/` script and its tests, not `docs/*.md` content directly — no documentation update is in scope beyond what `tools/TOOL_DESCRIPTIONS.md` requires if this changes the tool's described behavior (confirm per `routing.md`'s "Adding a new tool" guidance, since this extends an existing tool rather than adding one).

## Out of Scope
- Retroactively re-scanning all of `docs/` for existing content-similarity duplicates as part of this issue — that is a follow-up sweep, not part of building the check itself.
- Any change to `check_duplicate_heading_numbers`'s existing purely-numeric detection — that behavior is correct and unchanged; this issue only adds the alphabetic-suffix case alongside it.

## Dependencies
N/A: none.

## Unresolved Questions
The exact test file location for `tools/check_docs_quality.py`'s existing tests was not confirmed during this issue's drafting — confirmed via adversarial verification that no such test file exists; a new file `tests/tools/test_check_docs_quality.py` must be created. Additionally, the content-similarity threshold value should be validated empirically against the full `docs/` tree during implementation rather than assumed beforehand.

## AI Implementation Instruction
Keep the alphabetic-suffix check and the content-similarity check as clearly separate functions (they target different failure modes) even if registered together; do not conflate them into one over-general "duplicate detector." Tune the content-similarity threshold conservatively and validate it against the full `docs/` tree before finalizing, specifically checking for false positives on this project's own templated Verification/Out-of-Scope sections. Locate the existing test file for `check_docs_quality.py` before adding new tests, per Unresolved Questions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-112554
- **Related target files**: tools/check_docs_quality.py, tools/_docs_consistency_lib.py

## Adversarial Verification (2026-09-19)

### Claims Verified
| Claim | Status | Evidence |
|---|---|---|
| Regex `\d[\d.]*\.` doesn't match alphabetic-suffix headings | Confirmed | Code inspection: `tools/check_docs_quality.py:371` — regex only matches digits+dots |
| Alphabetic-suffix duplicates exist in docs | Confirmed | 28 instances found across docs tree; `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` has two `## 7c.` headings (lines 54, 87) |
| Current tool misses these duplicates | Confirmed | `uv run python tools/check_docs_quality.py --only duplicate_heading_numbers` reports zero issues despite the `## 7c.` duplicate |
| No content-similarity check exists | Confirmed | Search of all `tools/*.py` scripts — none implement content similarity or merge-boundary detection |
| Test file location unconfirmed | Resolved | No existing test file for `check_docs_quality.py` found under `tests/tools/`; new file required |

### Priority Change
Low → Medium: Confirmed active undetected defects (not theoretical gap). The `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` is a real, currently-missed defect.

### Additional Findings
1. RagPipeline Class duplicate (cited in original Summary) has been resolved by prior work.
2. The `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` provides a concrete, reproducible test case for the alphabetic-suffix check.
