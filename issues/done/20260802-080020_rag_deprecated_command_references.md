# Fix deprecated command references (/db consistency, /db rag rebuild-fts) across docs/03_rag_05_2, 05_7, 91_design_notes-part1

## Priority
High

## Summary
`docs/03_rag_05_2-execution-guide.md`, `docs/03_rag_05_7-rag-index-consistency-checks.md`, and `docs/03_rag_91_design_notes-part1.md` all reference deprecated commands `/db consistency` and `/db rag rebuild-fts`. These commands' source no longer exists (only `.pyc` remnants in `__pycache__`); the current, correct commands are `/session rag-consistency` and `/session rag-rebuild-fts` (implemented in `cmd_session.py`). `05_2` notices the deprecation but doesn't name the successor; `05_7` and `91` are unaware of the deprecation and present the old commands as current procedure.

## Reason for Change
This is a confirmed factual error (the old commands' source doesn't exist) — an operator following any of these 3 files during an incident would attempt to run a nonexistent command, delaying recovery.

## Implementation Intent
Replace every reference to `/db consistency`/`/db rag rebuild-fts` with the correct `/session rag-consistency`/`/session rag-rebuild-fts` across all 3 files, and record the deprecation event in the RAG Known Issues document.

## Target Files or Areas
`docs/03_rag_05_2-execution-guide.md`, `docs/03_rag_05_7-rag-index-consistency-checks.md`, `docs/03_rag_91_design_notes-part1.md`

## Required Changes
- In `05_2`, add the successor command name (`/session rag-consistency` / `/session rag-rebuild-fts`) where the deprecation is already noted but the successor is missing.
- In `05_7` and `91_design_notes-part1`, replace the deprecated command references entirely with the current commands, noting that the old names are deprecated (`cmd_session.py` reference).
- Add an entry to `docs/03_rag_90_inconsistencies_and_known_issues.md` recording this command rename (tracked as part of the broader Known Issues population issue, but note it here as a required cross-reference).

## Acceptance Criteria
No file in this set references `/db consistency` or `/db rag rebuild-fts` as a currently-executable command; all 3 files consistently point to `/session rag-consistency` / `/session rag-rebuild-fts`.

## Testing Expectations
Not required (documentation-only). Manually verify via `grep -rn "rag-consistency\|rag-rebuild-fts" scripts/agent/commands/cmd_session.py` and confirm no source exists for the old command names before finalizing.

## Documentation Impact
3 files corrected; a cross-reference should be added to `docs/03_rag_90` once that file is populated (separate issue).

## Out of Scope
Do not change `cmd_session.py` or any command implementation in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply directly. Verify the exact current command names/flags via `cmd_session.py` before finalizing wording, in case they have changed further since this review was written.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 1), §4 強化候補 (91_design_notes-part1), §5 例1, §6A (廃止コマンド)
- Generated at: 2026-08-02
