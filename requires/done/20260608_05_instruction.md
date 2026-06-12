# Refactoring Plan

## 1. Global Strategy
- Lean CLI Layer: Decouple command mixins. Move state mutation, business logic, and output formatting away from the CLI layer into dedicated Service and Formatter layers. Eliminate mixed responsibilities like `print()`, `args.split()`, and direct `ctx` updates.
- Remove Backward Compatibility: Clean up legacy code. Target the `mask_args` backward-compatible re-export in `registry.py` as the initial cleanup checkpoint to organize old public interfaces.
- Refine Exception Handling: Reduce the use of broad `except Exception` blocks across multiple files. Replace them with granular error handling to clearly pinpoint failure locations.

## 2. Refactoring Steps

### Objective
Standardize cross-cutting concerns by introducing shared parsers, formatters, error handling, dependency injection, and explicit typing. Prioritize reducing duplication in subcommand routing, usage generation, list rendering, JSON decoding, and exception handling.

### Step 1: Introduce Common Command Parser & Definitions
#### Actions
- **Consolidate Parsing Logic:** Replace repetitive `parts = args.strip().split()` or `split(None, 1)` patterns found across `cmd_session.py`, `cmd_db.py`, `cmd_notes.py`, `cmd_mcp.py`, `cmd_memory.py`, and `cmd_tooling.py` with a central subcommand definition table and common parser.
- **Absorb Local Parsing:** Move localized flag parsing (such as `_parse_flag_int()` and `_parse_flag_str()` in `cmd_db.py`) into the common parser framework.
- **Automate Help/Usage:** Structure command definitions to automatically generate usage text. Target definitions include `/set` parameters in `cmd_config.py`, `list/search/show/pin/unpin/delete/prune` in `cmd_memory.py`, and `add/list/delete` in `cmd_notes.py`.

#### Target Files
- `cmd_session.py`
- `cmd_db.py`
- `cmd_mcp.py`
- `cmd_memory.py`
- `cmd_notes.py`
- `cmd_tooling.py`
- `cmd_config.py`

#### Deliverables
- Shared Command Parser module.
- Central Subcommand Definition Table.
- Automated Usage/Help Generation Infrastructure.

### Step 2: Introduce Common Formatter, Presenter, & Safe Decoding
#### Actions
- **Standardize UI/Display:** Convert ad-hoc list and table rendering logic into standardized formatters/presenters. Target views: session lists (`cmd_session.py`), URL lists/statistics (`cmd_db.py`), note lists (`cmd_notes.py`), tool results (`cmd_tooling.py`), and memory lists/search results (`cmd_memory.py`).
- **Unify JSON Handling:** Route all JSON operations through safe helper utilities. This covers `args_json` decoding in `cmd_tooling.py` and `tool_calls` size measurements in `cmd_context.py`.
- **Decouple Export Logic:** Refactor `render_history_md()`, `render_export()`, and `write_export()` in `utils.py` to return writing results, separating core functionality from the CLI layer.
- **Unify Status Toggles:** Move state and toggle displays in `cmd_debug.py` and `cmd_tooling.py` into a shared Status Presenter.

#### Target Files
- `cmd_session.py`
- `cmd_db.py`
- `cmd_notes.py`
- `cmd_tooling.py`
- `cmd_memory.py`
- `cmd_context.py`
- `utils.py`
- `cmd_debug.py`

#### Deliverables
- Shared Formatter / Presenter modules.
- Safe JSON Decode & Render Helpers.
- List/Detail view implementations structurally separated from business logic.

### Step 3: Standardize Error Handling, Dependency Injection, & Typing
#### Actions
- **Categorize Exception Catching:** Break down broad `except Exception` blocks in `cmd_config.py`, `cmd_session.py`, and `cmd_db.py` into granular types (e.g., I/O, HTTP, config loading, and DB operations).
- **Inject Dependencies:** Refactor tight coupling for better injectability. Eliminate direct instantiation of `McpStatusService()` / `McpInstallService()` in `cmd_mcp.py` and remove local imports in `cmd_ingest.py`.
- **Enforce Explicit Type Boundaries:** Replace ambiguous typing like `_as_memory_layer(mem: object)` in `cmd_memory.py` with an explicit interface defined under `ctx.services.memory`.
- **Resolve Static Internal Dependencies:** Route static internal references through provider components instead of hardcoding them (e.g., `SQLiteHelper._ensure_config()`, `_RAG_PATH` / `_SESSION_PATH` in `cmd_config.py`, and explicit logger name strings in `cmd_debug.py`).

#### Target Files
- `cmd_config.py`
- `cmd_session.py`
- `cmd_db.py`
- `cmd_mcp.py`
- `cmd_ingest.py`
- `cmd_memory.py`
- `cmd_debug.py`

#### Deliverables
- Granular error handling mapped by specific exception types.
- Injectable Service and Provider architecture.
- Strongly typed boundaries for memory, config, and debug modules.

## 3. Completion Criteria
- [ ] Subcommand parsing and usage documentation are unified via the shared parser.
- [ ] List, detail, and export views are standardized using the formatter/presenter layer.
- [ ] Broad exception catching is eliminated, dependency injection is implemented, and type boundaries are cleanly established.
