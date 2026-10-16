# Remove the diff, system, and audit slash commands

## Priority
Medium

## Summary
Remove the `/diff`, `/system`, and `/audit` slash commands from the Agent CLI, with no alias, shim, forwarding path, or hidden flag, and add fail-closed guards: the removed command names are rejected as unknown commands and their reintroduction in current specifications is detected by `GV-017`. A fourth command named in the source directive, `/workflow`, is not registered today; for it only the `GV-017` guard and a rejection test are added.

## Background
Source directive: `memo3.md` (2026-10-16), a breaking command-surface reduction. Verified against the repository on 2026-10-16 (inventory, task 1 of the directive):
- `/diff`: `CommandDef` in `scripts/agent/commands/command_defs_list.py` (async, no arguments); handler `_cmd_diff` in `scripts/agent/commands/cmd_context.py` with helpers `_collect_diff_touched_paths`, `_group_paths_by_repo`, `_print_repo_diffs`, and the constant `_DIFF_TOUCHED_TOOL_NAMES`; it derives the touched files from tool calls in the conversation history and calls the `git_diff` tool.
- `/system`: `CommandDef` (prefix, argument `name`); handler `_cmd_system` in `cmd_context.py`, which calls `switch_system_prompt` in `scripts/agent/services/conversation_service.py` (its only caller).
- `/audit`: `CommandDef` with subcommands `tail`, `turn`, and `tool`; the whole module `scripts/agent/commands/cmd_audit.py` (`_AuditMixin`) reads the audit log file named by `cfg.obs.audit_log_file`; `registry.py` documents the mixin in its module docstring and composes it.
- `/workflow`: no `CommandDef`, no handler, and no occurrence as a command in scripts, tests, docs, or tools (only paths such as `scripts/agent/workflow/` match a plain search).
- Remaining references to the three commands: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (index), `agent_07_08_cli-and-commands-slash-commands-context-plan.md` (`/system`), `agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` (`/diff`, `/audit`), `agent_02_runtime-architecture.md` (`/diff` in an enforcement table), and tests including `tests/agent/commands/test_agent_cmd_context.py`, `tests/agent/commands/test_cmd_audit.py`, `tests/docs/test_command_docs_sync.py`, and `tests/tools/test_check_docs_consistency_checks.py` (which uses `/audit` as a fixture).
- `GV-017` is implemented by `_REMOVED_NAME_PATTERNS` in `tools/check_compat_shims.py` (11 patterns, none for a command name; status Partial, severity Warning in `governance_04`).
- No command-completion code exists in `scripts/agent` (the matches for "completion" are LLM completions).

## Problem
The three commands are part of the supported CLI contract that must be implemented, documented, tested, and covered by `GV-023`, although they are no longer wanted: they expose repository-diff, prompt-selection, and audit information through the REPL, overlapping other interfaces. There is also no guard that keeps removed command names out of current specifications.

## Reason for Change
Reduce the CLI to commands with a clear, current responsibility and an actively maintained contract, and make the removal permanent by checking for reintroduction.

## Implementation Intent
- Delete the three registry entries, the handlers and helpers used only by them, and the mixin module for `/audit`; keep every shared service that a supported path still uses.
- Make the removed names fail like any unknown command, with a test per name that also shows no state is changed.
- Add the command names (including `/workflow`) to the removed-name patterns of `GV-017` so that only command-like uses match, not ordinary words.
- Update current documentation and tests to the reduced command set.

## Target Files or Areas
- `scripts/agent/commands/command_defs_list.py`, `cmd_context.py`, `cmd_audit.py` (delete), `registry.py`, `scripts/agent/services/conversation_service.py` (`switch_system_prompt`, if no other caller remains)
- `tools/check_compat_shims.py` (`_REMOVED_NAME_PATTERNS`), `tools/check_docs_consistency.py` and `tests/tools/` only if `GV-023` expectations or fixtures name the removed commands
- Tests: `tests/agent/commands/test_agent_cmd_context.py`, `test_cmd_audit.py`, `tests/docs/test_command_docs_sync.py`, `tests/tools/test_check_docs_consistency_checks.py`, and the tests of `check_compat_shims`
- Docs: `agent_07_03`, `agent_07_08`, `agent_07_09`, `agent_02_runtime-architecture`, `governance_04` (`GV-017` description), and any Operations, Security, or Workflow document that tells an operator to use a removed command (to be confirmed with `rg` at plan time)
- Generated references (for example `agent_13_reference-api-generated.md`, `agent_11_04`), regenerated with `tools/generate_reference_table.py`

## Required Changes
- Remove the `/diff`, `/system`, and `/audit` `CommandDef` entries and every alias or spelling; remove their dispatch, argument parsing, usage text, and the `_AuditMixin` composition from `registry.py`.
- Delete `_cmd_diff` with `_collect_diff_touched_paths`, `_group_paths_by_repo`, `_print_repo_diffs`, `_DIFF_TOUCHED_TOOL_NAMES`, `_cmd_system`, and `cmd_audit.py`; remove imports that become unused (for example `git`, `orjson`, `check_preflight`) after confirming with static analysis.
- Remove `switch_system_prompt` only if no non-command caller exists; keep system-prompt configuration and startup selection (`startup_prompt_setup.py`, `system_prompts` config) unchanged.
- Keep audit generation, persistence, and redaction unchanged (`audit_log_file`, `factory.py`, `audit_event_emitter.py`).
- Add `GV-017` patterns for `/diff`, `/system`, `/audit`, and `/workflow` that match command usage and not words such as `workflow`, `audit`, `system`, or `diff`; add tests for detection and for the historical-context exemption.
- Add rejection tests for all four names: unknown-command result, no mutation of session, workflow, audit, prompt, file, or configuration state, and absence from `/help`.
- Update the docs, the `GV-017` description, and the generated references; keep any historical mention only in an approved release-note or migration-history context.

## Constraints
- No alias, forwarding handler, deprecated shim, hidden registration, or reactivating flag; this is an intentional breaking change without a deprecation period.
- Do not remove the Workflow Engine, audit logging, system-prompt configuration, or any file-change tracking used by a supported feature (these are out of scope).
- Follow `skills/DESIGN.md` Docs content policy for documentation edits; `docs/` is English.
- Tests must not open production DBs or write the real audit log.

## Acceptance Criteria
- `/diff`, `/system`, `/audit`, and `/workflow` are rejected with the standard unknown-command result, and the rejection changes no state.
- No alias, shim, forwarding path, hidden flag, or alternate spelling runs any of them; `/help` and generated references do not list them.
- Current documentation does not present them as supported commands; `GV-017` detects reintroduction of each name in a current specification.
- `GV-023` passes with the reduced command set; the full Agent command tests, static analysis, the docs checkers, and the generated-reference check pass.
- Workflow Engine behavior, audit generation and persistence, system-prompt startup selection, and any retained file-change tracking are unchanged (confirmed by tests or code reading recorded in the plan).
- A repository search for the four spellings leaves only approved historical references and removed-name test fixtures.

## Testing Expectations
- Unit tests for the registry and dispatch (rejection of the four names), `GV-017` pattern tests (hit on command use, no hit on ordinary words, historical exemption), and `GV-023` with the reduced set.
- Run the Agent command tests, `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`, `bandit`, the full suite, and the docs checkers named in `routing.md`.
- Regenerate the generated references and run `tools/generate_reference_table.py --check`.

## Documentation Impact
Yes: remove the commands from the command index and per-command chapters, from the runtime-architecture enforcement table, and from any operator procedure; update the `GV-017` description; regenerate guarded blocks; do not hand-edit generated blocks.

## Out of Scope
- Removing the mandatory Workflow Engine or its persistence, audit logging, audit persistence or redaction, system-prompt configuration used outside the slash command, and file-change tracking used by supported features.
- Introducing replacement commands (needs a separate issue).
- Changes to the `/memory` command contract (see the open `/memory` plan).

## Dependencies
- Overlaps with the `/memory` contract Plan (`plans/done/20261016-143248_plan.md`, implementation procedures under `implementations/20261016-145841_*`): both edit `scripts/agent/commands/command_defs_list.py`, the `GV-023` checks and documents, and the command chapters. Sequence them (implement the `/memory` procedures first, or coordinate the edits) and re-verify this issue against current source before planning.
- No other open issue under `issues/` covers these commands.

## Unresolved Questions
- Which documents count as an "approved release note or migration-history context" for keeping a historical mention; none was identified in this review.
- Whether any script, automation, or external caller invokes the commands through the REPL (not found in the repository; operational use is unknown).
- Whether `switch_system_prompt` has callers outside the repository's `scripts/` (none found inside it).
- Which operations, security, or workflow documents instruct operators to use the commands; the search to settle this belongs to the planning step.

## AI Implementation Instruction
Implement only what this issue states. Remove command-only code, keep shared services, and prove it with static analysis and tests; do not add compatibility behavior. Re-run the repository search for the four spellings after the change and classify every match. Stop and ask if a retained capability turns out to depend on code that this issue removes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-162117
- **Related target files**: scripts/agent/commands/command_defs_list.py, scripts/agent/commands/cmd_context.py, scripts/agent/commands/cmd_audit.py, scripts/agent/commands/registry.py, tools/check_compat_shims.py
