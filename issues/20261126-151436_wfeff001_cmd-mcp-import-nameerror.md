# Fix the import-time NameError in the /mcp command module

## Priority
High

## Summary
`scripts/agent/commands/cmd_mcp.py` raises `NameError: name 'RuntimeToolRegistry' is not defined` when it is imported, so the command registry cannot be imported and every test that imports it errors. Make the module importable again and add a guard so an annotation-only import cannot break module import silently.

## Background
Evidence (`Explicit in code`, by reading and by running `import agent.commands.cmd_mcp` from `scripts/`): `RuntimeToolRegistry` is imported only under `TYPE_CHECKING` (`cmd_mcp.py` lines 24-25), the module has no `from __future__ import annotations` (19 of the 26 modules under `scripts/agent/commands/` have it), and `_write_tool_summary` annotates a parameter as `RuntimeToolRegistry | None`, which Python evaluates when the `def` runs. `scripts/agent/commands/registry.py` imports `_McpMixin` from this module at module level, and `scripts/agent/startup_component_init.py` imports `CommandRegistry` inside `initialize()` at run time, so the failure sits on the Agent startup path (reading only; not run end to end).

The module was last changed by commit `f0334b72f` (2026-11-25, staged reload transaction). A full test run on 2026-11-26 showed 26 failed and 88 errors, all in `tests/agent/` and `tests/docs/test_command_docs_sync.py`, all from this one error; no failing test touches a file changed that day.

## Problem
Importing `agent.commands.registry` fails, so the REPL command table cannot be built. Whether the deployed `/opt/llm` copy contains the failing commit is `不明`.

## Reason for Change
Startup or correctness failure of the Agent and a permanently red test suite that hides new failures. Time-sensitive: every full-suite run now needs manual triage.

## Implementation Intent
Make annotation evaluation lazy for this module in the way the sibling command modules already do, without changing `/mcp status` behavior. Keep the change to the import mechanism.

## Target Files or Areas
- `scripts/agent/commands/cmd_mcp.py`
- `tests/agent/commands/` (a guard test that imports every command module)

## Required Changes
- Defer evaluation of the annotations in `cmd_mcp.py` (the pattern of the other command modules).
- Check the other modules under `scripts/agent/commands/` that are not covered by that pattern for the same defect and report any.
- Add a test that imports every module under `scripts/agent/commands/` so a runtime import failure of one module names that module.

## Constraints
- No change to `/mcp status` output or to the command registry contents.
- Do not add a runtime import of `shared.runtime_tool_registry` just to satisfy an annotation if lazy evaluation is enough.

## Acceptance Criteria
- [ ] `import agent.commands.cmd_mcp` and `import agent.commands.registry` succeed.
- [ ] The 26 failed tests and 88 errors listed in Background pass, with no other test newly failing.
- [ ] The guard test fails when a command module has an import-time error.

## Testing Expectations
Run the guard test, `tests/agent/commands/`, `tests/agent/test_repl.py`, `tests/docs/test_command_docs_sync.py`, ruff, mypy, and the full suite.

## Documentation Impact
Not required.

## Out of Scope
- Any other behavior change in `/mcp` or the registry.
- A baseline mechanism for known test failures (issues/20261126-151437_wfeff002_test-failure-baseline.md).

## Dependencies
- Related: issues/20261126-151437_wfeff002_test-failure-baseline.md (once this is fixed the current known-failure set is empty).

## Unresolved Questions
- `不明`: whether the deployed `/opt/llm` Agent already runs the failing commit.

## AI Implementation Instruction
Reproduce the failure first. Keep the diff to the import mechanism and the guard test. Stop and report if another module shows a different import-time defect.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151436
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/`
