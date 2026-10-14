# Remove the skill slash command and its ephemeral plumbing

## Priority
Medium

## Summary
Remove the `/skill` slash command and the `_skill_ephemeral` / `skill_mixin` plumbing. The feature does not deliver its documented behavior (the skill text never reaches the LLM), so deletion is preferred over repair. Deletion also closes the stale Known Issue AGENT-009. Source: `memo2.md`, corrected by adversarial verification against current source.

## Background
`/skill <name>` appends `skills/<name>/SKILL.md` as a system message tagged `_ephemeral` and `_skill_ephemeral`. No ADR defines `/skill`, so no ADR approval is needed. `memo2.md` inferred its targets without source access; this issue replaces those inferences with verified facts.

Verified facts (current source):
- `append_message(source="skill_mixin")` strips `_ephemeral` because `TRUSTED_SOURCES["skill_mixin"]` authorizes only `_skill_ephemeral` (`scripts/agent/message_schema.py`, `scripts/agent/context.py`). Reproduced.
- `_skill_ephemeral` is in `_EPHEMERAL_KEYS` (`scripts/agent/conversation_state_manager.py`), so the message is removed by `clear_previous_turn_ephemeral_messages()`.
- That clear runs at the start of `_process_turn`, before `append_user_message` and `handle_llm_turn` (`scripts/agent/workflow_engine_adapter.py`). Reproduced with a script: after `/skill`, history holds the message; after the turn-start clear, history is empty. The skill text is therefore removed before the first LLM call that could use it.
- AGENT-009 and `docs/23_agent/agent_07_10_*` claim the message is NOT cleared at the next turn. That claim is stale. The earlier fix was made by adding `_skill_ephemeral` to `_EPHEMERAL_KEYS`.
- `memo2.md` stated that `replace_history()` strips reserved keys and that `orchestrator.py` handles `_skill_ephemeral`; neither is true. `replace_history()` sanitizes by whitelist (source `""`), and `orchestrator.py` has no reference.
- Nothing except `cmd_skill.py` reads `skills/` at agent runtime. `tools/*` and pre-commit hooks read `skills/` as lint/doc inputs, so `skills/` must stay.
- Saved sessions are unaffected: `session_message_repo.py` persists only `role`, `content`, `tool_calls`, `tool_call_id`, and `cmd_skill` never calls `session.save`.

## Problem
- `/skill` is documented as passing skill content "to the next LLM turn", but the content is cleared before that turn's LLM call. The command silently does nothing useful.
- AGENT-009 and its docs describe a lifetime problem that no longer exists; the ledger and docs are stale.
- User-supplied invocation arguments are appended to a system-role message without injection checks (`docs/91_security/security_01_*`).
- The feature needs a dedicated marker (`_skill_ephemeral`) and a dedicated trusted source (`skill_mixin`).

## Reason for Change
The command cannot work without reworking turn-boundary clearing, and its only purpose is covered by alternatives (ask in the user message so the model reads the file via file-read tools, a `/system` preset, or MDQ indexing of `skills/`). Deleting it removes a dead command, an untrusted-input path into system-role messages, one marker and one trusted source, and the stale AGENT-009.

## Implementation Intent
Delete the feature and its dedicated plumbing only. Keep `skills/` (including `skills/DESIGN.md`), `_ephemeral`, and `_memory_injected`. No backward-compat alias. Edit mixed test files in place instead of deleting them. Add a regression test that `/skill` stays unregistered, following the existing removed-commands pattern.

## Target Files or Areas
Code:
- `scripts/agent/commands/cmd_skill.py` (delete)
- `scripts/agent/commands/command_defs_list.py` (`/skill` CommandDef and help text)
- `scripts/agent/commands/registry.py` (import, `_SkillMixin` base, docstring line)
- `scripts/agent/message_schema.py` (`skill_mixin` entry, docstring)
- `scripts/shared/types.py` (`_skill_ephemeral` field)
- `scripts/agent/conversation_state_manager.py` (`_EPHEMERAL_KEYS`)

Tests:
- `tests/agent/commands/test_cmd_skill.py` (delete)
- `tests/agent/test_message_schema.py`, `tests/agent/test_ephemeral_filtering_security.py`, `tests/agent/test_orchestrator.py` (partial edits; skill and non-skill cases are mixed)
- `tests/agent/commands/test_removed_commands.py` (add `/skill` regression case)

Docs and governance:
- `routing.md` (the `/skill <name> [args]` sentence in the header; not in memo2)
- `docs/23_agent/agent_07_03_*` (command row), `agent_07_10_*` (title/Purpose, Skill Category section, Responsibility Boundary, Known Limitations, Keywords)
- `docs/40_shared/shared_02_01_*`, `docs/91_security/security_01_*`
- `docs/00_governance/governance_03_*` (AGENT-009 table row and detail entry; the active-item count drops by one)
- `tools/check_compat_shims.py` and `tests/tools/test_check_compat_shims.py` (see Constraints)

Checked and needing no change: `agent_07_01_*`, `agent_04_01_*`, `agent_13_*` (no skill references), `orchestrator.py`, `tools/TOOL_DESCRIPTIONS.md`.

## Required Changes
- Delete `cmd_skill.py`; remove the `/skill` `CommandDef` and the `_SkillMixin` composition and docstring entry.
- Remove `skill_mixin` from `TRUSTED_SOURCES`, `_skill_ephemeral` from `LLMMessage` and `_EPHEMERAL_KEYS`, and fix the `message_schema.py` docstring.
- Delete `test_cmd_skill.py`; remove only the skill-specific cases from the three mixed test files; add the `/skill` unregistered test.
- Update `routing.md` and the docs above; remove AGENT-009 row and entry; remove the `_cmd_skill()` source reference from security_01.
- Optionally add removed-name entries to `_REMOVED_NAME_PATTERNS` (documentation guard only; see Constraints).

## Constraints
- Do not delete `skills/` or `skills/DESIGN.md`.
- `_REMOVED_NAME_PATTERNS` checks only `*.md` files, is opt-in (`--check-removed-names`, default OFF, not in pre-commit), and exempts lines near words like "removed". It cannot guard `.py` reintroduction, so the unregistered-command test is the real guard. A `/skill` pattern must be `/skill(?![\w-])`: `\b` alone matches `/skill-creator` and fails to separate `/skills/`.
- Removed names will still appear in `tools/check_compat_shims.py` and its test; the acceptance grep must account for that.
- `check_known_deviation_sync.py` only cross-checks ADR-cited IDs; AGENT-009 is cited only from the two docs, so removing it is consistent.

## Acceptance Criteria
- Typing `/skill` yields the unknown-command message (`scripts/agent/repl_input_loop.py`), and the new regression test asserts `/skill` is not in `_COMMANDS`.
- `rg -n "skill_ephemeral|skill_mixin|cmd_skill|SkillMixin|/skill(?![\w-])|AGENT-009" scripts tests docs routing.md --pcre2` returns nothing.
- `rg` over `tools/` hits only the intentional removed-name entries and their test, if added.
- AGENT-009 is absent from the ledger; `skills/DESIGN.md` remains; docs checks pass.
- No remaining test references `_skill_ephemeral`.

## Testing Expectations
- `uv run pytest` (full), including `tests/agent/commands/`, `tests/docs/` command-sync tests, and `tests/tools/test_check_compat_shims.py`.
- `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check`, `PYTHONPATH=scripts uv run lint-imports`.
- `check_compat_shims.py --check-removed-names`, `check_known_deviation_sync.py`, `check_issue_inventory_conformance.py`, `check_docs_consistency.py --domain agent`, `check_skills_references.py`, plus the docs checkers in `routing.md`.

## Documentation Impact
Yes: command index, slash-command chapter (remove the Skill section and stale Known Limitation), core types lifecycle, trust boundaries (Agent to LLM row: two kinds of content remain, memory snippets and fixed MDQ/RAG hints), Known Issues ledger, `routing.md`. Add a release-note line pointing `/skill` users to the alternatives (user-message instruction, `/system` preset, MDQ). Docs stay in English.

## Out of Scope
- Deleting `skills/` or changing skill content.
- Changing `_ephemeral` / `_memory_injected` semantics or turn-boundary clearing.
- Editing historical files (`issues/done`, `plans/done`, `requires/done`, `implementations/done`).

## Dependencies
N/A: none (no open issue under `issues/` touches these files; checked 20261014)

## Unresolved Questions
- Should `memo2.md` (repo root) be removed or updated after this issue is filed? Unknown.
- Should the `_REMOVED_NAME_PATTERNS` additions be made at all, given they cannot guard source? Assumption: optional.

## AI Implementation Instruction
Keep changes to the listed targets. Edit mixed test files surgically. Run `rg` before and after to confirm no reference is missed; if a reference outside the listed targets appears, report it before editing. Do not change turn-clearing behavior or touch `skills/`. Do not commit unless asked.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-090429
- **Related target files**: see Target Files or Areas
