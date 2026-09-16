# Resolve self-contradictory statements in the Known Issues Part 1 inventory

## Priority
High

## Summary
Two independent defects in `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 cause the document to assert conclusions that contradict its own content: leftover bullets under the CI-005 removal placeholder, and a closing summary sentence that enumerates removed and resolved entries as active.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
The `#### CI-005` removal placeholder paragraph states that `ConfigLoader.load_all()`'s `strict` parameter already defaults to `True`, `_REQUIRED_CONFIG_FILES` already includes `agent.toml`, and `ConfigMissingError` is already re-raised as `ConfigLoadError` — i.e. the config-loading defect is already fixed. Two leftover bullets immediately below it state the opposite: that missing configuration "silently fails open across all environments, including production," and recommend passing `strict=True`. Separately, the Part 1 closing summary sentence names `DESIGN-1` and `EVENTBUS-008` as active even though the same document marks both resolved and removed on 2026-09-14, and uses the range notation `EVENTBUS-001 through EVENTBUS-008`, which no longer holds since 002 is resolved, 005 through 007 are deferred, and 008 is removed.

## Reason for Change
This document is the single system of record for Known Issues across all areas, and the Decision Target Canonical Source Matrix designates it as the registration destination for nearly every conflict type. A reader who encounters a contradiction here has no higher authority to appeal to — there is no document above it that settles which of the two conflicting statements is correct.

Both defects are also actively harmful rather than merely untidy:

The CI-005 leftover bullets state that missing configuration "silently fails open across all environments, including production," and recommend passing `strict=True`. The placeholder paragraph directly above them establishes the opposite: `ConfigLoader.load_all()`'s `strict` parameter already defaults to `True`, `_REQUIRED_CONFIG_FILES` already includes `agent.toml`, and `ConfigMissingError` is already re-raised as `ConfigLoadError`. A reader who scans for the actionable bullets — which is how the other entries are structured, and therefore where the eye goes — will conclude that production configuration loading is unsafe. The likely outcome is wasted investigation; the worse outcome is a change to already-correct fail-closed behavior made in the belief that it is a fix.

The closing summary sentence is the cheapest way to enumerate active issues, and is the form most likely to be consumed by tooling or quoted into a status report. It currently names DESIGN-1 and EVENTBUS-008, both of which the same document states were resolved and removed on 2026-09-14, and uses a contiguous range `EVENTBUS-001 through EVENTBUS-008` that no longer holds — 002 is resolved, 005 through 007 are deferred, 008 is removed. The document therefore declares a violation of its own Current-Specification-Only Policy in its own summary line.

## Implementation Intent
Restore the invariant that this document does not contradict itself, without changing the substance of any entry. Both fixes are deletions or mechanical rewrites of statements that are already known to be wrong from evidence contained in the same file. No external verification is required, which is why these are batched: they can be completed, reviewed, and merged in one pass by one reviewer reading one file.

The closing summary should be rebuilt by parsing the actual `#### ` headings and their `Status` fields rather than by editing the existing sentence, so the result is derived from the document's real state instead of from a prior author's assumption about it.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Delete the two orphaned bullets that follow the `#### CI-005` placeholder paragraph. Leave the placeholder paragraph itself unchanged.
- Rewrite the Part 1 closing summary to enumerate only entries whose `Status` is `open`, `investigating`, or `deferred`.
- Omit DESIGN-1 and EVENTBUS-008 from the enumeration.
- Replace the `EVENTBUS-001 through EVENTBUS-008` range with an explicit list, since the range now contains gaps.
- Separate deferred entries from open ones in the sentence if doing so improves clarity.
- Scan the remaining removal placeholders (RAG-003, RAG-004, DESIGN-1, SHARED-001, EVENTBUS-008, CI-004, CI-006) for the same orphaned-bullet pattern and remove any found.

## Constraints
- Do not change the `Status` value of any entry as part of this issue.
- Do not modify `scripts/shared/config_loader.py` or `scripts/agent/config_builders.py` — the fail-closed behavior described in the CI-005 placeholder is already correct and must not be altered.
- Derive the enumeration mechanically from the headings present; do not infer or carry forward IDs from the existing sentence.

## Acceptance Criteria
- [ ] No bullet list appears between the `#### CI-005` placeholder paragraph and the `#### CI-006` heading.
- [ ] The document contains no remaining statement that missing configuration fails open.
- [ ] Every ID named in the closing summary has a full entry whose `Status` is `open`, `investigating`, or `deferred`.
- [ ] No ID named in the closing summary is described elsewhere in the document as resolved or removed.
- [ ] No contiguous range notation is used where the range contains gaps.
- [ ] No other removal placeholder is followed by orphaned field bullets.
- [ ] Markdown structure is valid and no heading levels changed.

## Testing Expectations
Not required for code — documentation-only change with no behavior impact. Manually verify each Acceptance Criteria item by reading the edited sections, and run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` to confirm no new structural findings.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 (the CI-005 region and the closing summary sentence) is the document being corrected; no other document is affected.

## Out of Scope
- Resolving or reclassifying any individual entry.
- Amending the Current-Specification-Only Policy itself.
- Any code change.

## Dependencies
N/A: none block this issue's own content. `memo3.md`'s suggested Execution Order places this third, after ISSUE-8 (typo/indentation cleanup) and ISSUE-6 (conformance checker deployment) — not because this issue's content depends on either, but so the checker (once built) can validate this fix's output on a syntactically-clean file.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Edit only the CI-005 region and the closing summary sentence. Build the ID list by parsing `#### ` headings and their `Status` fields programmatically, not by hand-editing the existing sentence. Stop and report if the orphaned bullets appear to belong to an entry other than CI-005.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-195957
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
