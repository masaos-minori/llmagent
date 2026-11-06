# Installed console scripts cannot import the tools package

## Priority
Low

## Summary
`uv run check-needs-confirmation` fails with `ModuleNotFoundError: No module named 'tools'`, although `python tools/check_needs_confirmation_inventory.py` and `python -m tools.check_needs_confirmation_inventory` work.

## Background
`pyproject.toml` declares console scripts `check-needs-confirmation = "tools.check_needs_confirmation_inventory:main"` and `check-tool-descriptions = "tools.check_tool_descriptions_sync:main"` (and the docs-consistency entries). `rules/toolchain.md` mentions `uv run check-mcp-docs` and `uv run check-agent-docs` as shorthand. Observed on 2026-11-06 in the development environment: the installed entry point imports `tools` from an environment where the repository root is not on `sys.path`. The cause is not confirmed.

## Problem
The documented shorthand commands fail, while the equivalent module and path forms work.

## Reason for Change
A documented command that fails erodes trust in the toolchain documentation.

## Implementation Intent
Find out why `tools` is not importable from the installed scripts (packaging configuration, editable install, or the `tools` directory not being a packaged module) and either fix the packaging or remove the console scripts and the documentation that cites them.

## Target Files or Areas
`pyproject.toml` (`[project.scripts]` and the packaging table), `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md`.

## Required Changes
- Reproduce on a clean `uv sync`.
- Fix the packaging so the console scripts import `tools`, or remove the scripts and update every document that names them.

## Constraints
Keep `python tools/<name>.py` and `python -m tools.<name>` working; do not change what any tool checks.

## Acceptance Criteria
- Every documented console script runs, or no document names a script that cannot run.
- The three invocation forms in `tools/TOOL_DESCRIPTIONS.md` stay accurate.

## Testing Expectations
Run each console script after a clean `uv sync`; `uv run python tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes: `rules/toolchain.md` and `tools/TOOL_DESCRIPTIONS.md` if scripts are removed or the packaging changes.

## Out of Scope
Choosing the standard invocation form for all tools (a separate owner decision).

## Dependencies
N/A: none

## Unresolved Questions
- Whether the console scripts are used outside this repository (not searchable from here).
- Whether `tools` is meant to be an installable package.

## AI Implementation Instruction
Reproduce first; do not change tool behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-123523
- **Related target files**: `pyproject.toml`, `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md`
