# test_check_mcp_docs_consistency.py tests a fully replaced API — entire file (506 lines) fails to collect

## Priority
Medium

## Summary
`tests/tools/test_check_mcp_docs_consistency.py` imports `_ACTIVE_ISSUE_ALLOWLIST`, `DocFile`,
`check_active_inconsistencies`, `check_audit_log_single_format`,
`check_fail_open_workflow_allowlist`, `check_live_discovery_routing`, `check_routing_authority`,
`check_routing_authority_v1tools`, `check_startup_modes`, `check_stdio_active_transport`,
`check_strict_validation_skips_unreachable`, `check_tool_names_routing_input`, and
`check_transport_error_is_error` from `check_mcp_docs_consistency` — none of these symbols exist
in the current module. The entire 506-line test file fails at collection, meaning the
`check-mcp-docs` CI entry point (referenced in `rules/toolchain.md`) has no test coverage at all.

## Reason for Change
`tools/check_mcp_docs_consistency.py`'s own module docstring documents that the original file
was deleted in commit `74906389` ("refactor: remove unsupported MDQ tool/search surface and
stale tool-count doc check") and later "Restored and redesigned" with a completely different
check set: `check_port_drift`, `check_tool_name_drift`, and a `main()` CLI entry point, sharing
`DocFile`/`Issue` dataclasses and generic checks with `tools/check_agent_docs_consistency.py`
via `tools/_docs_consistency_lib.py`. The old catalog-based checks
(`check_active_inconsistencies`, `check_fail_open_workflow_allowlist`, etc.) no longer exist.
The test file predates this rewrite and was never updated, so it silently stopped running.

## Implementation Intent
This is not a small API rename — it is a full test rewrite against the redesigned module. Do
not attempt to patch individual import names; the old checks and their behaviors are gone.
Write new characterization tests against the current `check_port_drift`, `check_tool_name_drift`,
and shared `DocFile`/`Issue` primitives (see `tools/_docs_consistency_lib.py`), covering the
`--skip` flags documented in `check_mcp_docs_consistency.py`'s module docstring
(`links`, `removedfiles`, `commanddrift`, `portdrift`, `tooldrift`, `filerefs`, `funcrefs`).

## Target Files or Areas
- `tests/tools/test_check_mcp_docs_consistency.py` (full rewrite)
- `tools/check_mcp_docs_consistency.py` (reference only)
- `tools/_docs_consistency_lib.py` (reference only, shared primitives)

## Required Changes
- Remove or fully rewrite `tests/tools/test_check_mcp_docs_consistency.py` against the current
  module's actual exported symbols.
- Cover `check_port_drift` and `check_tool_name_drift` with synthetic doc/config fixtures (per
  the file's own stated convention of using synthetic content, not real repo files).
- Cover `main()`'s `--skip` flag handling for the checks it currently supports.

## Acceptance Criteria
- `pytest tests/tools/test_check_mcp_docs_consistency.py` collects and passes.
- The rewritten tests exercise `check_port_drift` and `check_tool_name_drift` behavior, not just
  import success.
- No reference to a removed symbol (`_ACTIVE_ISSUE_ALLOWLIST`, `check_active_inconsistencies`,
  etc.) remains anywhere in the test file.

## Testing Expectations
Unit tests (full rewrite of the file). Run
`PYTHONPATH=scripts pytest tests/tools/test_check_mcp_docs_consistency.py -v` after the rewrite.
Also run `uv run check-mcp-docs` manually to confirm the CLI entry point itself still works,
since this has apparently been unverified since commit `74906389`.

## Documentation Impact
If `rules/toolchain.md`'s "MCP documentation consistency" section (§ `check-mcp-docs`) describes
behavior that no longer matches the redesigned checks, update it. Confirm whether the CI
workflow `.github/workflows/mcp-docs-consistency.yml` (mentioned in the module docstring as
having been silently failing) has since been fixed or still needs attention — flag as a
Known Issue if unresolved.

## Out of Scope
- Do not restore the old catalog-based checks that were intentionally removed in `74906389`.
- Do not modify `tools/check_mcp_docs_consistency.py` or `tools/_docs_consistency_lib.py` logic
  — this issue is test-only.
- Do not touch other collection errors (`TurnContext`, `apply_config_changes`) — those are filed
  as separate issues.

## AI Implementation Instruction
Read `tools/check_mcp_docs_consistency.py` and `tools/_docs_consistency_lib.py` in full before
writing any test code — the old test file's structure is not a reliable guide to the new API's
shape. Write fresh, synthetic-fixture-based tests; do not try to preserve old test names or
structure if they don't map cleanly to current functions. Stop and report if
`.github/workflows/mcp-docs-consistency.yml`'s current state cannot be determined from the repo
alone.
