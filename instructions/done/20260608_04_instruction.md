# Refactoring Plan

## 1. Global Strategy
- Lean CLI Layer: Decouple command mixins. Move state mutation, business logic, and output formatting away from the CLI layer into dedicated Service and Formatter layers. Eliminate mixed responsibilities like `print()`, `args.split()`, and direct `ctx` updates.
- Remove Backward Compatibility: Clean up legacy code. Target the `mask_args` backward-compatible re-export in `registry.py` as the initial cleanup checkpoint to organize old public interfaces.
- Refine Exception Handling: Reduce the use of broad `except Exception` blocks across multiple files. Replace them with granular error handling to clearly pinpoint failure locations.

## 2. Refactoring Steps

### Objective
Prioritize removing backward-compatible code, moving state mutation logic to the Service layer, and leaning out CLI responsibilities.

Key targets:
- Legacy re-exports in `registry.py`
- Direct state mutations in `cmd_context.py`, `cmd_session.py`, `cmd_db.py`, and `cmd_memory.py`
- Bloated handling logic in `cmd_config.py`, `cmd_ingest.py`, and `cmd_tooling.py`

### Step 1: Remove Compatibility Layer & Clean Up Public API
#### Actions
- Delete the `mask_args` backward-compatible re-export from `registry.py` and remove it from `__all__`.
- Review public utility functions in `registry.py`. Restrict internal-only functions to internal use. (e.g., Stop re-exporting `_budget_breakdown` from `cmd_context.py` if it is only used internally).
- Update outdated module header descriptions (e.g., "Extracted from agent_commands.py") to reflect current actual responsibilities.

#### Target Files
- `registry.py`
- `cmd_context.py`
- Module docstrings in `cmd_config.py`, `cmd_session.py`, `cmd_db.py`, and `cmd_ingest.py`

#### Deliverables
- Cleaned `registry.py` with legacy re-exports removed.
- Updated public API list aligned with current module scopes.
- Cleaned file headers with legacy/outdated design comments removed.

### Step 2: Migrate State Mutation Logic to Service Layer
#### Actions
- Move direct updates to `ctx.conv.history`, `ctx.stats`, and `ctx.session` from `_cmd_clear()`, `_cmd_undo()`, and `_cmd_system()` in `cmd_context.py` to a dedicated history/session service.
- Extract mixed logic from `cmd_session.py`:
  - Move `_load_session()` (handles history rebuilding, session switching, and stats resetting simultaneously) into a unified Session Switch Service.
  - Move `_generate_session_title()` (handles HTTP requests and local fallbacks internally) to a separate Title Generation Service.
- Offload destructive or maintenance operations (`/db clean`, `/db purge`, `/db recover`, `/db vacuum`) from `cmd_db.py` to a DB Maintenance Service. Limit the CLI layer strictly to argument parsing and output presentation.
- Refactor `cmd_memory.py`: Move mixed tasks (argument parsing, memory retrieval, deletion, pin/unpin, pruning, and audit logging) into an explicit Memory Application Service.
- Relocate `_reset_session_stats()` from `mixin_base.py` to the stats owner API. Prevent mixins from directly mutating state fields.

#### Target Files
- `cmd_context.py`
- `cmd_session.py` / `mixin_base.py`
- `cmd_db.py`
- `cmd_memory.py`

#### Deliverables
- Decoupled architecture design covering History, Session Switch, DB Maintenance, and Memory services.
- Refactored command mixins with minimized direct `ctx` state modifications.

### Step 3: Lean CLI Layer & Separation of Concerns
#### Actions
- Refactor `cmd_config.py`: Decouple mixed responsibilities (fetching, formatting, displaying, and applying configuration) inside `_print_config_values()`, `_cmd_config()`, `_cmd_stats()`, and `_cmd_set()`. Divide into data access and presentation layers.
- Refactor `cmd_ingest.py`: Delegate the core actions of `_cmd_export()`, `_cmd_ingest()`, and `_cmd_compact()` to services. Remove mixed argument parsing and history update logic from the command layer.
- Refactor `cmd_tooling.py`: Separate the display model and presenter from `_tool_list()` and `_tool_show()` (currently handling data retrieval, JSON decoding, formatting, and rendering all in one). Align flag toggles in `_cmd_plan()` with the state mutation infrastructure.

#### Target Files
- `cmd_config.py`
- `cmd_ingest.py` / `utils.py`
- `cmd_tooling.py`

#### Deliverables
- Lean dispatcher implementations for config, ingest/export, and tooling commands.
- CLI implementation structurally separated into clear Formatters, Presenters, and Services.

## 3. Completion Criteria
- [ ] Backward-compatible re-exports are fully removed from `registry.py`.
- [ ] Core state mutations in `cmd_context`, `cmd_session`, `cmd_db`, and `cmd_memory` run through designated services.
- [ ] `cmd_config`, `cmd_ingest`, and `cmd_tooling` act strictly as lean command dispatchers.
