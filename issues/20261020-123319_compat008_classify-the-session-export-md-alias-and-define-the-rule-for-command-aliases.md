# Classify the session export md alias and define the rule for command aliases

## Priority
Low

## Summary
Decide whether `md` in `/session export md` is an official short name for `markdown` or a temporary compatibility alias, and make the usage text, help, documentation, and tests say the same thing. Define one short rule that separates official aliases from temporary compatibility aliases, so the next alias does not need this investigation.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility candidates. It read documents only; the facts below were re-checked against the current code, tests, and documents on 2026-10-20.
- `_session_export()` in `scripts/agent/commands/cmd_session.py` accepts `markdown` or `md` and maps both to the internal format name `md`; it accepts `json`; any other argument is taken as the output file name. (Explicit in code)
- The usage line in the handler, the command help text, and the argument specification list only `markdown|json`, with `markdown` as the default. (Explicit in code)
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` says `md` is accepted as an alias for `markdown` and that any argument that is not a format is taken as the output file. It gives no reason for the alias and no end date. (Documentation only)
- A test exercises `export md <file>`, so the alias is covered. (Verified by test)
- The investigation found no statement that `md` exists for compatibility; the alias may only be a convenience.

## Problem
The alias is accepted, documented in prose, and tested, but invisible in the usage text and help, and nothing says whether it is meant to stay. A reader cannot tell whether it is a supported short name or a leftover. Because any unrecognized argument becomes the output file name, a mistyped format name such as `markdwon` silently writes a file with that name instead of reporting an error.

## Reason for Change
A small alias is cheap to keep, but an alias with no stated status is how compatibility leftovers accumulate. Deciding its status once, and fixing the rule for later aliases, keeps the command grammar, help, completion, and tests consistent.

## Implementation Intent
- Decide the status first. If `md` is an official short name, list it in the usage text, help, and argument specification and describe it as an official short name; no expiry applies. If it is a temporary compatibility alias, give it an owner, a removal condition, and a warning when used, and plan its removal.
- Define the alias rule in the CLI documentation: an official alias is documented in the usage text and kept; a temporary compatibility alias carries a removal condition and a notice, and is tracked in the compatibility manifest (`compat007`).
- Keep the existing behavior of the file-name argument unless the owner decides a mistyped format should be an error; that would be a separate change.

## Target Files or Areas
- `scripts/agent/commands/cmd_session.py` (usage text and, if the alias is temporary, a notice)
- `scripts/agent/commands/command_defs_list.py` (argument specification and help text)
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` (the export description)
- `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (the alias rule)
- `tests/agent/commands/test_agent_cmd_session.py` (alias and help consistency)
- `tests/agent/commands/test_command_registry_consistency.py` (help and specification consistency)

## Required Changes
- Obtain the owner's decision: official short name or temporary compatibility alias.
- If official: add `md` to the usage text, help, and argument specification, and document it as an official short name.
- If temporary: record the owner and removal condition, add a notice when `md` is used, track it in the compatibility manifest, and file the removal issue.
- Write the alias rule in the command registry document, in present tense.
- Make the usage text, help, argument specification, documentation, and tests agree, and add a test that fails if they disagree.
- Decide whether an unrecognized format-like argument should be an error; if so, file a separate issue.

## Constraints
- Do not change the default format, the JSON output, or the handling of the output file name.
- Do not add a second alias or a hidden spelling.
- The documentation follows the docs content policy: describe the rule and the decision, not the history of the alias; written in English.
- The generated command references must be regenerated, not edited by hand, if the argument specification changes.

## Acceptance Criteria
- The status of `md` is decided and recorded in the CLI documentation.
- The usage text, help, argument specification, documentation, and tests describe the same set of accepted formats.
- The alias rule is written in the command registry document and covers both kinds of alias.
- A test fails if the help or specification and the accepted formats disagree.
- `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/generate_reference_table.py --check`, and the Agent command tests pass.

## Testing Expectations
- Update or add tests in `tests/agent/commands/test_agent_cmd_session.py` and `tests/agent/commands/test_command_registry_consistency.py`.
- `uv run pytest tests/agent/commands`, `uv run mypy --no-namespace-packages`, `uv run ruff check`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_quality.py`, and `uv run python tools/check_docs_content_policy.py --strict`.

## Documentation Impact
Yes. Update the export description and add the alias rule to the command registry document (intent, constraints, failure behavior). Do not record the history of the alias.

## Out of Scope
- Changing the export output, adding formats, or changing where the export is written.
- Making an unrecognized format an error (decide here, implement separately).
- Other command aliases, and the removed slash commands.

## Dependencies
- Related: `compat007` provides the manifest in which a temporary compatibility alias would be tracked; this issue does not need it if `md` is an official short name.
- Sibling-issue check: no open issue under `issues/` touches the session export command.

## Unresolved Questions
- Is `md` a deliberate short name or a compatibility alias, and why was it added? (Needs confirmation; the repository does not record the reason)
- Does any script or habit of existing users rely on `export md`? (Needs confirmation)
- Should a mistyped format name be an error instead of an output file name?

## AI Implementation Instruction
- Do not decide the status of `md` yourself; if the owner has not decided, stop and report the open question.
- Change only the files listed; keep the default format, the JSON output, and the file-name handling unchanged.
- Regenerate generated references with the generator; do not hand-edit them.
- Run the commands in Testing Expectations before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123319
- **Related target files**: `scripts/agent/commands/cmd_session.py`, `scripts/agent/commands/command_defs_list.py`, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`, `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `tests/agent/commands/test_agent_cmd_session.py`, `tests/agent/commands/test_command_registry_consistency.py`
