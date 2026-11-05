## Goal
- Remove the hand-maintained module count from the Index heading of `tools/TOOL_DESCRIPTIONS.md`, so no stale count can exist (`REQ-001`: no count in the heading; `REQ-003`: no reference to the heading breaks).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the heading `## Index (65 modules)` at line 15 of `tools/TOOL_DESCRIPTIONS.md`, rewritten as `## Index`.
- Plan: `plans/20261105-105554_toolsdocsync001_check-index-count-in-tool-descriptions.md`, Plan step 1 (Phase 1).

## Assumptions
- The count is already stale: the heading says 65 while `tools/` holds 66 non-package modules (`tools/proc_step_status.py` was added by commit `91c033e32` without a heading update), and `check_tool_descriptions_sync.py` still reports `No issues found.` because it compares name sets only (verified 2026-11-05).
- No anchor, parser, or text search consumes the heading: `rg` over rules, skills, templates, prompts, routing, tools, tests, docs, and CI configuration found only the heading itself (verified 2026-11-05).
- Plan overlap: `tools/TOOL_DESCRIPTIONS.md` is also targeted by the `toolcli001`, `toolcommon001`, `toolreport001`, `toolwrite001`, and `toolsizegate001` Plans. The designs are compatible: this Plan edits only the Index heading and the others edit different rows or add sections; `toolcli001` records a `Depends on` line for this Plan, so this one-line edit lands first (a sequencing dependency, not a conflict).

## Design decisions
- Delete the number instead of deriving it: nothing consumes it, and a derived check would be new behavior outside the Plan.

## Alternatives considered
N/A: removal is the Issue's stated preference.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Replace the heading line `## Index (65 modules)` with `## Index`.

### Method
- One-line edit; the table that follows the heading is untouched.

### Details
- Keep the blank line and the table header after the heading unchanged.
- Do not touch the sentence above the heading about `check_tool_descriptions_sync.py`.

## Compatibility considerations
N/A: documentation heading; no anchor or parser reads it.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports `No issues found.` (exit 0).
- `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q` passes.
- `rg -n 'Index \(' tools rules skills routing.md` finds no remaining count.

## Completion criteria
- The Index heading contains no number, and the checker and its tests pass unchanged.

## Out of Scope
- Other tables or sections of the document, a count check in the sync checker, and a convention for batch-specific tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the Index heading without the count | Completed | 20261105-165124 | 20261105-165458 | Stale check clean. Changed: tools/TOOL_DESCRIPTIONS.md (Index heading without the count) |
| 2 | Run the sync checker, its tests, and the reference search (`routing.md` "When to run which tool") | Completed | 20261105-165124 | 20261105-165458 | check_tool_descriptions_sync: No issues found.; its 3 tests pass; rg 'Index \(' finds no remaining count; run_validation_gates exit 0; full suite 11616 passed (-n 8); docs N/A: the changed file is itself the documentation deliverable |

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
- **Requirement ID**: `REQ-001` (no count in the heading), `REQ-003` (no reference to the heading breaks)
- **Source issue**: issues/20261104-152002_toolsdocsync001_check-index-count-in-tool-descriptions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105554_toolsdocsync001_check-index-count-in-tool-descriptions.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-155758
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`