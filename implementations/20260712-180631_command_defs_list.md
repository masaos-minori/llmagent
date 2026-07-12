# Implementation: command_defs_list.py — register `/skill` CommandDef

Source plan: `plans/20260712-174955_plan.md` (Implementation Steps, Phase 1)

## Goal

Register `/skill` as a recognized prefix command in the single source of truth
(`_COMMANDS`) so `CommandRegistry.dispatch()` routes `/skill` and `/skill <name> [args]`
lines to a handler method named `_cmd_skill`.

## Scope

**In scope**
- One new `CommandDef(...)` entry appended to `_COMMANDS` in
  `scripts/agent/commands/command_defs_list.py`.

**Out of scope**
- The handler method itself (`_cmd_skill`) — implemented in a separate document
  (`cmd_skill.py`, see `implementations/{same-batch}_cmd_skill.md`).
- Any change to `CommandDef` / `SubcommandSpec` dataclasses in `command_defs.py`.

## Assumptions

1. `_COMMANDS` in `command_defs_list.py` is edited in isolation from
   `scripts/agent/commands/registry.py` and `scripts/agent/commands/cmd_skill.py`, but this
   commit is not independently testable/mergeable on its own — `CommandRegistry.__init__`'s
   fail-fast handler check (`registry.py:84-88`) will raise `AttributeError` at
   `CommandRegistry()` construction time until `_cmd_skill` exists on some mixin in the
   base-class list. This file's change and the `cmd_skill.py` + `registry.py` change
   (Phase 2) must land in the same commit / be validated together, matching the plan's
   explicit note under "Implementation Steps".
2. `/skill` is a prefix command (`prefix=True`) because it accepts an optional
   `[name] [args]` payload, and synchronous (`is_async=False`) because its handler does
   only local filesystem reads, matching the shape of the existing `/plugin` entry.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Open `scripts/agent/commands/command_defs_list.py`.
2. Locate the existing `/plugin` `CommandDef` block (currently ends at line 174, directly
   before the `# ── Prefix async ──` section comment).
3. Insert a new `CommandDef` for `/skill` immediately after the `/plugin` block and before
   the `# ── Prefix async ──` comment, keeping it inside the "Prefix sync" group (`/skill`
   is sync, like `/plugin`, not async like `/mdq`).
4. Do not reorder any existing entries — `_COMMANDS` order determines `dispatch()`'s
   linear match order (`registry.py:129-145`); appending at the end of the sync-prefix
   group is safe since command names don't overlap as prefixes of one another.

### Method

Direct text insertion via an editor tool (e.g. `Edit`), anchored on the exact existing
`/plugin` `CommandDef` block text to guarantee correct placement.

### Details

Insert this block right after the `/plugin` `CommandDef` (and before the
`# ── Prefix async ──` comment):

```python
    CommandDef(
        "/skill",
        True,
        False,
        "_cmd_skill",
        "[name] [args]  List skills, or load skills/<name>/SKILL.md as ephemeral system context",
    ),
```

Resulting fragment (context shown for anchoring; the `/plugin` block and the
`# ── Prefix async ──` comment are pre-existing, unchanged):

```python
    CommandDef(
        "/plugin",
        True,
        False,
        "_cmd_plugin",
        "status  Show plugin load results (loaded, failed, conflicts)",
    ),
    CommandDef(
        "/skill",
        True,
        False,
        "_cmd_skill",
        "[name] [args]  List skills, or load skills/<name>/SKILL.md as ephemeral system context",
    ),
    # ── Prefix async ───────────────────────────────────────────────────────────
```

Field values, per the `CommandDef` dataclass (`name`, `prefix`, `is_async`, `handler`,
`help`):
- `name="/skill"`
- `prefix=True` — accepts `[name] [args]` after the command token
- `is_async=False` — handler is synchronous (filesystem-only I/O)
- `handler="_cmd_skill"` — must exactly match the method name defined in `cmd_skill.py`
- `help="[name] [args]  List skills, or load skills/<name>/SKILL.md as ephemeral system context"`

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Syntax | `uv run python -m compileall -q scripts/agent/commands/command_defs_list.py` | No syntax errors |
| Format | `uv run ruff format scripts/agent/commands/command_defs_list.py` | No diff after format (or auto-formatted cleanly) |
| Lint | `uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/command_defs_list.py` | No new errors |
| Integration (requires Phase 2 landed) | `uv run pytest tests/test_cmd_registry_ingest_removal.py tests/test_cmd_registry_note_removal.py -v` | `CommandRegistry()` still constructs without `AttributeError` |
| Full regression (requires Phase 2 landed) | `uv run pytest -v` | No new failures |

Note: this file's change alone is not independently testable — `CommandRegistry.__init__`
will raise `AttributeError: CommandDef references unknown handler: '_cmd_skill'` until the
`cmd_skill.py` + `registry.py` changes from Phase 2 are also applied. Validate both
together.
