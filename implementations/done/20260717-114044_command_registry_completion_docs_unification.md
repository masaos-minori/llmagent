# Implementation Procedure: Unify Slash Command Registry, Completion Behavior, and CLI Documentation

Source plan: `plans/20260717-002601_plan.md`
Source requirement: `requires/20260716_16_require.md`

## Goal

Eliminate the confirmed documentation drift between the slash command registry (`_COMMANDS`), tab-completion (`SLASH_COMMANDS`), and the CLI documentation set — the underlying code is already correctly unified (commit `16ba870d`); only docs and guard-rail tests are missing — and add tests so the drift cannot silently reappear.

## Scope

**In scope**
- `docs/05_agent_01_system-overview.md`: remove the stale `/db` command-table row (line 129); rewrite the stale "Current behavior (コマンド一覧の相違)" section (lines 140-146) to state completion is derived from `_COMMANDS` with no exclusions.
- `docs/05_agent_02_runtime-architecture-part1.md` and `docs/05_agent_07_03_cli-and-commands-command-registry.md`: reword the bare "15 mixins" figure to state the 13-direct + 2-nested breakdown explicitly.
- CLI reference doc set (most likely `docs/05_agent_07_05_cli-and-commands-repl-io.md`): add a new "REPL prompt" subsection documenting the current fixed `"> "` prompt and no session-id display.
- `tests/docs/test_command_docs_sync.py`: update the doc-file list from the removed `docs/05_agent_07_cli-and-commands.md` to the current split files (at minimum `05_agent_07_08` through `05_agent_07_11`).
- `tests/test_command_registry_consistency.py` (or a new focused module): add a drift-guard test (`SLASH_COMMANDS == _COMMANDS names | reserved_repl_command_names()`) and a mixin-count guard test (via `inspect.getmro(CommandRegistry)`).

**Out of scope**
- Redesigning the slash command framework.
- Removing valid slash commands.
- Changing command business behavior.
- Redesigning the CLI or changing the prompt style itself — document current behavior only.
- Adding `completion_excluded` metadata to `CommandDef` — no command needs it today; document this as a deliberate decision instead (Assumption 2).
- Any code change to `command_defs_list.py`, `repl.py`, or `registry.py` — verified already correct; touch only if a new guard test reveals something this plan's manual read missed.

## Assumptions

1. The completion-drift problem described in the source requirement was already fixed in commit `16ba870d` ("feat: unify command metadata as single source of truth", 2026-07-15): `AgentREPL.SLASH_COMMANDS` is a `cached_property` derived from `builtin_command_names() | reserved_repl_command_names()` — confirmed by direct read of `scripts/agent/repl.py:52-89`. The remaining gap is purely documentation and missing regression coverage.
2. No command currently needs `completion_excluded` metadata — all 18 `_COMMANDS` entries are includable in tab completion today, and `CommandDef` has no such field. This is documented as a deliberate decision, not implemented as a speculative field.
3. `AgentREPL._prompt` returns a fixed `"> "` with no session id (`scripts/agent/repl.py:96-98`) — documented as-is per the "do not redesign the CLI" non-goal.
4. "CommandRegistry mixin count" is ambiguous between 13 direct base classes (`scripts/agent/commands/registry.py:60-74`) and the full transitive tree including `_ConfigMixin`'s own two nested mixins (`_ConfigDisplayMixin`, `_ConfigStatsMixin`), totaling 15. Both existing docs state "15" without this qualification.
5. **Confirmed still current (verified 2026-07-17)**: `docs/05_agent_01_system-overview.md:129` still contains the stale `/db` command-table row; no `SLASH_COMMANDS ==`-style drift-guard test exists yet in `tests/test_command_registry_consistency.py`. Both gaps this plan targets are still open.
6. **Overlap with a separately-tracked plan**: `plans/done/20260717-095443_plan.md` (requirement 21, defect P-3) independently targets the exact same two items — removing the stale `/db` row from `docs/05_agent_01_system-overview.md:129`, and updating `tests/docs/test_command_docs_sync.py`'s stale file list. Implementation Steps 1 and 5 below (marked "SHARED WITH REQ-21 P-3") must be implemented **once**, not twice — whichever of this document or `implementations/` (once req-21's own procedure doc is created) is executed first should perform the `/db` row removal and doc-sync-test file-list fix; the other should verify the fix already landed rather than re-applying it, to avoid a duplicate/conflicting edit.

## Implementation

### Target file

Primary: `docs/05_agent_01_system-overview.md`, `tests/docs/test_command_docs_sync.py`, `tests/test_command_registry_consistency.py`. Secondary: `docs/05_agent_02_runtime-architecture-part1.md`, `docs/05_agent_07_03_cli-and-commands-command-registry.md`, `docs/05_agent_07_05_cli-and-commands-repl-io.md` (or whichever `05_agent_07_*` file's content best fits the REPL-prompt subsection — re-grep at implementation time per Details below).

### Procedure

1. **[SHARED WITH REQ-21 P-3 — verify not already done before applying] Fix the currently-failing test**: remove the stale `/db` row from `docs/05_agent_01_system-overview.md`'s command table (line 129) so `tests/docs/test_command_docs_sync.py::test_active_docs_match_registered_commands` passes.
2. **Rewrite the stale "Current behavior" section** in `docs/05_agent_01_system-overview.md` (lines 140-146) to state that completion is derived from `_COMMANDS` with `/exit` added via `reserved_repl_command_names()`, and that no commands are currently excluded from completion.
3. **Reword mixin count documentation** in both `docs/05_agent_02_runtime-architecture-part1.md` and `docs/05_agent_07_03_cli-and-commands-command-registry.md` to state the 13-direct + 2-nested breakdown explicitly instead of a bare "15".
4. **Add REPL prompt documentation**: re-grep each `docs/05_agent_07_*` candidate file's content for existing "prompt" mentions or slash-command listings immediately before choosing a target (do not rely solely on filename inference); add a short subsection describing the fixed `"> "` prompt, absence of session-id display, and that `CLIView.read_multiline`'s continuation input does not change the prompt string.
5. **[SHARED WITH REQ-21 P-3 — verify not already done before applying] Fix the doc-sync test's stale path**: update `tests/docs/test_command_docs_sync.py`'s checked-file list from the removed `docs/05_agent_07_cli-and-commands.md` to the current split files (at minimum `05_agent_07_08` through `05_agent_07_11`, whose filenames indicate slash-command content); treat any newly-surfaced stale-command findings from widening this list as expected discoveries to fix in the same pass, not scope creep.
6. **Add the completion-drift guard test**: assert `AgentREPL.SLASH_COMMANDS == frozenset(cmd.name for cmd in _COMMANDS) | reserved_repl_command_names()` in `tests/test_command_registry_consistency.py` (or a new focused module if that file's fixture shape doesn't fit).
7. **Add the mixin-count guard test**: compute the actual total mixin count via `inspect.getmro(CommandRegistry)` filtered to class names ending in `Mixin`, and assert it matches the documented total (15); document the `*Mixin`-suffix naming-convention dependency directly in the test's docstring as a known limitation.
8. **Verification**: run the full validation sequence scoped to the changed test/doc files, then the full suite.

### Method

- Direct Markdown edits for all doc changes; direct pytest additions for the two new guard tests.
- Step 1 is the same single-row edit already specified in `implementations/` for req-21 P-3 (or will be, once that procedure doc exists) — implement once, cross-reference in both places.
- New guard tests follow the existing pattern in `tests/test_command_registry_consistency.py` (or the closest existing sibling test file) rather than inventing a new test-module layout.

### Details

- Do not add `completion_excluded` to `CommandDef` — Assumption 2 documents this as a deliberate non-change.
- Do not change the REPL prompt string itself — document current behavior only, per the "do not redesign the CLI" non-goal.
- Before choosing the REPL-prompt doc target file, grep the actual content of each `05_agent_07_*` file rather than trusting the filename alone — this plan's own Risks section flags this as a real miss-risk given 11 split files exist.
- Before applying Steps 1/5, check whether `implementations/`'s req-21 (P-3) procedure has already applied the identical `/db`-row removal and doc-sync-test fix — if so, skip re-applying and only add this document's Step 6/7 guard tests plus Steps 2-4's remaining doc work.
- The mixin-count guard test's `*Mixin`-suffix dependency must be called out in-code (docstring/comment), not left as a silent limitation.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_01_system-overview.md` | Regression (pre-existing failure) | `uv run pytest tests/docs/test_command_docs_sync.py -v` | `test_active_docs_match_registered_commands` passes (currently fails) |
| `tests/docs/test_command_docs_sync.py` | Unit (updated paths) | `uv run pytest tests/docs/test_command_docs_sync.py -v` | All tests pass, now covering the current split doc files instead of silently skipping |
| `repl.py` / `command_defs_list.py` drift guard | New unit test | `uv run pytest tests/test_command_registry_consistency.py -v` | New test asserting `SLASH_COMMANDS` == `_COMMANDS` names + `/exit` passes |
| `registry.py` mixin count guard | New unit test | `uv run pytest tests/test_command_registry_consistency.py -v` | New test computing the actual mixin total (15) passes and matches docs |
| Full CLI/command test set | Regression | `uv run pytest tests/test_command_def_sync.py tests/test_command_registry_consistency.py tests/test_repl.py tests/test_commands_utils.py tests/test_removed_commands.py tests/docs/test_command_docs_sync.py -v` | No new failures |
| Full suite | Regression | `uv run pytest -v` | No new failures |
| Lint/format | Static | `uv run ruff check scripts/ tests/` | No new errors |
| Pre-commit | Final gate | `uv run pre-commit run --all-files` | All hooks pass |
