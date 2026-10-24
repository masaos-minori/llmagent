# Implementation Procedure: tools/TOOL_DESCRIPTIONS.md

## Goal

State in both `check_docs_structure.py` entries (summary table and detail table) that a glob
matching zero files is reported as an error with a non-zero exit (`REQ-005` docs/description
update; AC-4 sync check).

## Scope

- Edit the summary row (`:34`) and the detail row (`:114`) of `tools/TOOL_DESCRIPTIONS.md` only.
- No other tool entry changes.

## Assumptions

- Neither entry mentions empty-match behavior today (grep 2026-10-24); both are one-line table
  rows kept one line after the edit.
- `check_tool_descriptions_sync.py` compares file names, not descriptions, so text edits cannot
  introduce drift as long as the tool name strings stay intact.

## Design decisions

- Append to the existing Usage sentence: "A glob that matches no files is an error: the pattern is
  reported and the tool exits non-zero." — matches the `REQ-001` message semantics without
  restating the whole tool contract.

## Alternatives considered

N/A: docs-only wording change in an existing row; no structural alternative applies.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Summary row `:34`: extend the short description, e.g. `Validate structural conventions of
   docs/*.md; a glob matching no files is an error`.
2. Detail row `:114`: insert the empty-match sentence immediately before the `Usage:` sentence.

### Method

Detail-row sentence to add: `A glob pattern that matches no files is reported as an error
(no files matched the given glob(s)) and the tool exits non-zero; per-file findings from patterns
that did match are still reported.`

### Details

- Observed while reading the row (out of scope, flagged not fixed): the detail row says `--schema`
  "is disabled by default", while `main()` is default-on against the canonical schema when
  `--schema` is omitted (`check_docs_structure.py:494-499`). Not part of `REQ-005`; surface to the
  owner separately.

## Compatibility considerations

- Table row format must stay valid Markdown single-line rows (the file is parsed for name sync).

## Security considerations

N/A: documentation wording only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` → no drift (AC-4).
- `uv run python tools/check_workitem_structure.py` and `uv run python tools/stale_detector.py`
  clean for this document.

## Completion criteria

- Both entries state the empty-match = error behavior; the sync checker passes; tool name strings
  unchanged (AC-4).

## Out of Scope

- The `--schema` default-on wording discrepancy noted in Details (owner decision).
- `docs/00_governance/governance_04_documentation-checks.md` (procedure doc `20261024-235840_04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the two table rows | Pending | — | — | |
| 2 | Run `check_tool_descriptions_sync.py` + docs checkers | Pending | — | — | routing.md Tools |

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
- **Requirement ID**: `REQ-005` (tool description must state empty-match error)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235840
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
