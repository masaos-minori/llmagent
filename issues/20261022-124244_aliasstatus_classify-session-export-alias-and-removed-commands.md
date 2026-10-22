# Classify the session export alias and cover every removed command with a test

## Priority
Low

## Summary
Record the status of the `md` input alias of `/session export` (permanent or temporary), and add a removal test for each deleted slash command that does not yet have one.

## Background
`memo-issue.md` item L-01 asked to classify CLI aliases and to enforce the removal of deleted commands. Checked against current source:
- `scripts/agent/commands/cmd_session.py` (`_session_export`) accepts `markdown` and `md` as the Markdown format (both map to the internal name `md`) and `json`; the usage line and `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` list only `[markdown|json]`. So `md` is an accepted but undocumented input form, and there is no recorded decision whether it is permanent.
- `tests/agent/commands/test_removed_commands.py` asserts that `/db` and the note command are not registered. `/diff`, `/system`, `/audit`, and `/workflow` do not appear in that file; they appear in other test files (`test_agent_cmd_context.py`, `test_repl.py`, `test_orchestrator.py`), and it is not confirmed from the search whether those tests check that the commands are rejected. The removed-name patterns of `tools/check_compat_shims.py` also guard documentation against presenting removed commands as current.
- None of the five names is registered in `scripts/agent/` source (search of string literals).

## Problem
The `md` alias has no stated status, so it may be removed or kept by accident, and the removal of four deleted commands is not demonstrably locked by a dedicated test.

## Reason for Change
A small, explicit decision and a regression test per removed command keep the command contract unambiguous and prevent a removed command from returning silently.

## Implementation Intent
Decide whether `md` is a permanent short alias; if permanent, document it as current behavior in the usage line and the command document; if temporary, assign an owner, a warning behavior, and a removal condition. Extend `test_removed_commands.py` (or the command contract tests) so each of the five names is checked to be absent from the registry, help, and completion data and to be rejected as an unknown command.

## Target Files or Areas
- `scripts/agent/commands/cmd_session.py` (usage text, and warning behavior only if the alias is temporary)
- `tests/agent/commands/test_removed_commands.py`
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
- Help and completion definitions under `scripts/agent/commands/` (read to verify; edit only if a removed name is found)

## Required Changes
- Record the status decision for the `md` alias and apply it to the usage text and document.
- Verify, by running the existing tests, which removed commands are already covered, and add the missing tests for `/diff`, `/system`, `/audit`, and `/workflow` (and `/db` if the existing one is only registry-level).
- Keep the removed-name documentation check and the command contract tests consistent.

## Constraints
- Do not change the export content or the formats supported.
- A documented command usage must match the command contract check (GV-023).
- Follow the existing test style.

## Acceptance Criteria
- The `md` alias has one documented status and the usage line matches the behavior.
- Each removed command is covered by a test that checks it is unregistered and rejected as unknown.
- `check_docs_consistency.py --domain agent`, the command contract checks, `ruff`, `mypy --no-namespace-packages`, and the full suite pass.

## Testing Expectations
- `uv run pytest tests/agent/commands -q`, the agent-domain documentation check, then the full suite once.

## Documentation Impact
Yes if the alias is documented or deprecated; one usage form in the session command document.

## Out of Scope
- General CLI redesign, export content changes, and non-CLI API compatibility.

## Dependencies
- Related: the command contract check (GV-023) in `tools/check_docs_consistency.py`.
- Sibling-issue check: no open issue under `issues/` and no active plan under `plans/` touches these files.

## Unresolved Questions
- Is `md` intended as a permanent short alias? Unknown; no decision is recorded.
- Do the existing tests that mention `/diff`, `/system`, `/audit`, and `/workflow` already check rejection as unknown commands? Not confirmed.
- Is there CLI usage telemetry for the alias? Unknown; none in the repository.

## AI Implementation Instruction
Do not change the formats or the export output. Obtain the alias decision before editing the usage text; stop and report if it is missing. Add tests only for commands not already covered, after running the existing tests.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261022-124244
- **Related target files**: scripts/agent/commands/cmd_session.py, tests/agent/commands/test_removed_commands.py, docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md
