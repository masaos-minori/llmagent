## Goal
- REQ-006: replace the Japanese ADR-008 quote with the translated ADR-008 Assumptions text; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/21_rag/rag_01_system_overview.md`.
- Out: every other line of `docs/21_rag/rag_01_system_overview.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- Prerequisite gate: `plans/done/20261001-105822_plan.md` (langadr001) Execution Status Steps 2-16 must be `Completed` (ADR H1 titles, boilerplate, and ADR-008 Assumptions translated) before this procedure starts. If not, record the blocker in Blocker Log and stop; do not translate independently (Plan Blocker Log, Steps 6-7).

## Design decisions
- Quote must match the ADR exactly so readers can grep it in the ADR.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Paraphrase instead of quoting: rejected — the paragraph cites the ADR's Assumptions section verbatim by design.

## Implementation
### Target file
- `docs/21_rag/rag_01_system_overview.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/21_rag/rag_01_system_overview.md` that only the listed lines changed.

### Details
- Current lines:
  - 232: `**Database** — An architectural assumption per `ADR-008` (Assumptions section: "対象環境：単一Host、複数プロセス"; ...)`
- Change:
  - Replace only the quoted Japanese text with the translated ADR-008 `## Assumptions` line, copied verbatim from `docs/10_adr/ADR-008-sqlite-4db-separation.md` (langadr001 procedure 08 asks for a self-contained sentence such as 'Target environment: a single host, multiple processes').
  - Leave the rest of the paragraph unchanged, including the pre-existing 'lines 91-101' source-line reference (out of scope per Plan).

## Compatibility considerations
- Only the quoted string changes.

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/21_rag/rag_01_system_overview.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — file not listed.
- Full-width grep (AC-007 pattern) on the file — no output.
- `grep -F` of the new quoted text in `docs/10_adr/ADR-008-sqlite-4db-separation.md` — exactly one match in `## Assumptions`.
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_01_system_overview.md` — only the baseline self-reference finding.

## Completion criteria
- The quote equals the ADR-008 Assumptions line verbatim; no Japanese characters remain.
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm prerequisite gate (langadr001 Steps 2-16 Completed) | Pending | — | — | |
| 2 | Apply the change in Implementation > Details | Pending | — | — | |
| 3 | Run the Validation plan and compare with the Plan Design baseline | Pending | — | — | |
| 4 | Self-review meaning and record result in Notes | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-007 (AC-006, AC-007) — Plan Implementation steps Step 7
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/21_rag/rag_01_system_overview.md
