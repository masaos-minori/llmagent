# Refactoring Plan

## Overall Policy
- Do not preserve backward compatibility. Remove compatibility entry points, re-exports, fallbacks, and continuation-oriented recovery logic.
- Do not use `assert` in business logic. Raise explicit exceptions for precondition violations.
- Do not use `except Exception`. Catch only specific exception types.
- Do not use `dict[str, Any]` outside external boundaries. Convert external input through DTOs and validators, and maintain strict typing internally.
- Do not use unconditional string conversion such as `str(args.get(...))` or `str(msg.get(...))`. Validate input types and fail if the value is not of the expected type.
- Do not treat `None`, empty strings, and unset values as equivalent.
- For LLM / HTTP / JSON / SQLite rows, perform schema validation and type conversion immediately after decoding or retrieval.
- Do not output directly via `print()`. Route all output through a UI/CLI output interface.
- For unknown tool names, unknown tiers, and unknown metadata, use fail-fast behavior instead of fail-open behavior.

## Implementation Rules

### Mandatory Rules
- Unify the public APIs of the command, service, and memory layers around request DTOs and result DTOs.
- Refactor the code so that it does not depend excessively on string-based subcommand names, handler names, stage names, tier names, or role names.
- Do not collapse exceptions into `0`, `-1`, `None`, `[]`, or `success=False`. Replace them with specific exceptions or dedicated result types.
- Do not keep the formatter as a simple print helper. Treat it as a UI/CLI output adapter.
- Restrict command handlers to input interpretation and service invocation. Move formatting and detailed state mutation into services, presenters, or adapters.

### Common Elements to Add or Reorganize
- Add the following under `agent/shared/models.py` or another appropriate layer:
  - `CommandResult`
  - `ValidationErrorDetail`
  - `ConfigReloadRequest`
  - `ConfigReloadResult`
  - `ConversationCommandResult`
  - `IngestRequest`
  - `IngestResult`
  - `McpInstallRequest`
  - `McpServerStatus`
  - memory-related DTOs
- Add the following under `agent/shared/enums.py`:
  - `CommandName`
  - `ExtractionDecision`
  - `RetrievalMode`
  - `ToolSafetyTier`
  - `McpRole`
  - `WorkflowStage`
- Add the following under `agent/shared/exceptions.py`:
  - `ValidationError`
  - `ConfigurationSchemaError`
  - `WorkflowStageError`
  - `UnknownTierError`
  - `UnknownRoleError`
  - memory-related exceptions

## File-by-File Changes

### `agent.py`
- Remove the backward-compatibility-only entry point. The file explicitly states that it exists only for backward compatibility and preserves the legacy startup path via `sys.path.insert(...)`. This conflicts with the no-backward-compatibility policy.

### `agent/commands/formatter.py`
- Eliminate direct `print()` calls such as `print_success()`, `print_error()`, `print_table()`, and `print_kv_list()`, and replace them with a UI/CLI output interface.
- Redesign the formatter as a presenter or output adapter rather than a simple print helper.

### `agent/commands/registry.py`
- Replace string-based handler references such as `"_cmd_memory"` with type-safe handler references.
- Convert prefix/exact-match logic and subcommand metadata into enums or DTOs, and reduce the stringly-typed dispatcher structure.

### `agent/commands/utils.py`
- Remove backward-compatibility re-exports (`render_export`, `render_history_md`, `write_export`) and unify all callers on the new import paths.
- Replace ambiguous `None` returns from `parse_flag_int()` and `parse_flag_str()` with explicit parse result DTOs or validation errors.

### `agent/commands/cmd_context.py`
- Eliminate direct `print()` calls from command handlers.
- Replace dict-based state access and history processing that depends on `msg.get("content")` with DTO-based structures.
- Change `_cmd_clear`, `_cmd_undo`, `_cmd_history`, and `_cmd_system` to return dedicated result DTOs instead of human-readable strings.

### `agent/commands/cmd_db.py`
- Eliminate direct `print()` calls.
- Replace loose parsing such as `lang: str | None = str(lang_raw) if ...` and `isdigit()`-based interpretation with strict request DTOs and validators.
- Convert dict-based service results such as `DbMaintenanceService().stats()` accessed via keys like `result['docs']` into DTOs.
- Replace lambda-based dispatch with a structured dispatcher.

### `agent/commands/cmd_memory.py`
- Eliminate direct `print()` calls from all command handlers.
- Replace lambda-based dispatch such as `dispatch = {"list": lambda: ...}` with structured command definitions.
- Remove implicit fallback logic such as `summary or e.content[:60]` and manage summary/snippet sources through DTOs.
- Convert the inputs for list/search/show/pin/unpin/delete/prune into request DTOs.
- Split `MemoryOpResult` into monitoring/audit DTOs and UI-facing DTOs.

### `agent/commands/cmd_mcp.py`
- Replace direct `print()` calls used for next-step output and status tables with the output interface.
- Convert install/status results into presenter-facing DTOs so that the command layer has minimal display responsibility.

### `agent/services/config_reload.py`
- Replace `apply_config_dict(self, new_cfg: dict[str, Any])` with a strict `ConfigReloadRequest` DTO.
- Remove unconditional conversions using `int(...)`, `float(...)`, `bool(...)`, `list(...)`, and `dict(...)`, and introduce schema validation.
- Separate config update logic into category-specific adapters and validators.
- Expand `needs_restart`, `applied`, and `skipped` into result DTOs that contain enums or typed items.

### `agent/services/conversation_service.py`
- Replace human-readable string return values with structured results such as `ConversationCommandResult`.
- Replace dict-style history operations such as `ctx.conv.history[0]["role"]` and `ctx.conv.history[0]["content"]` with typed history DTOs.
- Return audit log information for clear/system-prompt switching as dedicated DTOs.

### `agent/services/ingest_workflow.py`
- Replace `except Exception` in crawl/split/ingest stages with specific exception handling.
- Convert string stage values in `IngestResult.stage` (`"ok"`, `"crawl"`, `"split"`, `"ingest"`) into an enum.
- Replace `result.error: str | None` with typed error details.
- Reorganize the workflow around request DTOs, result DTOs, and stage-specific exceptions.

### `agent/services/mcp_install.py`
- Change `CliInstallQA.ask_role()` so that unknown roles fail fast instead of falling back to `"generic"`.
- Consolidate `port`, `role`, and `with_confd` into an `McpInstallRequest` DTO.

### `agent/services/mcp_status.py`
- Replace `_TIER_PRIORITY` and `_TIER_LABEL`, which depend on raw string tiers, with a `ToolSafetyTier` enum.
- Convert `McpServerStatus` fields such as availability, health, write, and role into enums, and make unknown tier/role values fail fast.

### `agent/memory/types.py`
- Finalize strict definitions for `MemoryEntry`, `MemoryQuery`, `MemoryHit`, `EmbeddingResult`, `SourceType`, and `EmbeddingErrorKind`.
- Reorganize memory type handling into enums and immutable DTO structures rather than relying only on constant sets.
- Separate parsers, validators, and factories from `types.py`.

### `agent/memory/embedding_client.py`
- Remove direct access via `resp.json().get("embedding")` and introduce DTO-based parsing plus schema validation.
- Remove `except Exception` from `_fetch_embedding()` and split errors into HTTP, transport, JSON, and schema exceptions.
- Rework the structure that collapses failures into `success=False`.
- Extract retry and circuit-breaker logic into independent components.

### `agent/memory/jsonl_store.py`
- Remove `read_all(strict=False)` and quarantine-based continuation logic. Fail immediately on malformed JSONL.
- Replace `_entry_from_dict(d: dict)` with `JsonlRecord` DTO parsing and validation.
- Remove the default-value fallback in `memory_type = d.get("memory_type", "")`.
- Replace `asdict(entry)` serialization with an explicit serializer.

### `agent/memory/mapper.py`
- Remove support for `sqlite3.Row | dict[str, Any]` and accept only validated row DTOs.
- Remove implicit completion via `.get(..., default)`.
- Prohibit unconditional `float(...)` and `bool(...)` conversions.
- Separate the SQLite row mapper from the JSONL mapper.

### `agent/memory/retriever.py`
- Do not absorb timestamp parse failures in `_recency_boost()` as `0.0`. Treat them as schema errors.
- Convert retrieval requests, hit results, and merge results into DTOs and reduce dependence on helper dictionaries.
- Separate query building, scoring, merging, and storage access.

### `agent/memory/extract.py`
- Remove dependency on `shared.types.LLMMessage` and replace it with memory-specific message DTOs.
- Eliminate `msg.get("content")` and unconditional string conversion such as `str(content_raw)`.
- Replace `MemoryEntry | None` extraction outcomes with `ExtractionDecision` or `ExtractionCandidate` DTOs.
- Separate semantic/episodic rule evaluation into evaluators.

### `agent/memory/ingestion.py`
- Remove `except Exception` from `_link_duplicates()`.
- Split `on_session_stop()` into extract / dedup / persist / link stages, and define DTO and exception contracts for each stage.
- Move fixed importance values into policy or config DTOs.

### `agent/memory/injection.py`
- Reject empty queries through request validation instead of silently returning `[]`.
- Do not continue with `embedding=None` after embedding failure. Return an exception or an explicit result type instead.
- Remove implicit fallback logic such as `summary or content[:100]` and manage snippet sources through DTOs.
- Make `InjectionPolicy` an immutable DTO.

### `agent/memory/services.py`
- Remove dependency on `shared.types.LLMMessage` and replace it with memory-specific history DTOs.
- Unify the facade public API around request/result DTOs.
- Restrict the facade to orchestration responsibilities and move type-conversion responsibilities into adapters.

## Work Steps
1. Identify and remove backward-compatibility targets first (`agent.py`, `agent/commands/utils.py`, etc.).
2. Redesign the output layer by turning `formatter.py` into an output adapter and eliminating direct `print()` from the command layer.
3. Replace the command registry/dispatcher with structured command definitions.
4. Migrate config, conversation, ingest, and MCP services to DTOs, enums, and specific exceptions.
5. Refactor the memory layer (`types`, `mapper`, `jsonl`, `embedding`, `extract`, `ingestion`, `injection`, `retriever`, `services`) for strict typing and fail-fast behavior.
6. Reduce stringly-typed dependencies on handler names, state names, and result names in the command layer.
7. Update callers to follow the new DTO/enum/exception contracts.
8. Update tests and static checks.

## Definition of Done
- Backward-compatibility-only code (legacy entry points, re-exports, permissive fallbacks) has been removed.
- Direct `print()` calls have been removed from the command, service, and memory layers.
- `except Exception` has been removed from all target files.
- `dict[str, Any]` has been removed from all internal code outside external boundaries.
- Implicit completion using `.get(..., default)` has been removed from the internal memory layer.
- Loose conversions such as `str(msg.get(...))` and unconditional `int()/float()/bool()/list()/dict()` have been replaced with schema validation and validators.
- Unknown roles, unknown tiers, and unknown metadata are handled with fail-fast behavior.
- JSONL, embedding responses, history messages, reload config input, and workflow stages are validated immediately after decode or parse.
- `mypy --strict`, `ruff check`, and `pytest` all pass.
