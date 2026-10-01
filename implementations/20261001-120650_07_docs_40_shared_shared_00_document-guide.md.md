## Goal
- REQ-005: replace Japanese ADR titles in link descriptions with the translated ADR H1 titles; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/40_shared/shared_00_document-guide.md`.
- Out: every other line of `docs/40_shared/shared_00_document-guide.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- Prerequisite gate: `plans/done/20261001-105822_plan.md` (langadr001) Execution Status Steps 2-16 must be `Completed` (ADR H1 titles, boilerplate, and ADR-008 Assumptions translated) before this procedure starts. If not, record the blocker in Blocker Log and stop; do not translate independently (Plan Blocker Log, Steps 6-7).

## Design decisions
- Copy titles from the translated ADR H1 (single source); do not translate independently (Plan Risks).
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Translate titles locally before langadr001 lands: rejected — creates new mismatches (Plan Risks).

## Implementation
### Target file
- `docs/40_shared/shared_00_document-guide.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/40_shared/shared_00_document-guide.md` that only the listed lines changed.

### Details
- Current lines:
  - 94: `- [ADR-008](...) — SQLiteを4DBへ分離する`
- Change:
  - For each listed line, replace only the Japanese title text with the H1 title text (after `ADR-NNN: `) of the ADR the link points to, read from the translated ADR (`grep -h '^# ADR-' docs/10_adr/ADR-*.md`). Keep the link label, link target, separator, and list structure byte-identical.

## Compatibility considerations
- Navigation text only; link targets unchanged, so `check_docs_structure.py` link reachability is unaffected.

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/40_shared/shared_00_document-guide.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — file not listed.
- Full-width grep (AC-007 pattern) on `docs/40_shared/shared_00_document-guide.md` — no output.
- Title comparison: each edited description equals the linked ADR's H1 text.
- `uv run python tools/check_docs_structure.py docs/40_shared/shared_00_document-guide.md` — only the baseline missing Related Documents/Keywords and self-reference findings.

## Completion criteria
- Every ADR link description equals the linked ADR's H1 title; no Japanese characters remain.
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm prerequisite gate (langadr001 Steps 2-16 Completed) | Completed | 20261001-140332 | 20261001-140332 |  |
| 2 | Apply the change in Implementation > Details | Completed | 20261001-140332 | 20261001-140332 |  |
| 3 | Run the Validation plan and compare with the Plan Design baseline | Completed | 20261001-140332 | 20261001-140332 |  |
| 4 | Self-review meaning and record result in Notes | Completed | 20261001-140332 | 20261001-140332 | ADR title(s) in link descriptions replaced programmatically with the translated ADR H1 titles (langadr001 gate satisfied; only the listed lines changed); all checks unchanged vs batch baseline; targeted tests unchanged (1 pre-existing failure); full suite deferred to batch end per user decision; docs-mapping step N/A |

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
- **Requirement ID**: REQ-005, REQ-007 (AC-005, AC-007) — Plan Implementation steps Step 6
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/40_shared/shared_00_document-guide.md