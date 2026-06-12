# Refactoring Instructions for Claude Code

## Overall Policy

* Remove all remaining features, classes, and settings that exist only to preserve backward compatibility.
* Do not keep legacy compatibility layers unless there is an explicit and current requirement to retain them.
* Simplify the codebase by eliminating transitional behavior and duplicated compatibility paths.

***

## `shared/tool_executor.py`

* Split `tool_executor.py` by responsibility.

* Do not keep all of the following in a single module or class:
  * routing
  * transport execution
  * TTL caching
  * plugin bypass
  * lifecycle integration
  * error formatting

* Refactor the module into separate units such as:
  * routing
  * transport
  * cache
  * plugin integration
  * error model

* The current design makes change impact too broad.

* Make it easier to add new transports or change caching policy without modifying a monolithic execution layer.

* Refactor `is_side_effect()`.

* Do not keep side-effect detection as a fixed set:
  * `WRITE_TOOLS | DELETE_TOOLS | {"shell_run"}`

* Tool safety is currently split across:
  * `tool_constants.py`
  * agent-side approval policy

* This creates a risk of duplicated or drifting definitions.

* Move side-effect classification into a shared safety model.

* Refactor `format_transport_error()`.

* Do not keep separate representation policies for:
  * tool transport errors
  * LLM transport errors

* Promote the error taxonomy into shared structured types.

* Unify error handling around explicit fields such as:
  * `retryable`
  * `partial`
  * `source`
  * `phase`

***

## `shared/llm_client.py`

* Split responsibilities in `llm_client.py`.

* Do not keep all of the following inside `LLMClient`:
  * HTTP retry policy
  * SSE parsing
  * heartbeat monitoring
  * malformed frame retry
  * reconnect-aware streaming
  * stat counters

* Separate:
  * transport
  * parser
  * retry policy
  * metrics

* Refactor `LLMErrorKind`.

* Do not keep error taxonomy only as a `Literal` string enumeration without a clear programmatic contract.

* Promote the error taxonomy into:
  * explicit types
  * explicit result/error models

* Separate the responsibilities of:
  * retry logic
  * reconnect logic
  * UI-facing error presentation

* Clarify metric scope.

* Instance-lifetime counters are convenient, but observability becomes ambiguous if the boundary between:
  * per-turn
  * per-request
  * per-instance lifetime
    is not explicit.

* Define and document metric scopes clearly.

***

## `shared/mcp_config.py`

* Strengthen typed config in `mcp_config.py`.

* Clean up legacy fallback behavior.

* Refactor `McpServerConfig`.

* Do not leave key transport/lifecycle fields loosely typed as generic strings and integers only.

* Convert at least the following fields to enums:
  * `transport`
  * `startup_mode`
  * `healthcheck_mode`

* Make configuration errors easier to detect and reason about.

* Refactor `_build_mcp_servers()`.

* It currently accepts both:
  * the current `mcp_servers` section
  * legacy URL constants

* This preserves compatibility, but it duplicates configuration paths.

* Separate:
  * explicit backward-compatibility mode
  * the new canonical configuration path

* Treat the deprecated path as temporary and remove it early.

* Reduce dependence on multiple routing sources of truth.

* `tool_names`-based config-driven routing and static fallback in `route_resolver.py` currently coexist.

* Config-first routing is the correct direction, but fallback makes drift easier to tolerate silently.

* Move toward a config-first routing model with an explicit migration plan.

***

## `shared/route_resolver.py`

* Reduce fallback dependence in `route_resolver.py`.

* Introduce:
  * strict mode
  * warning mode

* The resolver is clear, but the two-layer structure:
  * config map
  * static fallback
    can create silent drift.

* Do not allow new tools to route successfully through fallback when they were never explicitly registered in config.

* In strict mode:
  * forbid fallback entirely

* In warning mode:
  * emit warnings or audit events whenever fallback is used

* Refactor routing policy.

* Do not couple routing policy too tightly to `tool_constants.py`.

* Static fallback currently depends heavily on those frozensets.

* Move routing toward:
  * role-based routing
  * capability-based routing

***

## `shared/tool_constants.py`

* Keep centralized tool metadata, but refactor the representation model.

* Do not express multiple axes of tool taxonomy only as separate frozenset groups.

* The current sets mix multiple concerns such as:
  * capability
  * risk
  * backend

* As the number of tools grows, this makes set consistency and classification drift harder to control.

* Replace this with a single metadata model such as `ToolSpec`.

***

## `shared/plugin_registry.py`

* Reconsider the registry design.

* The current module-level global state plus import-time side effects is easy to understand, but it makes the following difficult:
  * multiple registry instances
  * plugin namespace separation

* Consider refactoring toward a plugin manager object.

* Refactor `load_plugins()`.

* It currently fails open by logging and skipping errors, but the result is not machine-readable.

* Return a structured report that clearly states:
  * which plugins were loaded
  * which plugins failed
  * why they failed

***

## `shared/logger.py`

* Migrate `logger.py` to task-local context management.

* `Logger` is convenient as a wrapper, but behavior is implicit when multiple instances are created with the same logger name.

* Duplicate handlers are avoided, but filters are still added repeatedly.

* The overwrite rules for context fields are not explicit.

* Separate:
  * logger factory responsibilities
  * logger context management responsibilities

* Refactor `_ContextFilter`.

* Do not keep mutable context fields inside a shared filter object.

* This design is weak under:
  * concurrent tasks
  * multiple simultaneous turns

* Migrate to thread/task-local context based on `contextvars`.

***

## `shared/config_loader.py`

* `ConfigLoader` itself is simple, but many callers still implement ad hoc load/cache logic at the module level.

* As a result, configuration consistency is not truly shared across the system.

* Unify the following as shared infrastructure:
  * configuration loading
  * cache policy
  * reload policy

***

## `shared/types.py`

* Make `LLMMessage` and tool call types stricter.

* `LLMMessage.role` is documented as:
  * `"user" | "assistant" | "tool" | "system"`
    but the actual type is only `str`.

* Do not leave invalid roles unchecked at the type level.

* Tighten this with:
  * `Literal`
  * or `Enum`

* Tool-call fields such as `tool_calls: list[dict]` are too weakly typed for an OpenAI-compatible message schema.

* Introduce shared tool call structures so transport, executor, and orchestrator layers can rely on consistent types safely.

***

## `shared/otel_tracer.py`

* The private-provider design is useful for avoiding test pollution, but lifecycle behavior is not explicit enough when multiple tracer instances coexist.

* Make tracer lifecycle explicit in the service layer.

* Clarify:
  * exporter/processor cost model
  * ownership
  * shutdown behavior

***

## `shared/token_counter.py`

* Remove the module-global effect of `_warned_unavailable`.

* Warning suppression should not exist at process scope.

* The current design makes behavior ambiguous across:
  * multiple agents
  * test runs
  * multiple client instances

* Move warning suppression to:
  * caller scope
  * or instance scope

***

## `shared/formatters.py`

* `formatters.py` is a reasonable shared utility module, but it currently mixes:
  * formatters for LLM context
  * formatters for terminal output

* Separate formatter boundaries by usage.

* This will make policy differences easier to manage.

* Refactor logging format policy.

* `fmt_kvlog()` produces string-based key=value logs, while `logger.py` also supports JSON formatting.

* Do not keep both string-based kvlog and JSON logging as parallel patterns without a unified policy.

* Standardize structured logging strategy.

***

## `shared/git_helper.py`

* Do not swallow all exceptions with `except Exception` and return `None`.

* The current behavior collapses very different conditions into the same result, including:
  * environment problems
  * permission issues
  * GitPython not installed
  * path outside a repository

* From the caller’s perspective, everything becomes just “unavailable.”

* Return a reason-coded result instead.

***

## General Implementation Rules

* Remove backward-compatibility leftovers aggressively.
* Prefer explicit contracts over implicit fallback behavior.
* Prefer typed metadata models over parallel frozenset classifications.
* Prefer task-local or instance-local state over mutable module-global state.
* Prefer structured reports over silent skip/fallback behavior.
* Keep routing, safety, transport, logging, metrics, and plugin lifecycle boundaries explicit.

