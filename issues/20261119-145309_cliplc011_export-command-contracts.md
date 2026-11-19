# Make export and command contracts Markdown-safe and registry-consistent

## Priority
Medium

## Summary
Harden Markdown export and normalize command naming, module ownership, parsing, help, completion, and unknown-subcommand behavior.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 11).

Evidence (`Explicit in code`, by `rg`): `scripts/agent/services/export_formatter.py:40` wraps tool output in a fixed triple-backtick fence; `/compact` is defined in `scripts/agent/commands/cmd_rag_export.py` and registered in `command_defs_list.py:83`; `/stats` is defined in `cmd_config_stats.py`. The claims about export argument parsing, `/debug`, `/set`, `/mcp` without arguments, and echoing of unknown command input are from the backlog and `Needs confirmation`.

## Problem
Export breaks when tool output contains the same fence; export silently treats unknown tokens as filenames; command ownership, naming, and error behavior are inconsistent across modules and documents.

## Reason for Change
Contract consistency of the command surface; moderate risk (malformed export, misleading docs), no data loss.

## Implementation Intent
Export is valid for arbitrary content; each command has one implementation owner, one canonical usage definition, and one error contract; help, completion, registry, and documents list the same command set.

## Target Files or Areas
- `scripts/agent/services/export_formatter.py`, `scripts/agent/commands/cmd_session.py`, `cmd_rag_export.py`, `cmd_debug.py`, `cmd_mcp.py`, `command_defs_list.py`, `registry.py`
- CLI command documentation under `docs/23_agent/`

## Required Changes
- Export: a fence longer than the longest backtick run or a safe alternative; escape tool call ids and structural metadata; a formal argument parser; reject unknown formats and multiple output files; add `--output` and quoted filename support; preserve UTF-8 and newlines.
- Commands: move `/compact` to a history or context module and keep one canonical document; raise `UnknownSubcommandError` from `/debug`; document `/stats` as aggregate counts only; remove `/set` references and point to `/reload`; decide whether bare `/mcp` is a status alias or a usage error; show only the unknown command token; add a CI check comparing command definitions, help, completion, and documentation.

## Constraints
- Uses the final CLI input and error contracts of `issues/20261119-145259_cliplc001_repl-input-controller.md`.
- Changes to command names or flags are user-visible.

## Acceptance Criteria
- [ ] Exported Markdown remains valid for arbitrary tool text; invalid export arguments produce usage errors.
- [ ] Every documented command exists; every command has one canonical specification and common error behavior.
- [ ] Unknown-command output does not echo sensitive arguments.

## Testing Expectations
- Embedded backtick runs, Markdown injection, Unicode, and newline variants; unknown format, duplicate output, quoted filename; help, completion, registry, and documentation set equality; common unknown-subcommand handling.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. One canonical specification per command; remove `/set`; document `/stats` scope.

## Out of Scope
- The final documentation rewrite (`issues/20261119-145312_cliplc014_cli-docs-consolidation.md`).

## Dependencies
- Depends on `issues/20261119-145259_cliplc001_repl-input-controller.md`.

## Unresolved Questions
- `不明`: bare `/mcp` behavior (status alias or usage error).
- `不明`: the target module for `/compact`.

## AI Implementation Instruction
Write the nested-fence export test first. Keep command renames minimal and documented. Stop and report any command whose removal would break a documented workflow.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145309
- **Related target files**: `scripts/agent/services/export_formatter.py`, `scripts/agent/commands/cmd_session.py`, `scripts/agent/commands/cmd_rag_export.py`, `scripts/agent/commands/cmd_debug.py`, `scripts/agent/commands/cmd_mcp.py`
