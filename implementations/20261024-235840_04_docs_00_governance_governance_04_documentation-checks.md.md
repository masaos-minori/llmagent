# Implementation Procedure: docs/00_governance/governance_04_documentation-checks.md

## Goal

Document the new failure mode in §8 "Documentation Structure Validation
(`check_docs_structure.py`)": a glob matching zero files is reported as an error with a non-zero
exit (`REQ-005`; AC-2 shows the unchanged `docs/**/*.md` usage stays valid).

## Scope

- §8 only: the check list (around `:167-176`) and the Usage block (`:178-181`).
- No new chapter, no GV table row, no change to any other section of the file.

## Assumptions

- §8 currently lists the per-file checks and two usage commands with no empty-match statement
  (read 2026-10-24); the Issue's "no docs chapter describes the checker" claim was already
  corrected by the Plan (this section exists).
- `docs/00_index.md` needs no row: this is an edit of an existing registered document, not a new
  file.

## Design decisions

- Add one bullet to the §8 check list plus one sentence after the Usage block — the file's existing
  pattern for describing checker behavior; prose stays English, tool-facing text mirrors the
  `REQ-001` message.

## Alternatives considered

N/A: docs-only wording change in an existing section; no structural alternative applies.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Append to the §8 check list: `- A glob pattern that matches no files is reported as an error
   (the pattern(s) are named on stderr) and the tool exits non-zero; findings from patterns that
   did match are still reported.`
2. After the Usage code block, add: `With no glob argument the default pattern `docs/**/*.md` is
   used.` (one line; matches `check_docs_structure.py:480`).

### Method

Both insertions stay inside §8 so the section ordering and `##` heading structure of the file are
untouched.

### Details

- The §8 check list is a bullet list; the new bullet takes the same style as the existing six.

## Compatibility considerations

- `check_docs_structure.py "docs/**/*.md"` must still pass on this edited file (it validates the
  docs tree itself, AC-2); the edit adds no headings or links that could violate its checks.

## Security considerations

N/A: documentation wording only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py "docs/**/*.md"` → exit `0` (AC-2).
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`
  → clean (Plan target-row validators).
- `uv run python tools/check_workitem_structure.py` and `uv run python tools/stale_detector.py`
  clean for this document (routing.md Tools).

## Completion criteria

- §8 states the empty-match error behavior and the default-glob usage; the three doc checkers and
  the checker's own self-run on `docs/**/*.md` are clean (AC-2, AC-4).

## Out of Scope

- `tools/TOOL_DESCRIPTIONS.md` (procedure doc `20261024-235840_03`).
- Any GV-numbered table changes (the Plan adds no new GV row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the §8 bullet and usage sentence | Pending | — | — | |
| 2 | Run the docs checkers + `check_docs_structure.py` self-run | Pending | — | — | routing.md Tools |

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
- **Requirement ID**: `REQ-005` (governance docs must state the new failure mode)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235840
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
