# Consolidate output-truncation and dry-run message templates in `git/format_output.py`

## Priority
Low

## Summary
`scripts/mcp_servers/git/format_output.py` has two related duplication patterns not addressed
during its 2026-08-14 refactor cycle:
1. `format_show`'s byte-limit truncation logic (`GIT_SHOW_OUTPUT_MAX_CHARS`) is not shared with
   any other MCP server's output-truncation logic, despite the same concern existing elsewhere
   in `scripts/mcp_servers/`.
2. `format_add`, `format_commit`, `format_checkout`, `format_pull`, and `format_push` each repeat
   an `if req.dry_run: return "[DRY RUN] ..."` branch with a distinct message template per
   function.

## Reason for Change
Both patterns were identified as genuine duplication during the refactor cycle but deferred
because truncation and dry-run message wording are both visible-output-sensitive — any
consolidation risks silently altering the exact truncation boundary or wording that callers/
tests may depend on verbatim, which is out of scope for a behavior-preserving refactor cycle
without explicit review of the resulting output diffs.

## Implementation Intent
For truncation: before any consolidation, enumerate every MCP server module with similar
byte/char-limit truncation logic (not just this file), and add snapshot/characterization tests
pinning the exact truncated output at `len == max`, `len == max+1`, `len == max-1` boundaries for
each, before extracting a shared utility.

For dry-run messages: enumerate the current exact wording of each of the 5 dry-run templates in
this file (already captured by the file's own 32-test characterization suite added 2026-08-14),
and only extract a shared `_dry_run_or(...)` helper if a maintainer confirms the wording
differences are intentional stylistic variation vs. accidental drift that should be unified.

## Target Files or Areas
- `scripts/mcp_servers/git/format_output.py`
- Unknown: other MCP server formatter modules with similar truncation logic (identify via `rg`
  for byte/char-limit constants across `scripts/mcp_servers/**/format*.py` and
  `**/*formatter.py`)

## Required Changes
- Enumerate all truncation-limit constants across `scripts/mcp_servers/` before proposing a
  shared utility.
- Add boundary characterization tests (at/over/under the limit) for each truncation site found.
- For dry-run messages: get explicit confirmation on whether the 5 current wordings should be
  unified before extracting a shared template.

## Acceptance Criteria
- If a shared truncation utility is introduced: byte-for-byte identical truncated output at all
  tested boundaries, for every consolidated call site.
- If dry-run templates are unified: explicit maintainer sign-off recorded, and all 32 existing
  `test_format_output.py` characterization tests updated to match the (deliberately changed)
  wording, with the change called out in the PR description.

## Testing Expectations
Full `tests/mcp_servers/git/test_format_output.py` suite plus any other affected formatter
test files; new boundary tests for truncation.

## Documentation Impact
None expected unless dry-run wording changes are visible in `docs/04_mcp_*` tool-output examples
— check before assuming no impact.

## Out of Scope
- Do not change any exact output string without first confirming (via characterization tests
  and, for wording changes, maintainer sign-off) that the change is intentional.
- Do not bundle unrelated `format_output.py` changes into this issue.

## AI Implementation Instruction
Treat this as two independent sub-tasks (truncation consolidation, dry-run message
consolidation) that can be implemented and reviewed separately. Do not implement either without
the boundary/characterization evidence described above, since both touch visible MCP tool output.
