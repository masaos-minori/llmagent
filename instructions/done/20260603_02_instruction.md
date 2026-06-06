# Refactoring Instructions for Claude Code

## Overall Policy

* Remove all remaining legacy features, classes, and settings that are kept only for backward compatibility.
* Do not preserve backward-compatibility leftovers unless there is a clear, explicit requirement to keep them.
* Simplify the codebase by eliminating transitional compatibility layers.

## `agent/commands/registry.py`

* Reduce implicit dependencies between mixins.

* Do not rely on hidden cross-mixin assumptions. For example:
  * `cmd_ingest.py` currently assumes `_render_history_md()` is provided by `_ToolingMixin`.
  * `cmd_memory.py` currently accesses internal attributes of `MemoryLayer`.
  
* Do not keep `CommandRegistry` in a state where “which mixin provides which API” is only an informal convention.

* Make those contracts explicit in the type system or through explicit composition.

* Move toward an explicit architecture based on:
  * services
  * renderers
  * command objects

* Make future extraction, replacement, or recomposition safe without depending on mixin implementation details.

***

## `agent/commands/cmd_config.py`

* Split responsibilities in this module.

* Do not keep all of the following inside one mixin:
  * configuration display
  * config diff application
  * live service synchronization
  * validation-like config reconciliation logic
  
* Move `_apply_config_params()` and related logic out of the command handler layer.

* Treat this as application service logic.

* Introduce a dedicated component such as `ConfigReloadService`.

* Remove direct writes to private service attributes inside `_sync_services_to_cfg()`.

* Do not write directly to fields such as:
  * `ctx.services.llm._temperature`
  * `ctx.services.llm._max_tokens`
  * `ctx.services.hist_mgr._char_limit`
  * `ctx.services.tools._cache_ttl`
  
* This breaks encapsulation and makes regressions more likely when service internals change.

* Add explicit public setter APIs or reload/apply APIs on the service side and synchronize through those APIs only.

* Refactor `_apply_mcp_url_reload()`.

* Do not hardcode the operational rule that “transport changes require restart” as an implicit limitation in command-layer code.

* Explicitly classify reload results into categories such as:
  * changes that require restart
  * changes that can be applied immediately
  * changes that cannot be applied

* Return the reload result as a structured report.

***

## `agent/commands/cmd_mcp.py`

* Split this module by concern.

* Do not keep all of the following together:
  * status probing
  * interactive wizard flow
  * template/scaffold generation
  * post-install instructions rendering

* In particular, refactor `/mcp install`.

* The UI prompt flow and scaffold-generation logic are too tightly coupled.

* Separate them into:
  * interaction layer
  * service layer for server generation
  * renderer layer for display/output
  
* Remove direct reliance on `input()` and `asyncio.to_thread(input, ...)` inside `_cmd_mcp_install()`.

* Do not hardcode the CLI interaction model into the command implementation.

* Introduce an abstract question/answer interface so the feature can work in:
  * non-interactive mode
  * automation
  * alternate frontends
  
* Refactor `_cmd_mcp_status()`.

* Do not infer write capability only from `cfg.tool_names` plus a simple write-capable tool set.

* Align status reporting with the actual tool safety policy model, including classes such as:
  * dangerous
  * write-safe
  * admin

* Ensure observable status output cannot drift from the real approval policy.

***

## `agent/commands/cmd_context.py`

* Split this module by concern.

* Do not keep all of the following in one command group:
  * conversation state display
  * history editing
  * system prompt switching
  * database maintenance/admin operations
  
* Separate:
  * context/history commands
  * database administration commands

* Refactor `_cmd_undo()`.

* It currently rolls back in-memory history from the last user-message boundary while delegating DB rollback to `ctx.session.delete_last_turn()`.

* Do not rely on this loose coupling between memory-side rollback and DB-side rollback.

* Introduce a consistent undo API based on a logical turn unit.

* This API must remain correct even when:
  * tool messages are present
  * system injections have occurred
  * the stored turn structure is more complex than `user + assistant`
  
* Refactor `_cmd_system()`.

* Do not directly rewrite the system prompt as `ctx.history[0]` or inject a `system` message at the front of history as the primary state model.

* The current design mixes:
  * the true system prompt
  * memory injection messages
  * compression summary messages
    under the same `role="system"` representation.

* This makes the assumption “the first system message is the actual system prompt” fragile.

* Store the system prompt in dedicated state.

* Project it into history only at render/build time.

* Refactor `/db` commands.

* Do not expose `SQLiteHelper` and `db.maintenance` directly from `CommandRegistry`.

* Introduce a DB administration service that centralizes:
  * permission boundaries
  * dry-run support
  * structured result reporting
  
***

## `agent/commands/cmd_ingest.py`

* Refactor `_cmd_compact()`.

* Do not force compression by temporarily setting `ctx.services.hist_mgr._char_limit = 0`.

* This directly depends on a private implementation detail.

* Add a public API such as `HistoryManager.force_compress()`.

* Do not let external callers mutate internal state just to force behavior.

* Split `_cmd_ingest()` by concern.

* It currently handles both:
  * crawl/split/ingest orchestration
  * CLI output/rendering

* Separate the ingest workflow service from the CLI command layer.

* Return structured stage-aware failures from the ingest workflow.

* Make it explicit which stage failed:
  * crawl
  * split
  * ingest

* Refactor `_cmd_export()`.

* Do not keep all of the following in a single function:
  * format selection
  * rendering
  * stdout emission
  * file writing

* Separate renderer and writer responsibilities so future export targets and formats can grow without making the command handler monolithic.

***

## `agent/commands/cmd_rag.py`

* Rename and split this module.

* The current filename is `cmd_rag.py`, but its responsibilities include:
  * tool result inspection
  * notes
  * plan mode
  * debug handling
  * export rendering

* These are not RAG-specific concerns.

* Align file names with actual responsibilities.

* Consider splitting into modules such as:
  * `cmd_tooling.py`
  * `cmd_notes.py`
  * `cmd_debug.py`

* Refactor `_cmd_debug()`.

* Do not keep the following in one command handler:
  * audit log tail display
  * logger level switching
  * debug mode toggle

* The boundary between observability functions and UI/debug convenience features is currently unclear.

* Split these into separate commands or separate services.

* Refactor `_tool_show()` and `_tool_list()`.

* Do not tightly couple tool result store access with presentation formatting.

* Separate renderer responsibilities now so that future support for:
  * large result rendering
  * JSON output
  * alternative display backends
    remains straightforward.

***

## `agent/commands/cmd_memory.py`

* Remove direct dependence on `MemoryLayer` internals.

* Do not access private attributes such as:
  * `layer._store.search_by_type()`
  * `layer._retriever.search()`
  * `layer._store.get_by_id()`
  * `layer._store.pin()`

* `MemoryLayer` must act as a proper façade.

* Add explicit public APIs on `MemoryLayer` and route all command-layer operations through those APIs.

* Refactor `_memory_prune()`.

* Do not call `SQLiteHelper("session")` and `db.maintenance.prune_old_memories()` directly from the command layer.

* This spreads consistency responsibilities across:
  * the JSONL source of truth
  * the SQLite secondary store
  * in-memory statistics/state

* Unify pruning behind a public memory service API.

* Unify permission, consistency, and result contracts across `/memory` commands.

* Right now, display, search, delete, and pin operations are handled inconsistently.

* In particular, `delete`, `prune`, and `pin` are state-changing operations.

* Standardize the following across them:
  * audit logging
  * dry-run support
  * result types / structured outcomes

* The current combination of `print()` and partial `logger.info()` is too weak as an operation audit trail.

***

## `agent/commands/cmd_session.py`

* Remove hidden title-generation policy from module-level constants.

* Do not keep `_TITLE_TEMPERATURE = 0.1` and `_TITLE_MAX_TOKENS = 20` as fixed internal constants without configuration support.

* Title generation is user-visible behavior and should not be governed by hidden LLM policy.

* Move these settings into:
  * dedicated config, or
  * a dedicated title generation service

* Formalize session lifecycle as an explicit service contract.

* Keeping restore/delete/load inside one mixin is acceptable, but consistency across the following is critical:
  * history restoration
  * system prompt restoration
  * memory injection interaction
  * statistics reset behavior

* Make session lifecycle semantics explicit rather than relying on scattered command behavior.

***

## General Refactoring Rules

* Keep command handlers thin.
* Move application logic into services.
* Move formatting into renderers.
* Do not let commands mutate private service state.
* Prefer explicit APIs, explicit contracts, and typed result models.
* Avoid hidden cross-mixin dependencies and avoid relying on implementation details of other modules.
* When a command changes persistent or session state, ensure:
  * consistent auditing
  * structured result reporting
  * well-defined rollback or compensation behavior where relevant.

