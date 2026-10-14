# Remove the mdq slash command

## Priority
Low

## Summary
Remove the `/mdq` slash command and its handler mixin so that MDQ is reachable only through the normal LLM tool-selection and MCP execution path. Keep `mdq-mcp`, `mdq.sqlite`, the MDQ tools, the MDQ/RAG classifier, and `mdq_rag_mode`. Source: `memo2.md` (procedure v1.0, 2026-10-13), corrected by adversarial verification against current source.

## Background
`/mdq` (status, index, refresh, search, outline, get, grep) is implemented by `_MdqMixin` in `scripts/agent/commands/cmd_mdq.py` and calls MDQ MCP tools through the agent's tool executor after a `check_preflight()` call. It follows the `/skill` removal (commit 6ef4f8fbd, which had to touch several tests the plan did not list). `memo2.md` section 15 lists `/approve` and `/reject` as later, separate removals. `memo2.md` was written without source access; this issue replaces its inferences with verified facts.

Verified facts:
- `cmd_mdq.py` (303 lines) defines only `_parse_int_flag` and `_MdqMixin`. Nothing else in `scripts/` or `tests/` uses `_parse_int_flag`, `_require_tools`, `_execute_mdq`, or `_MdqMixin` except `registry.py` and two tests. No shared logic is trapped in the file, and `test_cmd_mdq.py` tests only the handlers (no MDQ server tests mixed in).
- `mdq_rag_mode` is read only in `scripts/agent/mode_classification.py:49`; the slash command does not use it.
- The command list, `/help`, and completion are generated from `_COMMANDS`, so the `CommandDef` removal covers them. There is no `SubcommandSpec` entry for `/mdq`.
- Existing coverage already exists for the alternative path and MDQ body: `tests/agent/test_mode_classification.py` (hint), `tests/mcp_servers/mdq/test_mdq_path_jail.py` and `test_mdq_read_authorization.py` (`allowed_dirs=[]`), `test_mdq_search_modes.py` (BM25 only).
- `_REMOVED_NAME_PATTERNS` checks `*.md` only, is opt-in (`--check-removed-names`), and exempts lines within 10 lines of markers such as "removed" or "legacy". `--check-removed-names` currently reports 2 pre-existing findings (`docs/22_mcp/mcp_03_01_dispatch-and-routing.md:129`, `docs/23_agent/agent_12_reference-api.md:129`).
- The canonical MDQ-path statements already exist: `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` lines 76-81 ("The agent layer accesses both systems exclusively through MCP tool calls") and line 108 (override mode is a system-prompt routing hint), and `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` line 108 (`mdq_rag_mode` behavior). `mdq_rag_mode` is not documented in `agent_08_02` or `agent_03_02`.
- `COMPAT_PATTERNS` in `tools/check_compat_shims.py` is checked by default, scans code and docs, runs in CI (`.github/workflows/backward-compat-check.yml`), and already holds removed slash commands (`/note`, `/db` aliases, `/mcp install`). A trial run with a `/mdq` entry reports 44 findings, all in files this issue already targets, and none on `mdq.sqlite`, `mdq-mcp`, or `scripts/mcp_servers/mdq/` paths. `test_removed_commands.py`, `test_cmd_registry_note_removal.py`, `tests/tools/test_check_compat_shims.py`, and the checker itself are already on its allowlist.
- `check_docs_structure.py` validates `related:` entries only for existence, format, self-reference, and duplicates; it requires neither a body reference nor reciprocity.
- `generate_reference_table.py --type agent` indexes only top-level `scripts/agent/*.py`; the generated doc has no `cmd_mdq` or `_MdqMixin` entry, so regeneration changes nothing for this removal.

## Problem
- A second REPL path reaches `mdq-mcp` besides the normal LLM and MCP path, with its own preflight and output handling in the CLI layer.
- `/mdq search --mode grep` is advertised (`cmd_mdq.py:176`) and forwarded to `search_docs`, but that tool rejects `grep` (`tests/mcp_servers/mdq/test_mdq_search_modes.py::test_grep_mode_rejected`; grep is the separate `grep_docs` tool). The command also uses only the first token as the query.
- `docs/23_agent/agent_02_runtime-architecture.md` lists the `/mdq` path as a `check_preflight` call site and as a gateway-bypass pattern, so the command also widens the enforcement analysis.

## Reason for Change
Consolidate MDQ access into one path (LLM tool selection, `RuntimeToolRegistry`, MCP). Removal drops one command, one mixin, a partly broken option, and one gateway-bypass call site.

## Implementation Intent
Delete only the command, its handler mixin, its registration, and its tests and documentation. Do not touch the MDQ server, classifier, or configuration. After the change `/mdq` falls through to the existing unknown-command warning with no alias. Add no new documentation sentence about the canonical MDQ path: it is already stated in `mcp_05_04` and `agent_03_01`, and a repeat would duplicate it. Current specifications must not contain `/mdq`. Guard reintroduction with the unregistered-command test and a `COMPAT_PATTERNS` entry (default-on, CI, covers code and docs) instead of the opt-in, markdown-only `_REMOVED_NAME_PATTERNS`.

## Target Files or Areas
Code:
- `scripts/agent/commands/cmd_mdq.py` (delete)
- `scripts/agent/commands/command_defs_list.py` (the `/mdq` CommandDef and the now-empty `# Prefix async` comment)
- `scripts/agent/commands/registry.py` (docstring line, import, base class)

Tests:
- `tests/agent/commands/test_cmd_mdq.py` (delete)
- `tests/agent/commands/test_cmd_registry_note_removal.py` (imports `_MdqMixin`; remove the `_Mdq` class and the `_cmd_mdq` patch)
- `tests/agent/commands/test_command_def_sync.py` (seven `_cmd_mdq_*` entries in `INTENTIONAL_HANDLER_EXCLUSIONS`)
- `tests/agent/commands/test_command_registry_consistency.py` (mixin counts 13 total / 11 direct become 12 / 10; docstring and test name)
- `tests/docs/test_command_docs_sync.py` (delete `test_mdq_commands_in_registry`)
- `tests/docs/test_db_ownership_boundaries.py` (delete `test_cmd_mdq_no_direct_db_access`)
- `tests/agent/commands/test_cmd_registry_ingest_removal.py` (stale docstring line mentioning `/mdq`)
- `tests/agent/commands/test_removed_commands.py` (add the `/mdq` unregistered test)
- `tests/tools/test_check_compat_shims.py` (case for the new removed-name pattern)

Docs and tools:
- `docs/23_agent/agent_02_runtime-architecture.md` (call-site row 2 and the Pattern 1 text; renumber the remaining rows)
- `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` (chapter-index description only; it has no `/mdq` command list)
- `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (command row)
- `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` (title, Purpose, MDQ Category section, Responsibility Boundary item, keyword, and the `related:` entry for `mcp_05_04_mdq-rag-boundary.md`, which nothing in the body references afterwards)
- `tools/check_compat_shims.py` (`COMPAT_PATTERNS`)

Checked and needing no change: `mcp_05_04_*`, `mcp_05_05_*`, `agent_03_01_*`, `agent_03_02_*`, `agent_08_02_*` (the canonical statements already exist or the files have no `mdq` text), `agent_13_*` generated doc, `routing.md`, `rules/`, `skills/`, `config/`, `tox.ini`.

## Required Changes
- Delete `cmd_mdq.py`; remove the `/mdq` `CommandDef` and the `# Prefix async` comment, and the `_MdqMixin` import, base class, and docstring line in `registry.py`.
- Delete `test_cmd_mdq.py`; edit the mixed test files as listed (surgically; do not delete whole files); add a `/mdq` unregistered test next to the `/skill` one.
- Update the counts and test name in `test_command_registry_consistency.py`.
- Update the docs as listed. Do not add a new MDQ-path statement to any doc, and do not write `/mdq` into any current spec.
- Add a `"/mdq command"` entry to `COMPAT_PATTERNS` (not `_REMOVED_NAME_PATTERNS`) with the pattern `(?<![\w/.-])/mdq(?![\w./-])`, and a test case in `tests/tools/test_check_compat_shims.py`; the pattern must not match `mdq.sqlite`, `mdq-mcp`, `scripts/mcp_servers/mdq/`, or `/opt/llm/db/mdq.sqlite`.
- Do not add `generate_reference_table.py` regeneration as a step (no-op).

## Constraints
- Do not remove or change `mdq-mcp`, `mdq.sqlite`, MDQ tool definitions, `RuntimeToolRegistry` registration, `allowed_dirs`, `mdq_rag_mode`, `agent/mdq_rag_classifier.py`, or `agent/mode_classification.py`.
- Do not ban the string `mdq` as a whole.
- Current specifications must not keep the removed command's syntax or "formerly" notes, and must not contain `/mdq` anywhere (`COMPAT_PATTERNS` has no historical-marker exemption; `test_command_docs_sync.py` also scans `agent_01` and `agent_07_01` to `agent_07_10`).
- `_REMOVED_NAME_PATTERNS` (GV-017) is `*.md` only, opt-in, and exempts historical-marker lines, so it is not used for this guard.

## Acceptance Criteria
- `_COMMANDS` has no `/mdq`; the new test asserts it, and typing `/mdq` yields the unknown-command message (`scripts/agent/repl_input_loop.py`).
- `rg -n --pcre2 "cmd_mdq|_MdqMixin|_execute_mdq|(?<![\w/.-])/mdq(?![\w./-])" scripts tests docs tools` returns only intentional hits (the regression test, the `COMPAT_PATTERNS` entry, and its test).
- `uv run python tools/check_compat_shims.py` (default run) passes with the new entry; before the change the same entry reports 44 findings.
- `agent_02` lists no `/mdq` call site and its remaining rows are numbered consecutively.
- MDQ server tests, classifier tests, and `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` pass unchanged.
- `check_compat_shims.py --check-removed-names` reports no new finding versus the baseline of 2 pre-existing findings (no entry is added to that check).
- Full test suite, mypy, import-linter, and the docs checkers in `routing.md` pass.

## Testing Expectations
- `uv run pytest` (full), plus `tests/agent/commands/`, `tests/docs/`, `tests/tools/test_check_compat_shims.py`, `tests/mcp_servers/mdq/`.
- `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check`, `PYTHONPATH=scripts uv run lint-imports`.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` and `--domain mcp`, `check_compat_shims.py` (default) and `--check-removed-names`.
- Do not write new alternative-path tests that duplicate the existing coverage listed in Background; add one only if a gap is found during implementation.
- Measure impact first: `rg -c "cmd_mdq|_MdqMixin" tests` before editing.

## Documentation Impact
Yes: command index, slash-command chapter (title becomes Memory and Other), chapter-index description, runtime-architecture call-site table and gateway-bypass text. No new MDQ-path statement is added. Remove the `/mdq` entry from the current spec without a history note. Docs stay in English.

## Out of Scope
- `/approve` and `/reject` removals; MDQ server, classifier, or configuration changes.
- Adding a classification-status view to `/context` or `/debug`.
- Fixing the 2 pre-existing `--check-removed-names` findings.
- Editing historical files (`issues/done`, `plans/done`, `requires/done`, `implementations/done`, `.claude/worktrees/`).

## Dependencies
- Follows the `/skill` removal (commit 6ef4f8fbd); the mixin counts in `test_command_registry_consistency.py` must start from 13 / 11.
- No open issue under `issues/` touches these files (checked 20261014).
- `/approve` and `/reject` removals will touch the same registry, docs, and count tests; apply them in sequence and recount.

## Unresolved Questions
- Assumption to confirm: `memo2.md` section 10 names GV-017 (`_REMOVED_NAME_PATTERNS`) for the reintroduction guard. This issue instead registers `/mdq` in `COMPAT_PATTERNS` because GV-017's check is opt-in, markdown-only, and exempts historical-marker lines, while `COMPAT_PATTERNS` covers code and docs by default and in CI. The change from the memo's literal wording needs the maintainer's confirmation.
- Optional follow-up, not in this issue: register `/skill` in `COMPAT_PATTERNS` the same way (the `/skill` removal added no entry).

## AI Implementation Instruction
Keep changes to the listed targets and edit mixed tests by test name, comparing `pytest --collect-only -q` counts before and after. Do not touch MDQ server or classifier code. Do not write `/mdq` into any current spec. If another file needs modification, stop and report it as an additional target before editing. Do not commit unless asked.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-095505
- **Related target files**: see Target Files or Areas
