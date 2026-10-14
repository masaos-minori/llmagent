# Remove the mdq slash command

## Priority
Low

## Summary
Remove the `/mdq` slash command so that MDQ is reachable only through the normal LLM tool-selection and MCP execution path. Keep `mdq-mcp`, `mdq.sqlite`, the MDQ tools, the MDQ/RAG classifier, and `mdq_rag_mode`. Source: `memo2.md` (procedure document v1.0, 2026-10-13).

## Background
`/mdq` (status, index, refresh, search, outline, get, grep) calls MDQ MCP tools through the agent's tool executor. `memo2.md` proposes deleting it, replacing it with ordinary requests to the LLM, and recording the removal for GV-017. It is the follow-up to the removal of `/skill`, and `memo2.md` section 15 lists `/approve` and `/reject` as later separate removals. `memo2.md` was written without confirmed source inspection; its targets must be checked against current code.

## Problem
- A second REPL path reaches `mdq-mcp` besides the normal LLM and MCP path.
- The `/mdq` handler duplicates MDQ tool-call preflight and output handling in the CLI layer.

## Reason for Change
Consolidate MDQ access into one path (LLM tool selection, `RuntimeToolRegistry`, MCP), removing a command, a mixin, and its tests and documentation.

## Implementation Intent
Delete only the command, its handler mixin, registration, and tests. Do not touch the MDQ server, classifier, or configuration. Typing `/mdq` after the change gives the existing unknown-command message with no compatibility alias. Document the canonical path, and register the removed command name for GV-017.

## Target Files or Areas
- `scripts/agent/commands/cmd_mdq.py` (delete), `command_defs_list.py`, `registry.py`
- `tests/agent/commands/test_cmd_mdq.py` (delete)
- `agent_07_01`, `agent_07_03`, `agent_07_10`, `agent_03_02`, `agent_08_02` under `docs/23_agent/`, the MDQ/RAG boundary and MDQ enforcement docs under `docs/22_mcp/`
- `tools/check_compat_shims.py` (`_REMOVED_NAME_PATTERNS`)
- the generated Agent API reference

## Required Changes
- Delete the `/mdq` CommandDef and its SubcommandSpec entries, the handler file, and the mixin wiring.
- Delete the `/mdq` tests; add tests that `/mdq` is absent from the command list, `/help`, and completion, and that it is an unknown command.
- Remove `/mdq` from the Agent CLI docs; add a statement to the four MDQ-path docs that the Agent exposes no `/mdq` slash command and uses MDQ only through the normal LLM and MCP path.
- Regenerate the Agent API reference with `generate_reference_table.py --type agent`.
- Add the `/mdq` command form to the GV-017 removed-name check.

## Constraints
- Do not remove `mdq-mcp`, `mdq.sqlite`, MDQ tool definitions, `RuntimeToolRegistry` registration, `allowed_dirs`, `mdq_rag_mode`, or `agent/mdq_rag_classifier.py` and `agent/mode_classification.py`.
- Do not ban the string `mdq` as a whole in the removed-name check.
- Current specifications must not keep the removed command's syntax or history notes.

## Acceptance Criteria
- `_COMMANDS` has no `/mdq`; `/help` and completion do not list it; typing it gives the unknown-command message.
- No `/mdq` handler, mixin, or dispatch remains.
- The Agent CLI docs do not mention `/mdq`.
- The MDQ server, tools, authorization, index, and search still work.
- GV-017 detects `/mdq` reintroduction.
- All tests, mypy, import-linter, doc checks pass, and `check_compat_shims.py --check-removed-names` is clean.

## Testing Expectations
`uv run pytest` (full), `uv run mypy scripts`, `PYTHONPATH=scripts uv run lint-imports`, `check_docs_consistency.py`, `check_compat_shims.py --check-removed-names`, and the alternative-path and MDQ regression tests listed in memo2 section 8.2.

## Documentation Impact
Yes: Agent CLI docs, MDQ usage-path docs, generated API reference, removed-name rules. Docs stay in English.

## Out of Scope
- `/approve`, `/reject` removals; MDQ server, classifier, and configuration changes; adding a status command to `/context` or `/debug`.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `mdq_rag_mode` is referenced only by the classifier (memo2 requires this check).
- Exact `/mdq` handler file name (memo2 gives `cmd_mdq.py` as an example).

## AI Implementation Instruction
Keep changes minimal and limited to the listed targets. Do not modify MDQ server code. Stop and report if a reference outside the targets is found.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-095505
- **Related target files**: see Target Files or Areas
