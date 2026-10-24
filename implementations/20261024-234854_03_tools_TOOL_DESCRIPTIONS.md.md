## Goal
- State in `tools/TOOL_DESCRIPTIONS.md` that an empty or partial glob match set makes `check_docs_structure.py` fail (`REQ-005`: document the empty-match error).

## Scope
- Edit the detail-table row of `check_docs_structure.py` (line 114 at time of writing); the summary row (line 34) gets a short addition only if it fits its one-line style.

## Assumptions
- Neither row mentions empty-match behavior (grep 2026-10-24).
- The detail row already ends its usage text with `Usage: uv run python tools/check_docs_structure.py [glob ...]`; the new sentence goes right after it.

## Design decisions
- One added sentence: a glob matching no file is reported on stderr as `no files matched the given glob(s)` and the tool exits non-zero, including when only some globs match.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Append the sentence to the `check_docs_structure.py` detail row.
2. Leave the summary row unchanged unless it already lists exit behavior.

### Method
- Edit in place with a unique `old_string` taken from the Usage sentence.

### Details
- Do not add or rename any tool row; the sync checker compares file names only.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports no drift.

## Completion criteria
- The detail row states the empty and partial match failure; the sync checker passes.

## Out of Scope
- Any other tool's description and any change to `tools/*.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the empty/partial-match sentence to the `check_docs_structure.py` row | Pending | — | — | |
| 2 | Run `tools/check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (document the empty-match error)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234854
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
