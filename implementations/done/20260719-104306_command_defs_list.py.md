Source plan: `plans/20260719-093757_plan.md` ("Add `/diff` slash command to review files the agent
wrote/edited this session"), Implementation step 1.

No existing implementations doc (under `implementations/` or `implementations/done/`) covers adding a
`/diff` `CommandDef` entry. Two same-filename docs exist and were read in full:
`implementations/20260719-103003_command_defs_list.py.md` and
`implementations/20260719-103604_command_defs_list.py.md` — both only append `|rag-consistency` and
`|rag-rebuild-fts` to the **existing `/session`** `CommandDef`'s help string (lines 77-84 of the current
file). Neither touches `/diff` or adds any new `CommandDef` entry; grepped both for `diff`/`_cmd_diff`/
`"/diff"` with no matches. One older doc, `implementations/done/20260712-180631_command_defs_list.md`,
matches on the substring "diff" only inside an unrelated validation-table row ("No diff after format") —
confirmed unrelated. Flagged as checked, not a genuine overlap; this doc adds a brand-new, independent
`CommandDef` entry and does not conflict with the two sibling docs above.

## Goal

Add a new exact-match, async `CommandDef("/diff", ...)` entry to `_COMMANDS` in
`scripts/agent/commands/command_defs_list.py`, registering the `/diff` slash command (implemented by
`_cmd_diff` in `cmd_context.py`, per the paired doc) with the command registry.

## Scope

**In scope**
- Add one new `CommandDef(...)` entry to the `_COMMANDS` list literal in
  `scripts/agent/commands/command_defs_list.py`.

**Out of scope**
- Any change to the existing `/session` `CommandDef` entry (lines 77-84) — that entry is owned by the
  two sibling docs listed above (`20260719-103003_command_defs_list.py.md`,
  `20260719-103604_command_defs_list.py.md`), which append `rag-consistency`/`rag-rebuild-fts` to its
  help string. Those edits are to a *different* positional argument of a *different* `CommandDef`
  instance in the same list literal — no textual overlap with this doc's insertion point.
- Implementing `_cmd_diff` itself — covered by the paired
  `implementations/20260719-104343_cmd_context.py.md`.
- `scripts/agent/commands/registry.py` — no change; `_ContextMixin` (where `_cmd_diff` lives) is
  already in `CommandRegistry`'s MRO (verified: `registry.py` composes `_ContextMixin` among its base
  classes, and its fail-fast `hasattr` check validates handler existence generically, not per-command).

## Assumptions

1. `_COMMANDS` (`command_defs_list.py:26`) is `_COMMANDS: list[CommandDef] = [...]` — a plain list,
   confirmed by direct read of the current file (`scripts/agent/commands/command_defs_list.py:26`).
   Consistent with the two sibling docs' Assumption 3.
2. `CommandDef`'s dataclass fields, in order (`scripts/agent/commands/command_defs.py:31-40`, verified
   by direct read): `name: str`, `prefix: bool`, `is_async: bool`, `handler: str`, `help: str`,
   `subcommands: list[SubcommandSpec] = field(default_factory=list)`. All 21 existing entries in
   `_COMMANDS` use positional arguments (no `subcommands=` usage anywhere in the file except the
   line-12 docstring mention) — this plan follows the same convention, i.e. 5 positional args and no
   `subcommands` list.
3. `/diff` takes no sub-arguments in v1 (per the plan's Design step 1: "exact-match (no sub-args
   needed for v1), async"), so `prefix=False`. It requires an `await ctx.services...tools.execute(...)`
   call (per the paired `cmd_context.py` doc), so `is_async=True`.
4. Comparable exact-match async precedent already exists in the file: `CommandDef("/compact", False,
   True, "_cmd_compact", "Force immediate compression of conversation history")` at
   `command_defs_list.py:62-68`, under the `# ── Exact-match async ──` section header (line 61). `/diff`
   is placed in this same section, immediately after `/compact`, since it is also exact-match + async
   and there is no more specific section for it (it is not a prefix command, so the `# ── Prefix ... ──`
   sections, lines 69/148, do not apply).
5. The handler method name is `_cmd_diff`, matching the paired `cmd_context.py` doc's method name, and
   following the file's `_cmd_<name-without-slash>` naming convention used by every other entry (e.g.
   `/history` → `_cmd_history`, `/undo` → `_cmd_undo`).

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`.

### Procedure

1. Locate the `# ── Exact-match async ──` section (currently just the `/compact` entry,
   `command_defs_list.py:61-68`).
2. Insert a new `CommandDef` entry immediately after the `/compact` entry (i.e. before the
   `# ── Prefix sync ──` comment at line 69), so the file reads:
   ```python
   # ── Exact-match async ────────────────────────────────────────────────────
   CommandDef(
       "/compact",
       False,
       True,
       "_cmd_compact",
       "Force immediate compression of conversation history",
   ),
   CommandDef(
       "/diff",
       False,
       True,
       "_cmd_diff",
       "Show diffs for files written/edited this session",
   ),
   # ── Prefix sync ──────────────────────────────────────────────────────────
   ```
3. Run `uv run ruff format scripts/agent/commands/command_defs_list.py` and
   `uv run ruff check scripts/agent/commands/command_defs_list.py --fix` to normalize formatting.
4. No other line in the file needs to change — this is a pure insertion, not an edit to any existing
   entry. If, at implementation time, the two sibling `/session`-help-string docs have already landed,
   their edits are to lines 77+ (now shifted down by this insertion) and remain textually independent;
   insert this new entry first or after — order between the three docs does not matter since they touch
   disjoint `CommandDef` instances.

### Method

Single-entry insertion into an existing list literal. No new abstractions, no changes to
`command_defs.py`'s dataclasses.

### Details

- No new types or signatures. `CommandDef("/diff", False, True, "_cmd_diff", "Show diffs for files
  written/edited this session")` — 5 positional args, matching every other entry's calling
  convention in this file.
- The handler string `"_cmd_diff"` must exactly match the method name defined on `_ContextMixin` in
  `cmd_context.py` (see the paired doc) — `CommandRegistry`'s fail-fast `hasattr` check
  (referenced in the plan's Affected areas, `registry.py` lines ~74-84) will raise at startup if these
  two names ever diverge, so this is a hard consistency requirement, not just a convention.
- `tools/check_agent_docs_consistency.py`'s `check_command_drift` (verified: `tools/
  check_agent_docs_consistency.py:176-233`) regex-extracts registered command names from this exact
  file's `CommandDef(...)` calls and flags any doc-referenced `/command` name absent from `_COMMANDS`
  as a WARNING — this insertion must land before (or together with) the docs update
  (paired doc for `docs/05_agent_07_10_...md`) so that doc's new `/diff` row does not trigger this
  check.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/commands/command_defs_list.py && uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/command_defs_list.py` | 0 new errors vs. baseline |
| New entry present | `rg -n 'CommandDef\(\s*"/diff"' scripts/agent/commands/command_defs_list.py` | 1 match |
| Handler name matches paired doc | `rg -n '"_cmd_diff"' scripts/agent/commands/command_defs_list.py scripts/agent/commands/cmd_context.py` | 2 matches (one per file), identical string |
| No accidental edit to `/session` entry | `rg -n '"/session"' scripts/agent/commands/command_defs_list.py` | still exactly 1 match, entry unchanged apart from sibling docs' own help-string edits |
| Command-def sync suite | `uv run pytest tests/test_command_def_sync.py -v` | all pass, including new `/diff` entry validated against its handler |
| Docs consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING once the docs doc (paired) also lands |
| Full command-registry smoke test | `uv run pytest tests/test_agent_cmd_context.py -v` | all pass |
