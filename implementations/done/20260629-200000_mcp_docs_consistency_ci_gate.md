# Implementation Design: MCP Documentation Consistency CI Gate Closure

## Goal

Close the gaps between the existing MCP docs consistency check implementation and its acceptance criteria by adding an allowlist for intentionally uncited issue IDs, a tool count check, local-run instructions, and unit tests.

## Scope

- **In-Scope**:
  - Add `_ACTIVE_ISSUE_ALLOWLIST` to `scripts/check_mcp_docs_consistency.py` for MCP-01, MCP-02, MCP-04, MCP-06, MCP-07, MCP-08 (intentionally uncited in other MCP docs)
  - Update `check_active_inconsistencies()` to respect the allowlist
  - Add `check_tool_counts()` function that compares documented tool counts against canonical frozensets
  - Add `--skip toolcount` option to CLI
  - Remove `--skip active` from `.github/workflows/mcp-docs-consistency.yml`
  - Add local-run instructions to `rules/toolchain.md`
  - Add unit tests in `tests/test_check_mcp_docs_consistency.py`
- **Out-of-Scope**:
  - Full documentation generation
  - Deep semantic validation
  - Changes to StartupMode enum or runtime behavior

## Affected Files

1. `scripts/check_mcp_docs_consistency.py` — add allowlist, tool count check, CLI option
2. `.github/workflows/mcp-docs-consistency.yml` — remove `--skip active`
3. `rules/toolchain.md` — add MCP docs consistency section
4. `tests/test_check_mcp_docs_consistency.py` — new file with unit tests

## Implementation Steps

1. Add `_ACTIVE_ISSUE_ALLOWLIST` frozenset with MCP-01, MCP-02, MCP-04, MCP-06, MCP-07, MCP-08
2. Update `check_active_inconsistencies()` to skip allowlisted issues
3. Add `_SERVER_TOOLS_MAP` dict mapping server names to their canonical frozenset tool lists
4. Add `check_tool_counts()` function that compares documented counts against `_SERVER_TOOLS_MAP`
5. Add `_TOOL_COUNT_RE` regex for matching `Tools(N)` patterns in docs
6. Add `--skip toolcount` CLI option
7. Remove `--skip active` from CI workflow
8. Add local-run instructions to `rules/toolchain.md`
9. Add unit tests for all five checks

## Acceptance Criteria

- [x] Active check respects allowlist — no false warnings for intentionally uncited issues
- [x] Tool count check compares against canonical frozensets (WARNING severity)
- [x] CI workflow runs all checks without `--skip`
- [x] Local-run instructions present in `rules/toolchain.md`
- [x] Unit tests cover all five checks with synthetic doc content
