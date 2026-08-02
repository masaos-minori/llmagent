# Populate docs/03_rag_90_inconsistencies_and_known_issues.md with this review's confirmed errors and open questions

## Priority
High

## Summary
`docs/03_rag_90_inconsistencies_and_known_issues.md` currently has zero substantive entries (only migration notes and keywords), despite being intended as the single consolidated location for known bugs and unresolved discrepancies in the RAG domain. This review alone confirmed 7 cross-cutting factual errors plus numerous additional confirmed errors and open Needs Confirmation items across `docs/03_rag_*.md`.

## Reason for Change
An empty Known Issues file means the domain currently has no functioning consolidation point — every one of the confirmed errors and open questions found by this review (and future reviews) would otherwise stay scattered across individual files with no central tracking, repeating the exact "one source of truth" failure pattern this review criticizes elsewhere (e.g. Fail-Open/Closed tables, port numbers in other domains).

## Implementation Intent
First, check git/migration history to determine whether this file's emptiness reflects genuinely no known issues ever being recorded, or a migration that lost the actual entries. Then populate the file with every confirmed error and open Needs Confirmation item surfaced by this review, cross-referencing the specific fix issues already filed for each (this issue's siblings in this batch).

## Target Files or Areas
`docs/03_rag_90_inconsistencies_and_known_issues.md`

## Required Changes
- Check `git log` for this file's history to determine whether entries existed before a migration and were lost, or whether it has always been empty; record the finding.
- Add an entry for each of the 7 cross-cutting confirmed errors identified in this review (deprecated commands, delete_document() order, ETagManager doc_id=0, crawl_file responsibility, crawl depth/pages, [debug] output, chunk_utils.py sharing), cross-referencing the specific fix issue filed for each.
- Add entries for the additional confirmed errors (delete_existing_document() name, 05_1 filename typos, line-number drift, refiner_max_chars_per_chunk, use_rrf=False warning source, 02_08 usage-table errors) and the open Needs Confirmation items (unused DTOs, result_source dual definition, HTTP last_fetch_result, FTS token limit, MIN_TEXT_LENGTH_FOR_DETECTION, MIN_HEADING_LINES_FOR_MARKDOWN, etag_manager.py 05_6 cross-check), each cross-referencing its corresponding fix issue.
- Follow the entry template/lifecycle structure defined in `docs/00_governance_04_known-issues-template.md`.

## Acceptance Criteria
`docs/03_rag_90` contains a substantive entry for every confirmed error and open question surfaced by this review, each cross-referencing the specific tracking issue; the file's prior-emptiness cause (lost-in-migration vs. never-populated) is recorded.

## Testing Expectations
Not required (documentation-only). The migration-history check is a `git log`/`git blame` investigation, not a test run.

## Documentation Impact
`docs/03_rag_90_inconsistencies_and_known_issues.md` substantially populated — this becomes the domain's actual functioning Known Issues consolidation point.

## Out of Scope
Do not resolve any of the individual confirmed errors or open questions in this issue — this issue only creates the consolidated tracking entries; the actual fixes are tracked in this batch's other issues.

## AI Implementation Instruction
Wait until (or coordinate with) the other issues in this batch being filed, so each `03_rag_90` entry can cross-reference its specific fix issue by title/number rather than only restating the problem. Check `git log --follow docs/03_rag_90_inconsistencies_and_known_issues.md` before concluding the emptiness cause.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (再構成の基本方針 item 4), §6B (90_inconsistencies_and_known_issues.mdの本文欠落)
- Generated at: 2026-08-02
