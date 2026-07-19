## Goal

Add a general regression test asserting that the `/stats` hint, when printed, always references a
command name that actually exists in the command registry — so the exact class of drift this plan
fixes (a hint pointing at a removed command) cannot silently recur in the future.

## Scope

**In scope**
- Add one new test function/method to `tests/test_agent_cmd_config.py` (the file that already
  covers `_cmd_stats()`, via the `TestCmdStats` class) that:
  1. Forces `rag_db_configured=True` so the hint line is printed.
  2. Extracts the command token from the printed hint line.
  3. Asserts that command name is present among the command names defined in
     `agent.commands.command_defs_list._COMMANDS`.

**Out of scope**
- Any change to `_get_rag_db_configured()` or `_cmd_stats()` production logic.
- Any change to `tests/test_cmd_config_char.py` — confirmed (Assumption 2) that this file is
  unrelated to `_cmd_stats`/hint testing and is not the right home for this test.
- Any change to the existing 7 `TestCmdStats` test methods already in this file.

## Assumptions

1. `tests/test_agent_cmd_config.py` is the correct home for this test: it already has a `TestCmdStats`
   class (lines 62-143) with 7 test methods that call `cmd._cmd_stats()` and read
   `capsys.readouterr().out`, and already uses the pattern `with patch("db.config.build_db_config",
   side_effect=ValueError("bad config")):` (confirmed at lines 333-342, `test_db_config_error_shows_message`)
   to control `rag_db_configured`'s value indirectly. `tests/test_cmd_config_char.py` was checked and
   confirmed unrelated — it only tests `_print_config_values`/`TestPrintConfigValues` (via `_ConfigMixin`
   imported from `cmd_config.py`), with zero references to `_cmd_stats`, `rag_db_configured`, `Hint`,
   or the RAG consistency hint text. Neither file currently has any test asserting the RAG hint text
   itself — this is new coverage, not a modification of an existing assertion.
2. `_get_rag_db_configured(ctx)` (`cmd_config_stats.py:47-55`) calls `db.config.build_db_config()` for
   real, wrapped in a try/except — it is not directly ctx-driven. To force `rag_db_configured=True`
   in a test, the existing file's pattern is to patch `db.config.build_db_config` (patch target string
   `"db.config.build_db_config"`, confirmed live in this file at line 333) so it returns successfully
   (rather than raising), since success is what makes `_get_rag_db_configured` return `True`.
3. `agent.commands.command_defs_list._COMMANDS` is a **list of `CommandDef`**, not a dict — confirmed
   via `grep -n "_COMMANDS" scripts/agent/commands/command_defs_list.py`, which shows
   `_COMMANDS: list[CommandDef] = [...]` at line 26. This corrects the plan's Scope text, which
   describes "asserting the command name ... is present in `_COMMANDS`" without specifying the
   container type. The test must therefore check membership against
   `{c.name.lstrip("/") for c in _COMMANDS}` (or equivalent), not a dict-key lookup — `CommandDef.name`
   holds the leading-slash form (e.g. `"/session"`), per `command_defs_list.py:77` (`CommandDef(
   "/session", ...)`), so the hint's parsed command token needs a matching slash-inclusive or
   slash-stripped comparison depending on how it's extracted from the hint text.
4. The hint text as of this plan's companion `cmd_config_stats.py` fix
   (`implementations/20260719-103030_cmd_config_stats.py.md`) reads:
   `"  Hint          : Run /session rag-consistency for index integrity status"`. The command token to
   extract and validate is `/session` (the registry only tracks top-level command names, not
   subcommands like `rag-consistency` — confirmed: `CommandDef` entries are one per top-level slash
   command, e.g. `"/session"`, not per subcommand). So "the command token parsed out of the hint line"
   should be parsed as the first `/`-prefixed word in the hint string (`/session`), and the test
   asserts that token is a registered top-level command name — it does not (and structurally cannot,
   given `_COMMANDS`'s granularity) validate that `rag-consistency` specifically is a valid subcommand
   of `/session`; that finer-grained check is out of scope for this general regression test and is
   instead covered by the dispatch-level tests in
   `implementations/20260719-103047_test_agent_cmd_session.py.md`.
5. This test's value is specifically to catch a *future* recurrence of this exact bug class (hint
   text drifting to reference a since-removed top-level command) — it is deliberately generic (parses
   whatever command name currently appears in the hint) rather than hard-coding `/session`, so it
   remains a meaningful regression guard even if the command name changes again later.

## Implementation

### Target file

`tests/test_agent_cmd_config.py`.

### Procedure

1. Add an import for `_COMMANDS`: `from agent.commands.command_defs_list import _COMMANDS` (or
   `import agent.commands.command_defs_list as command_defs_list` and reference
   `command_defs_list._COMMANDS`, matching whichever import style dominates this file's existing
   top-of-file imports — check before adding a duplicate import style).
2. Add a new test function inside (or alongside) `TestCmdStats`, e.g.:
   ```python
   def test_stats_hint_references_a_registered_command(
       self, capsys: pytest.CaptureFixture
   ) -> None:
       import re
       from unittest.mock import patch

       from agent.commands.command_defs_list import _COMMANDS

       cmd = _make_cmd()  # or this file's equivalent fixture helper
       with patch("db.config.build_db_config"):  # succeeds -> rag_db_configured=True
           cmd._cmd_stats()
           out = capsys.readouterr().out

       hint_lines = [line for line in out.splitlines() if "Hint" in line]
       assert hint_lines, "expected a Hint line to be printed when rag_db_configured=True"

       match = re.search(r"(/\w[\w-]*)", hint_lines[0])
       assert match, f"no command token found in hint line: {hint_lines[0]!r}"
       command_token = match.group(1)

       registered_names = {c.name for c in _COMMANDS}
       assert command_token in registered_names, (
           f"/stats hint references {command_token!r}, which is not a registered command"
           f" in _COMMANDS: {sorted(registered_names)}"
       )
   ```
   (Exact fixture/helper name for constructing `cmd` — e.g. `_make_cmd()` — must match whatever this
   file's existing `TestCmdStats` tests already use; verify the helper name by reading the class's
   other test methods before finalizing, since this doc's investigation did not re-quote that helper
   verbatim for this specific file.)
3. Confirm the `re.search` pattern correctly extracts `/session` from the current hint text
   `"  Hint          : Run /session rag-consistency for index integrity status"` (it matches
   `/session` as the first `/`-prefixed token; `rag-consistency` is a plain word with no leading `/`,
   so it is not accidentally matched instead).

### Method

Plain `unittest.mock.patch`-based unit test, following this file's existing convention of patching
`db.config.build_db_config` to control `rag_db_configured`. No fixtures beyond what `TestCmdStats`
already uses.

### Details

No new production types. The test references `agent.commands.command_defs_list._COMMANDS` (a
module-private-by-convention name, leading underscore) directly from the test file — this matches
how this repo's other command-registry tests (e.g. `tests/test_command_def_sync.py`) already import
and inspect `_COMMANDS` directly for sync-checking purposes, so it is not a new precedent.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New test passes | `uv run pytest tests/test_agent_cmd_config.py -v -k hint` | passes |
| Regression guard works | Manually verify by temporarily reverting `cmd_config_stats.py`'s hint to reference a nonexistent command and re-running the new test | test fails (confirms it actually catches the drift class) |
| Full file regression | `uv run pytest tests/test_agent_cmd_config.py -v` | all tests pass, no new failures |
| Format/lint | `uv run ruff format tests/test_agent_cmd_config.py && uv run ruff check tests/test_agent_cmd_config.py` | 0 errors |
| Type check | `uv run mypy tests/test_agent_cmd_config.py` | 0 new errors vs. baseline |
