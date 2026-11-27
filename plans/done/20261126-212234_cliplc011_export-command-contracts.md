## Goal
- Make Markdown export valid for arbitrary tool content and normalize the command surface: one implementation owner, one canonical usage definition, and one error contract per command, with help, completion, registry, and documentation listing the same command set.

## Priority
Medium

## Scope
- **In-Scope**: adaptive code fence and metadata escaping in the export formatter; a formal export argument parser; `/compact` module ownership move; common unknown-subcommand error handling; the bare `/mcp` status-alias contract; unknown-command token-only display; a CI check comparing command definitions, help, completion, and documentation; documentation corrections.
- **Out-of-Scope**: the final documentation rewrite (issue `20261119-145312_cliplc014_cli-docs-consolidation.md`, still active); command renames beyond the canonical usage definitions.
- **Dependencies**: the REPL input controller Plan (cliplc001) is complete and archived; its input and error contracts are the integration point for the unknown-command display change.
  - **Depends on**: `plans/done/20261122-210208_cliplc001_repl-input-controller.md` | all | the unknown-command display change modifies the dispatch-miss path established by that plan

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 11).

Evidence (`Explicit in code`, by `rg`): `scripts/agent/services/export_formatter.py:40` wraps tool output in a fixed triple-backtick fence; `/compact` is defined in `scripts/agent/commands/cmd_rag_export.py` and registered in `command_defs_list.py:83`; `/stats` is defined in `cmd_config_stats.py`. The claims about export argument parsing, `/debug`, `/set`, `/mcp` without arguments, and echoing of unknown command input are from the backlog and `Needs confirmation`.

## Problem
Verified against current source at `901bea2549a2314ad612a233a5e4e16d3e9d52d3`:

- `scripts/agent/services/export_formatter.py:40` uses a fixed triple-backtick fence: tool output containing a triple-backtick run breaks the exported Markdown. Confirmed.
- Export argument parsing (`scripts/agent/commands/cmd_session.py` `_session_export`, lines 194-211): any token that is not `markdown|md|json` is silently treated as an output filename; multiple unknown tokens overwrite each other (last wins); quoted filenames with spaces break on `args.strip().split()`. Confirmed.
- `/debug` (`scripts/agent/commands/cmd_debug.py:55-58`) writes "Unknown subcommand" directly instead of raising `UnknownSubcommandError` like `cmd_memory.py:131`, `cmd_mcp.py:420`, `cmd_session.py:470`. Confirmed.
- `/set` has no implementation anywhere in `scripts/`; the only reference is `docs/23_agent/agent_05_llm-and-streaming.md:50` (documentation drift). Confirmed.
- Bare `/mcp` (`scripts/agent/commands/cmd_mcp.py:412-416`) is currently a status alias that also writes a redundant usage line. Confirmed as current behavior; behavior decision recorded as D5 (user decision: keep the status alias).
- Unknown command input echoes the full line including arguments (`scripts/agent/repl_input_loop.py:290`). Confirmed.
- `/stats` is implemented as aggregate counts (`scripts/agent/commands/cmd_config_stats.py:106`), but `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md:48` still says "not yet implemented, SHARED-003". Confirmed.
- `UnknownSubcommandError` renders as `[error]`, not `[usage]`, at the command boundary (`scripts/agent/commands/registry.py` `_emit_command_error`, lines 157-170: only `CommandValidationError`/`CommandParseError` render as usage). Confirmed.
- Help and completion are already derived from `_COMMANDS` (`scripts/agent/repl.py:74-76` `SLASH_COMMANDS` via `completion_command_names()`); the CI check `tests/agent/commands/test_command_def_sync.py` compares definitions, handlers, and help but not documentation. Confirmed.

## Reason for Change
Contract consistency of the command surface; moderate risk (malformed export, misleading docs), no data loss.

## Implementation Intent
Export is valid for arbitrary content; each command has one implementation owner, one canonical usage definition, and one error contract; help, completion, registry, and documents list the same command set.

## Requirements
- `REQ-001`: Exported Markdown remains valid for arbitrary tool text: the code fence is longer than the longest backtick run in the content; tool call ids and structural metadata are escaped.
- `REQ-002`: Export uses a formal argument parser: unknown formats and multiple output files are rejected as usage errors; `--output` and quoted filenames are supported; UTF-8 and newlines are preserved.
- `REQ-003`: Each command has one implementation owner: `/compact` moves to `scripts/agent/commands/cmd_context.py` (user decision); `cmd_rag_export.py` is removed and the registry wiring updated.
- `REQ-004`: One common error contract: `/debug` raises `UnknownSubcommandError`, and the command boundary renders it as a usage error.
- `REQ-005`: Bare `/mcp` is the formal status-alias contract (user decision); the redundant usage line is removed.
- `REQ-006`: Unknown-command output shows only the command token, not the full input line.
- `REQ-007`: Help, completion, registry, and documentation list the same command set; a CI check compares them; `/set` references are removed (point to `/reload`); `/stats` is documented as aggregate counts only.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed — see this Plan's Step 8 report in the workflow run).
Amended 2026-11-26 (fallout): added tests/agent/commands/test_command_registry_consistency.py — Pinned-count test discovered during Step 3c: the module removal changes both counts

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/export_formatter.py` | Fence length longer than the longest backtick run; escape tool call ids and structural metadata | Fixed triple-backtick fence breaks on embedded fences | REQ-001; AC-1 | `scripts/agent/services/export_formatter.py` line 40 (fixed fence) | `tests/test_export_formatter.py` | Verified |
| `scripts/agent/commands/cmd_session.py` | Formal export argument parser: reject unknown formats and multiple output files; `--output` flag; quoted filenames via `shlex` | Unknown tokens silently become filenames | REQ-002; AC-1 | `scripts/agent/commands/cmd_session.py` lines 194-211 (`else: outfile = part`) | `tests/agent/commands/test_command_arg_parsing.py` | Verified |
| `scripts/agent/commands/cmd_context.py` | Receive the `_cmd_compact` handler as the canonical owner | `/compact` lives in the RAG export mixin despite using only the history manager | REQ-003; AC-2 | `scripts/agent/commands/cmd_context.py` docstring lists the context mixin commands; handler uses only `hist_mgr` and `conv.history` (`cmd_rag_export.py:32-58`) | `tests/agent/commands/test_agent_cmd_context.py` | Verified |
| `scripts/agent/commands/cmd_rag_export.py` | Remove the module (empty after the handler move) | Single-owner normalization | REQ-003; AC-2 | `scripts/agent/commands/cmd_rag_export.py` contains only `_cmd_compact` (lines 19-58) | `tests/agent/test_history_compression_consistency.py` | Verified |
| `scripts/agent/commands/registry.py` | Remove the `_RagExportMixin` wiring; render `UnknownSubcommandError` as a usage error at the command boundary | Wiring removal; usage-error classification gap | REQ-003, REQ-004; AC-2 | `scripts/agent/commands/registry.py` lines 38, 59 (mixin wiring), 157-170 (`_emit_command_error` renders `UnknownSubcommandError` as `[error]`) | `tests/agent/commands/test_command_registry_consistency.py` | Verified |
| `scripts/agent/commands/cmd_debug.py` | Raise `UnknownSubcommandError` instead of writing directly | Error-contract inconsistency | REQ-004; AC-2 | `scripts/agent/commands/cmd_debug.py` lines 55-58 | `tests/agent/commands/test_cmd_debug.py` | Verified |
| `scripts/agent/commands/cmd_mcp.py` | Formalize bare `/mcp` as the status alias; remove the redundant usage line | Alias contract per user decision | REQ-005; AC-2 | `scripts/agent/commands/cmd_mcp.py` lines 412-416 | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| `scripts/agent/commands/command_defs_list.py` | Canonical usage definitions: export `ArgSpec` gains `--output`; help text aligned with the parser | Parser contract must match the registry definition | REQ-002, REQ-007; AC-2 | `scripts/agent/commands/command_defs_list.py` lines 83-86 (`/compact`), 118-121 (export `ArgSpec`) | `tests/agent/commands/test_command_defs.py` | Verified |
| `scripts/agent/repl_input_loop.py` | Show only the unknown command token | Full-line echo can leak sensitive arguments | REQ-006; AC-3 | `scripts/agent/repl_input_loop.py` line 290 | `tests/agent/test_repl.py` | Verified |
| `tests/test_export_formatter.py` | Nested-fence test first (Issue AI Instruction); fence-length, injection, Unicode, newline variants | New fence behavior needs coverage | REQ-001; AC-1 | `tests/test_export_formatter.py` lines 50, 172-193 (fence assertions) | itself | Verified |
| `tests/agent/services/test_commands_utils.py` | Fence and escaping assertions updated | Pinned fence output assertions change under D1 | REQ-001; AC-1 | `tests/agent/services/test_commands_utils.py` (34 `render_history_md` candidates from consumer scan) | itself | Verified |
| `tests/agent/commands/test_command_arg_parsing.py` | Unknown format, duplicate output, quoted filename, `--output` tests | New parser behavior needs coverage | REQ-002; AC-1 | `tests/agent/commands/test_command_arg_parsing.py` has no export coverage today | itself | Verified |
| `tests/agent/commands/test_cmd_debug.py` | Unknown-subcommand tests updated to assert the raised error | Direct-write assertions change under D4 | REQ-004; AC-2 | `tests/agent/commands/test_cmd_debug.py` lines 34-43 | itself | Verified |
| `tests/agent/commands/test_cmd_mcp.py` | Bare `/mcp` alias contract test | Contract formalization needs coverage | REQ-005; AC-2 | `tests/agent/commands/test_cmd_mcp.py` existing `/mcp` tests | itself | Verified |
| `tests/agent/commands/test_command_def_sync.py` | Add documentation-set and completion-set equality checks (CI check) | Existing check covers defs/handlers/help only | REQ-007; AC-2 | `tests/agent/commands/test_command_def_sync.py` docstring scope | itself | Verified |
| `tests/agent/test_repl.py` | Unknown-command display shows only the token | Pinned full-line echo assertion changes under D6 | REQ-006; AC-3 | `tests/agent/test_repl.py` line 313 (`msg.startswith(f"Unknown command: {removed_name}")`) | itself | Verified |
| `tests/agent/test_history_compression_consistency.py` | Update the `_RagExportMixin` import after the module removal | Module removal breaks the import | REQ-003; AC-2 | `tests/agent/test_history_compression_consistency.py` lines 21, 382 | itself | Verified |
| `docs/23_agent/agent_05_llm-and-streaming.md` | Remove the `/set` reference; point to `/reload` | Documentation drift: `/set` is not implemented | REQ-007 | `docs/23_agent/agent_05_llm-and-streaming.md` line 50 | N/A: documentation gate per `rules/tool-gates.md` | Verified |
| `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Canonical command specification: `/stats` aggregate-counts scope, bare `/mcp` alias, `/compact` owner | Documentation Impact | REQ-007 | `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` line 48 (`/stats` "not yet implemented, SHARED-003") | N/A: documentation gate per `rules/tool-gates.md` | Verified |
| `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | Regenerate the reference table after the formatter docstring change | Generated-reference domain hit by the predictable fallout check | REQ-001, REQ-007 | `docs/23_agent/agent_14_reference-api-subpackages-generated.md` line 170 lists `render_history_md` with its docstring first line | N/A: `generate_reference_table.py --check` | Verified |
| `tests/agent/commands/test_command_registry_consistency.py` | Update the pinned mixin counts (10 MRO, 8 direct bases) after the _RagExportMixin wiring removal | Pinned-count test discovered during Step 3c: the module removal changes both counts | REQ-003 / AC-2 | tests/agent/commands/test_command_registry_consistency.py lines 181-197 assert 10 Mixin classes in the MRO and 8 direct Mixin bases | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/commands/utils.py` | `parse_command_args` already supports `--flag value` pairs; the export parser reuses it with `shlex` tokens; `not affected` | REQ-002 |
| `scripts/agent/commands/exceptions.py` | `UnknownSubcommandError` and `CommandDispatchError` vocabulary; `not affected` | REQ-004 |
| `scripts/agent/cli_view.py` | Tab completion wiring (`slash_commands`); `not affected` | REQ-007 |
| `scripts/agent/repl.py` | `SLASH_COMMANDS` completion source; `not affected` | REQ-007 |
| `scripts/agent/commands/cmd_config_stats.py` | `/stats` aggregate-counts behavior to document; `not affected: no code change` | REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): Exported Markdown remains valid for arbitrary tool text; invalid export arguments produce usage errors.
- AC-2 (REQ-003, REQ-004, REQ-005, REQ-007): Every documented command exists; every command has one canonical specification and common error behavior.
- AC-3 (REQ-006): Unknown-command output does not echo sensitive arguments.

## Tests
- Write the nested-fence export test first (Issue AI Instruction): embedded backtick runs, Markdown injection, Unicode, and newline variants (`tests/test_export_formatter.py`, `tests/agent/services/test_commands_utils.py`).
- Parser tests: unknown format, duplicate output, quoted filename, `--output` (`tests/agent/commands/test_command_arg_parsing.py`).
- Command-contract tests: `/debug` raises, bare `/mcp` alias, unknown-token display, help/completion/documentation set equality (`tests/agent/commands/test_cmd_debug.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/test_repl.py`, `tests/agent/commands/test_command_def_sync.py`).
- Run ruff, mypy, import-linter, and the full test suite; diff-cover on the change.

## Documentation Impact
Yes. One canonical specification per command; remove `/set`; document `/stats` scope. Target docs via `docs/00_index.md` "Document References by Task": Agent spec (command registry). The three `docs/` rows in `Implementation Target Files` record the concrete files, including the regenerated reference table.

## Assumptions
- Help and completion are derived from `_COMMANDS`, so they stay consistent by construction; the CI check adds documentation-set equality only.
- The `/compact` handler name `_cmd_compact` is unchanged, so `command_defs_list.py` handler reference needs no rename.
- Command renames are minimal per the Issue AI Instruction; no command is removed except the `/set` documentation reference (no implementation exists, so no documented workflow breaks).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | Both Issue Unknowns resolved by user decision on 2026-11-26: bare `/mcp` stays a status alias (decision D5); `/compact` target module is `scripts/agent/commands/cmd_context.py` (decision D3) | N/A: resolved | N/A: resolved | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/services/export_formatter.py` | Adaptive fence; metadata escaping | 34 `render_history_md` test candidates + generated reference row | 1 | N/A: `git-fame` unavailable in this environment | N/A: no deploy change |
| `scripts/agent/commands/cmd_session.py` | Export argument parser | `/session` dispatch surface | 6 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_context.py` | Receive `/compact` handler | `/context` mixin consumers | 1 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_rag_export.py` | Module removal | 5 `_RagExportMixin` candidates (registry wiring, 1 test import) | 0 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/registry.py` | Wiring removal; usage-error classification | All command dispatch | 1 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_debug.py` | Raise `UnknownSubcommandError` | `/debug` display path | 0 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_mcp.py` | Bare `/mcp` alias contract | `/mcp` display path | 5 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/command_defs_list.py` | Export `ArgSpec` update | Help, completion, dispatch definitions | 4 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/repl_input_loop.py` | Token-only unknown-command display | REPL dispatch-miss path | 3 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `tests/agent/commands/test_command_registry_consistency.py` | Modify | Not assessed (amendment 2026-11-26) | N/A | N/A | Not assessed (amendment 2026-11-26) |

## Design
Grounded in the Path B analyses at HEAD `901bea2549a2314ad612a233a5e4e16d3e9d52d3`.

Validation quality baseline:
- radon: `render_history_md` is B (8) and `_cmd_session` is C (14); all other target functions are A. The fence change keeps `render_history_md` within B; the export parser stays a separate helper to avoid raising `_cmd_session` further.
- vulture: no dead code in the target files.
- bandit: 1 pre-existing Low finding (`B101` assert at `scripts/agent/commands/cmd_session.py:114`), unrelated to this change.
- diff-cover: no diff against `master` at HEAD, so the baseline is empty; coverage is measured on the change itself.
- import-linter: 6 contracts KEPT at HEAD; no new cross-layer imports (the handler move stays inside `agent/commands/`).
- Historical analysis: churn per file recorded in `Affected areas`; `git-fame` (bus factor) unavailable in this environment.
- Overlap check disposition (`check_plan_target_overlaps.py`, 3 findings involving this Plan): `scripts/agent/commands/cmd_mcp.py` with cliplc009 — no contradiction: cliplc009 masks endpoint URLs in the status display, this Plan changes the bare-`/mcp` dispatch branch only; `scripts/agent/repl_input_loop.py` with cliplc010 — no contradiction: cliplc010 changes the persistence-error branch, this Plan changes the dispatch-miss display branch; `tests/agent/commands/test_cmd_mcp.py` with cliplc009 — both add coverage, additive. The other 3 findings are between external plans and do not involve this Plan.

Consumer scan results (`tools/scan_change_consumers.py`):
- Seed `render_history_md` (34 test candidates): target rows `scripts/agent/services/export_formatter.py`, `tests/test_export_formatter.py`, `tests/agent/services/test_commands_utils.py`; `docs/23_agent/agent_14_reference-api-subpackages-generated.md` is a regeneration target row.
- Seed `_RagExportMixin` (5 candidates): target rows `scripts/agent/commands/registry.py` (wiring removal), `scripts/agent/commands/cmd_rag_export.py` (module removal), `tests/agent/test_history_compression_consistency.py` (import update).

Predictable fallout check:
- Module size gate (24576 B): all target files are below the gate (largest: `scripts/agent/commands/cmd_session.py` at 20775 B); no split row required.
- Pinned counts: `tests/agent/test_repl.py` line 313 pins the full-line unknown-command echo (changes under D6); `tests/test_export_formatter.py` lines 172-193 pin fence positions (changes under D1); `tests/agent/commands/test_cmd_debug.py` lines 34-43 pin direct-write messages (changes under D4). All recorded as target rows.
- Tool inventory: N/A: no tool added or removed.
- Generated blocks: `docs/23_agent/agent_14_reference-api-subpackages-generated.md` lists `render_history_md` with its docstring first line; the docstring change requires regeneration (`generate_reference_table.py --check`) — recorded as a target row.

Design decisions (Path B):
- D1 — Fence rule: the fence length is the longest backtick run in the content plus one, minimum three; tool call ids and structural metadata are escaped so they cannot inject Markdown headings. Alternative: switch to indented code blocks; rejected because the Issue requires fence-based export and indented blocks lose language semantics.
- D2 — Export parser: `shlex.split` tokens through the existing `parse_command_args` in `scripts/agent/commands/utils.py` (already supports `--flag value`); unknown formats and multiple output files raise usage errors; `--output` is the canonical flag and the positional filename stays accepted for compatibility. Alternative: a new parser module; rejected as unnecessary.
- D3 — `/compact` owner: move `_cmd_compact` to `_ContextMixin` in `scripts/agent/commands/cmd_context.py` (user decision); `cmd_rag_export.py` becomes empty and is removed; registry wiring updated. Handler name unchanged.
- D4 — Error contract: `/debug` raises `UnknownSubcommandError`; `registry._emit_command_error` classifies `CommandDispatchError` as a usage error so all command usage errors render consistently.
- D5 — Bare `/mcp`: stays a status alias (user decision); the redundant usage line is removed so the alias is the formal contract.
- D6 — Unknown-command display: show only the first token (the command name), not the full input line.
- D7 — CI check: extend `tests/agent/commands/test_command_def_sync.py` with documentation-set equality against the command index table in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` and completion-set equality via `scripts/agent/repl.py` `SLASH_COMMANDS`.

## Implementation steps
1. **Phase 1: Export formatter (tests first)**
   - [ ] Nested-fence, injection, Unicode, newline tests in `tests/test_export_formatter.py` (REQ-001; AC-1)
   - [ ] Adaptive fence length and metadata escaping in `scripts/agent/services/export_formatter.py` (REQ-001; AC-1)
   - [ ] Update pinned fence assertions in `tests/agent/services/test_commands_utils.py` (REQ-001; AC-1)
2. **Phase 2: Export argument parser**
   - [ ] Parser tests: unknown format, duplicate output, quoted filename, `--output` in `tests/agent/commands/test_command_arg_parsing.py` (REQ-002; AC-1)
   - [ ] Formal parser in `scripts/agent/commands/cmd_session.py` (REQ-002; AC-1)
   - [ ] Export `ArgSpec` update in `scripts/agent/commands/command_defs_list.py` (REQ-002, REQ-007; AC-2)
3. **Phase 3: Command ownership and error contract**
   - [ ] Move `_cmd_compact` to `scripts/agent/commands/cmd_context.py`; remove `scripts/agent/commands/cmd_rag_export.py`; update wiring in `scripts/agent/commands/registry.py` (REQ-003; AC-2)
   - [ ] Update the mixin import in `tests/agent/test_history_compression_consistency.py` (REQ-003; AC-2)
   - [ ] Raise `UnknownSubcommandError` in `scripts/agent/commands/cmd_debug.py`; usage-error classification in `scripts/agent/commands/registry.py` (REQ-004; AC-2)
   - [ ] Bare `/mcp` alias contract in `scripts/agent/commands/cmd_mcp.py` (REQ-005; AC-2)
   - [ ] Token-only unknown-command display in `scripts/agent/repl_input_loop.py` (REQ-006; AC-3)
   - [ ] Tests in `tests/agent/commands/test_cmd_debug.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/test_repl.py`
   - [ ] Update the pinned mixin counts (10 MRO, 8 direct bases) after the _RagExportMixin wiring removal (REQ-003; `tests/agent/commands/test_command_registry_consistency.py`) — amendment 2026-11-26
4. **Phase 4: CI check, documentation, regeneration, and full validation**
   - [ ] Documentation-set and completion-set equality check in `tests/agent/commands/test_command_def_sync.py` (REQ-007; AC-2)
   - [ ] Remove `/set` in `docs/23_agent/agent_05_llm-and-streaming.md` (REQ-007)
   - [ ] Canonical specification in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (REQ-007)
   - [ ] Regenerate `docs/23_agent/agent_14_reference-api-subpackages-generated.md` via `generate_reference_table.py --check` (REQ-001, REQ-007)
   - [ ] Deployment validation/scripts check: no deploy.sh change; confirm the deployed venv files are current per `skills/deploy/SKILL.md` after commit and push (user's decision to deploy)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/export_formatter.py` | Unit: adaptive fence, escaping, Unicode, newlines | `uv run pytest tests/test_export_formatter.py tests/agent/services/test_commands_utils.py` | Export valid for arbitrary content |
| `scripts/agent/commands/cmd_session.py` | Unit: parser rejects unknown format and duplicate output; `--output` and quoted filenames | `uv run pytest tests/agent/commands/test_command_arg_parsing.py` | Invalid arguments produce usage errors |
| `scripts/agent/commands/cmd_context.py` + `scripts/agent/commands/registry.py` | Unit: handler move, wiring, usage-error classification | `uv run pytest tests/agent/commands/test_agent_cmd_context.py tests/agent/commands/test_command_registry_consistency.py tests/agent/test_history_compression_consistency.py` | One owner per command; consistent usage rendering |
| `scripts/agent/commands/cmd_debug.py` + `scripts/agent/commands/cmd_mcp.py` | Unit: raised error, alias contract | `uv run pytest tests/agent/commands/test_cmd_debug.py tests/agent/commands/test_cmd_mcp.py` | Common error behavior |
| `scripts/agent/repl_input_loop.py` | Unit: token-only display | `uv run pytest tests/agent/test_repl.py` | No argument echo |
| Whole change | Full suite + static gates | `uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`, diff-cover | All pass; contracts KEPT; regenerated reference table current |

## Risks
- **Risk**: the adaptive fence changes existing pinned fence assertions → **Mitigation**: `tests/test_export_formatter.py` and `tests/agent/services/test_commands_utils.py` are target rows; the nested-fence test is written first per the Issue AI Instruction.
- **Risk**: the export parser rejects arguments that today "work" by accident (unknown token as filename) → **Mitigation**: this is the intended contract change; the positional filename stays accepted, only unknown formats and duplicate outputs are rejected.
- **Risk**: the `/compact` module removal breaks imports beyond the scanned consumers → **Mitigation**: consumer scan found exactly the registry wiring and one test import; both are target rows.
- **Risk**: command removals could break documented workflows (Issue AI Instruction) → **Mitigation**: no command is removed; `/set` exists only as a documentation reference, so the change is documentation-only.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Export formatter (tests first) | Completed | — | 20261127-102945 |  |
| 2 | Phase 2: Export argument parser | Completed | — | 20261127-102945 |  |
| 3 | Phase 3: Command ownership and error contract | Completed | — | 20261127-102945 |  |
| 4 | Phase 4: CI check, documentation, regeneration, and full validation | Completed | — | 20261127-102945 | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-230743_01_scripts_agent_services_export_formatter.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-230743_02_scripts_agent_commands_cmd_session.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-230743_03_scripts_agent_commands_cmd_context.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_04_scripts_agent_commands_cmd_rag_export.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_05_scripts_agent_commands_registry.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_06_scripts_agent_commands_cmd_debug.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_07_scripts_agent_commands_cmd_mcp.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_08_scripts_agent_commands_command_defs_list.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-230743_09_scripts_agent_repl_input_loop.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-230743_11_tests_agent_services_test_commands_utils.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-230743_15_tests_agent_commands_test_command_def_sync.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-230743_18_docs_23_agent_agent_05_llm-and-streaming.md.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-230743_19_docs_23_agent_agent_07_03_cli-and-commands-command-registry.md.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-230743_20_docs_23_agent_agent_14_reference-api-subpackages-generated.md.md` | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-212234
- **Evidence revision**: 901bea2549a2314ad612a233a5e4e16d3e9d52d3
- **Related target files**: `scripts/agent/services/export_formatter.py`, `scripts/agent/commands/cmd_session.py`, `scripts/agent/commands/cmd_context.py`, `scripts/agent/commands/cmd_rag_export.py`, `scripts/agent/commands/registry.py`, `scripts/agent/commands/cmd_debug.py`, `scripts/agent/commands/cmd_mcp.py`, `scripts/agent/commands/command_defs_list.py`, `scripts/agent/repl_input_loop.py`, `tests/test_export_formatter.py`, `tests/agent/services/test_commands_utils.py`, `tests/agent/commands/test_command_arg_parsing.py`, `tests/agent/commands/test_cmd_debug.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_command_def_sync.py`, `tests/agent/test_repl.py`, `tests/agent/test_history_compression_consistency.py`, `docs/23_agent/agent_05_llm-and-streaming.md`, `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `docs/23_agent/agent_14_reference-api-subpackages-generated.md`, `tests/agent/commands/test_command_registry_consistency.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `scripts/agent/services/export_formatter.py` line 40 | `scripts/agent/services/export_formatter.py` | Phase 1 | AC-1 | `tests/test_export_formatter.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; pinned fence assertions | `tests/agent/services/test_commands_utils.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Required Changes; `scripts/agent/commands/cmd_session.py` lines 194-211 | `scripts/agent/commands/cmd_session.py` | Phase 2 | AC-1 | `tests/agent/commands/test_command_arg_parsing.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `--output` in the canonical definition | `scripts/agent/commands/command_defs_list.py` | Phase 2 | AC-2 | `tests/agent/commands/test_command_defs.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; user decision D3 | `scripts/agent/commands/cmd_context.py` | Phase 3 | AC-2 | `tests/agent/commands/test_agent_cmd_context.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; module removal | `scripts/agent/commands/cmd_rag_export.py` | Phase 3 | AC-2 | `tests/agent/test_history_compression_consistency.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; registry wiring | `scripts/agent/commands/registry.py` | Phase 3 | AC-2 | `tests/agent/commands/test_command_registry_consistency.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `scripts/agent/commands/cmd_debug.py` lines 55-58 | `scripts/agent/commands/cmd_debug.py` | Phase 3 | AC-2 | `tests/agent/commands/test_cmd_debug.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `scripts/agent/commands/registry.py` lines 157-170 | `scripts/agent/commands/registry.py` | Phase 3 | AC-2 | `tests/agent/commands/test_command_registry_consistency.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; user decision D5; `scripts/agent/commands/cmd_mcp.py` lines 412-416 | `scripts/agent/commands/cmd_mcp.py` | Phase 3 | AC-2 | `tests/agent/commands/test_cmd_mcp.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; `scripts/agent/repl_input_loop.py` line 290 | `scripts/agent/repl_input_loop.py` | Phase 3 | AC-3 | `tests/agent/test_repl.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; CI check | `tests/agent/commands/test_command_def_sync.py` | Phase 4 | AC-2 | itself | Confirmed by repository evidence |
| REQ-007 | Required Changes; `docs/23_agent/agent_05_llm-and-streaming.md` line 50 | `docs/23_agent/agent_05_llm-and-streaming.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | N/A: documentation gate | Confirmed by repository evidence |
| REQ-007 | Required Changes; `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` line 48 | `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | N/A: documentation gate | Confirmed by repository evidence |
| REQ-007 | Documentation Impact; generated reference row | `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-26: Pinned-count test discovered during Step 3c: the module removal changes both counts | tests/agent/commands/test_command_registry_consistency.py | Phase 3 | AC-2 | itself | Confirmed by repository evidence |
