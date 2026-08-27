## Goal

Remove the stale `cache_ttl`/cache-lookup/`clear_cache()` description from
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`'s
`ToolExecutor` section, and correct the now-inaccurate `is_side_effect()` purpose
statement (REQ-001), per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the "## 4. `ToolExecutor`" section's first paragraph (verified at
  line 7 as of 2026-08-27) and its `is_side_effect()` helper-function sentence
  (same section).
- Out of scope: "## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation`"
  (still accurate).

## Assumptions

- `ToolExecutor`'s constructor no longer accepts `cache_ttl`; `execute()` no
  longer does a cache lookup, concurrency protection (stampede), or "caching
  successful results" step; `clear_cache()` no longer exists — re-verified
  2026-08-27 against `scripts/shared/tool_executor.py`'s actual `__init__`/
  `execute()`/`_raw_execute()` implementation.
- **Same `is_side_effect()` staleness found in this Plan's other target files**
  (`docs/04_mcp_03_02_tool-registry.md`, `docs/90_shared_03_03_...`): this file's
  sentence also claims `is_side_effect()` is "used solely within this module for
  determining TTL cache bypass" — false now that `execute()` no longer calls it.

## Design decisions

- Rewrite the constructor/`execute()` description to match the actual current
  sequence: `ToolExecutor` inherits from `ToolTransportInvoker`, accepts an HTTP
  client, `server_configs`, and optional `concurrency_limits`/`lifecycle`
  parameters (no `cache_ttl`). `execute()` calls `_raw_execute()`, which resolves
  the server key, runs the startup-mode/health gate chain, ensures lifecycle
  readiness, resolves the transport, and dispatches via a per-server semaphore.
  Remove `apply_config()`/`clear_cache()` references (both removed from
  `ToolExecutor`).
- Rewrite the `is_side_effect()` sentence to state its actual current caller
  (`agent/tool_scheduler.py`), matching the correction already made to
  `docs/04_mcp_03_02_tool-registry.md` and `docs/90_shared_03_03_...` in this
  same pass.

## Alternatives considered

- N/A: narrow, targeted rewrite matching the corrected behavior already applied
  consistently across this Plan's other 13 target files.

## Implementation
### Target file
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at line 7
   as of 2026-08-27; re-read the full "## 4. `ToolExecutor`" section since it may
   span more lines than the single line captured at Plan-authoring time).
2. Rewrite the constructor/`execute()` description.
3. Rewrite the `is_side_effect()` sentence.
4. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edit (Edit tool) — rewrite one paragraph.

### Details
Current text (verified 2026-08-27, line 7): `` `ToolExecutor` inherits from
`ToolTransportInvoker` and accepts an HTTP client, `cache_ttl`, `server_configs`,
and optional parameters via its constructor. `apply_config()` enables
hot-reloading. The `execute()` method follows this sequence: cache lookup →
concurrency protection → health check gate → transport resolution →
per-server semaphore execution → caching successful results. `clear_cache()` and
`get_error_counters()` manage state. Failures are not cached. ``

Replace with: `` `ToolExecutor` inherits from `ToolTransportInvoker` and accepts
an HTTP client, `server_configs`, and optional `concurrency_limits`/`lifecycle`
parameters via its constructor (no `cache_ttl` — `ToolExecutor` has no internal
cache). The `execute()` method calls `_raw_execute()` directly: resolve
`tool_name` → `server_key`, run the startup-mode/health gate chain, ensure
lifecycle readiness, resolve the transport, then dispatch via a per-server
semaphore. `get_error_counters()` manages error-count state. ``

Rewrite the sentence beginning "Helper functions: `is_side_effect()` identifies
tools ... (used solely within this module for determining TTL cache bypass)" to
state that `is_side_effect()` no longer has a caller in this module — `execute()`
dispatches every tool through the same path — and that its current use is
`agent/tool_scheduler.py`'s unrelated serial-execution-batching decision (already
described later in the same sentence as "a separate path from
`is_side_effect()`" — keep that clause, only correct the now-false "used solely
... for TTL cache bypass" framing).

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Text revert via `git diff`/`git checkout -- <path>`; independent of the other
  13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | Manual diff | `git diff <path>` | No `cache_ttl`/cache-lookup/`clear_cache()` claim remains; `is_side_effect()` purpose corrected |
| `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "cache_ttl|clear_cache|cache lookup" docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
  returns no matches.
- `is_side_effect()`'s described purpose matches its actual current caller.

## Out of scope

- "## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation`".

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current section content | Pending | — | — | |
| 2 | Rewrite constructor/`execute()` description | Pending | — | — | |
| 3 | Rewrite `is_side_effect()` sentence | Pending | — | — | |
| 4 | Run `check_docs_consistency.py` (correct domain) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
