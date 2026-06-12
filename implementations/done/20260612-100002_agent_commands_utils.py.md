# Goal

Remove backward-compatibility re-exports (`render_export`, `render_history_md`,
`write_export`) from `agent/commands/utils.py` and update `cmd_ingest.py` to import
them directly from `agent.services.export_formatter`.

# Scope

- `scripts/agent/commands/utils.py` — remove re-export imports and `__all__` entries
- `scripts/agent/commands/cmd_ingest.py` — update import source

# Assumptions

1. `utils.py` currently imports and re-exports `render_export`, `render_history_md`,
   `write_export` from `agent.services.export_formatter`.
2. `cmd_ingest.py` line 17 imports these names from `agent.commands.utils`.
3. No other file imports these names from `agent.commands.utils` (verify with grep).
4. `agent.services.export_formatter` already exports all three names directly.

# Implementation

## Target file

- `scripts/agent/commands/utils.py`
- `scripts/agent/commands/cmd_ingest.py`

## Procedure

1. Confirm all callers:
   ```bash
   grep -rn "from agent.commands.utils import.*render_export\|from agent.commands.utils import.*write_export\|from agent.commands.utils import.*render_history_md" scripts/
   ```
2. In `cmd_ingest.py`, change:
   ```python
   from agent.commands.utils import render_export, write_export
   ```
   to:
   ```python
   from agent.services.export_formatter import render_export, write_export
   ```
3. In `utils.py`, remove:
   - The import lines for `render_export`, `render_history_md`, `write_export`
   - Their entries in `__all__` (if present)
4. Run ruff + mypy to confirm no broken imports.

## Method

Import path change in `cmd_ingest.py`; remove dead re-export lines from `utils.py`.

## Details

After the change, `utils.py` should contain only its own utilities
(`parse_command_args`, `parse_flag_int`, `parse_flag_str`, etc.) with no
re-exports from other modules.

# Validation plan

- `grep -n "render_export\|render_history_md\|write_export" scripts/agent/commands/utils.py` → 0 hits
- `uv run ruff check scripts/agent/commands/utils.py scripts/agent/commands/cmd_ingest.py`
- `uv run mypy scripts/agent/commands/utils.py scripts/agent/commands/cmd_ingest.py`
- `uv run pytest tests/ -k "ingest" --ignore=tests/test_create_schema.py -v`
