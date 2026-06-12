## Refactoring Brief

Refactor this Python codebase with **no backward compatibility**. Remove legacy entry points, compatibility wrappers, and re-export shims.

### Global rules

- Do not use `assert` in business logic; raise explicit exceptions instead.
- Do not use `except Exception`; catch only specific exceptions.
- Do not use `dict[str, Any]` outside external boundaries; convert to typed DTOs immediately after JSON/HTTP/SQLite input.
- Do not use unconditional string conversion such as `str(args.get(...))` or `str(m.get(...))`; validate input types strictly.
- Do not treat `None`, empty string, and unset as equivalent.
- Define dedicated DTOs for audit logs, execution results, approval decisions, DB stats, and context views.
- Validate all decoded LLM/JSON payloads against schema and fail fast on mismatch.
- Do not print directly from command, service, or domain logic; route all output through a CLI/UI output interface.

### `agent/commands/`

- Remove direct `print()` usage from command modules and replace it with an injected output/presenter interface. This applies to command handlers such as `cmd_config.py`, `cmd_context.py`, `cmd_db.py`, `cmd_debug.py`, `cmd_ingest.py`, `cmd_mcp.py`, `cmd_memory.py`, `cmd_notes.py`, `cmd_session.py`, and `cmd_tooling.py`.
- Replace ad-hoc string-based argument parsing with strict request DTOs and validators for subcommands, IDs, modes, language flags, paths, and numeric options. Existing handlers currently parse raw strings and often convert values loosely.
- Remove compatibility-oriented helpers and legacy command wiring. Delete the legacy entry point in `agent.py`, remove backward-compatibility re-exports in `utils.py`, and remove compatibility wrappers in `mixin_base.py`.
- Refactor `cmd_session.py` from its compressed single-line style into properly separated functions with strict DTO-based session operations.
- Move formatting and display logic out of command handlers into dedicated presenters/renderers; keep command modules focused on input parsing and service invocation. `formatter.py` should become an output adapter rather than a set of direct print helpers.
- Replace dispatcher lambdas and stringly typed command metadata with structured command definitions and handler references in `registry.py`.

### `agent/services/`

- Replace `dict`, `object`, and `tuple[bool, str]` return types with typed DTOs in service modules such as `context_view.py`, `db_maintenance_service.py`, `tool_results.py`, `session_restore.py`, and `undo_service.py`.
- Remove unconditional string conversion and raw dict access in `context_view.py`; replace direct `m.get(...)`/`str(...)` access with typed message accessors or DTO conversion.
- Replace broad exception handling in `session_title.py` and `ingest_workflow.py` with specific exception handling, and validate decoded HTTP/JSON results explicitly.
- Make MCP flows fail fast: in `mcp_install.py`, do not silently map unknown roles to `generic`; validate strictly. In `mcp_status.py`, treat unknown tier values as errors instead of permissive fallbacks.
- Separate service logic from presentation text. Service modules should return structured results, while command/presenter layers should build user-facing messages.
- Move session/state mutation helpers such as reset, restore, undo, and prompt switching into clearer application-layer services with typed result models.

### `db/`

- Refactor `maintenance.py` to remove `except Exception`, replace loose `dict` result structures with typed maintenance DTOs, and make recovery/checkpoint/purge flows explicitly typed and fail-fast.
- Refactor `store.py` so SQLite-backed implementations do not leak raw rows/dicts across internal layers; keep protocol boundaries but convert external data to typed objects immediately.
- Move retention, recovery, and deletion result structures into explicit request/response DTOs and validators instead of implicit dict-based policies.

### Priority order

1. `db/maintenance.py`
2. `agent/services/session_title.py`
3. `agent/services/context_view.py`
4. `agent/commands/cmd_db.py`
5. `agent/services/mcp_install.py`
6. `agent/services/tool_results.py`
7. `agent/commands/cmd_session.py`

### Definition of done

- No `except Exception` remains in business logic.
- No direct `print()` remains in command/service/domain logic.
- No internal loose dict/tuple result contracts remain where typed DTOs can be used.
- Legacy compatibility code is removed.
- Unknown role/tier/tool/metadata values fail fast instead of falling back silently.
