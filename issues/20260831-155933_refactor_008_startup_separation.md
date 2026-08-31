# Refactor startup.py — separation of concerns

## Priority
Medium

## Summary
Split `scripts/agent/startup.py`'s `StartupOrchestrator` class (670 lines) into focused modules to separate its eight combined concerns — DI wiring, workflow preflight checks, MCP subprocess startup, post-startup health verification, the service-validation pipeline, readiness reporting, approval recovery, and system-prompt/memory setup.

## Background
The module docstring states this file was "Extracted from agent/repl.py so that AgentREPL contains only input loop, command dispatch, and output display logic." After that extraction, `StartupOrchestrator` accumulated the full startup sequence (component init through MCP server spawning, health checks, security audit, tool discovery, and prompt setup) in one class rather than being split further. Similar splits were already completed for `scripts/agent/orchestrator.py`, `scripts/agent/repl.py`, and `scripts/rag/ingestion/ingester.py`, and are pending for `scripts/agent/repl_health.py` (this session's `refactor_004`) and `scripts/agent/http_lifecycle.py` (`refactor_007`) — both of which `startup.py` calls into directly.

## Problem
`StartupOrchestrator` exceeds the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition (670 lines) and combines at least eight distinct concerns:

1. **DI wiring / component init** — `_initialize`, `_init_command_registry`, `_init_orchestrator` — readline setup, `build_agent_context`, `CommandRegistry`/`Orchestrator` construction.
2. **Workflow preflight checks** — `_check_workflow_definition`, `_check_workflow_schema` — validate the workflow definition file and DB schema exist before `Orchestrator.__init__()` runs.
3. **MCP subprocess startup** — `_start_servers`, `_start_http_subprocess_once`, `_interruptible_sleep` — per-server stagger delay, retry-once-with-delay logic, and shutdown-event racing.
4. **Post-startup health verification** — `_verify_mcp_health` — a second, separate retry-once-with-delay health-poll loop against each HTTP subprocess server's `/health` endpoint.
5. **Service validation pipeline** — `_check_services` (~90 lines) — runs security audit, service readiness, MCP tool discovery, routing drift, routing safety tiers, and RAG consistency checks in sequence, accumulating results into a `StartupValidationResult`.
6. **Readiness reporting** — `_display_pipeline_results`, `_report_readiness` (~140 lines combined) — formats and displays the validation pipeline's outcomes; `_report_readiness` alone repeats the same "sum matching outcomes by source and status" pattern five times (for `security_audit`, `readiness`, `mcp_tool_discovery`, `rag_consistency`, plus per-status breakdowns), a strong duplication signal.
7. **Approval recovery** — `_recover_pending_approvals` — restores workflow approval-pending state from a previous session.
8. **System prompt / memory setup** — `_setup_prompt`, `_classify_memory_failure` — injects semantic memory snippets into the initial system prompt with failure classification.

The MCP subprocess startup logic (concern 3) and the post-startup health check (concern 4) independently implement near-identical retry-once-with-delay patterns against the same kind of `/health` endpoint, which is itself worth resolving during the split rather than carrying the duplication into new modules.

## Reason for Change
- `_check_services()` and `_report_readiness()` together account for roughly a third of the file and mix five independent validation concerns (security, readiness, tool discovery, routing, RAG) with formatting/aggregation logic that has to change every time a new validation source is added.
- `_report_readiness()`'s repeated per-source/per-status counting pattern is a maintenance risk: adding a new validation source requires copy-pasting four `sum()` blocks rather than calling a shared helper.
- MCP subprocess startup and post-startup health verification duplicate retry-with-delay logic in two different methods, doubling the surface area for a future bug fix in that pattern.
- Approval recovery and memory/prompt setup are functionally unrelated to server startup and health checking, but changes to either currently require reviewing the same 670-line file.

## Implementation Intent
Extract the concerns above into separate modules/classes, following the constructor-injection / delegation pattern already used for the `orchestrator.py` and `ingester.py` splits. Suggested (not mandatory) grouping, left for the implementation planning phase to finalize:
- **Component initializer** — owns `_initialize`, `_init_command_registry`, `_init_orchestrator`, `_check_workflow_definition`, `_check_workflow_schema`.
- **MCP server starter** — owns `_start_servers`, `_start_http_subprocess_once`, `_verify_mcp_health`, `_interruptible_sleep` — consider factoring the shared retry-once-with-delay pattern into one reusable helper used by both startup and post-startup health verification.
- **Startup validation pipeline** — owns `_check_services`, delegating each of its five checks to the existing services it already calls (`audit_security_defaults`, `check_readiness`, `McpToolDiscoveryService`, `check_routing_drift`, `check_routing_safety_tiers`, `RagMaintenanceService`).
- **Readiness reporter** — owns `_display_pipeline_results`, `_report_readiness` — replace the repeated per-source counting with a shared helper that takes a source name and returns its OK/FATAL/WARNING/SKIPPED counts.
- **Approval recovery** — owns `_recover_pending_approvals`.
- **Prompt/memory setup** — owns `_setup_prompt`, `_classify_memory_failure`.

`StartupOrchestrator.run()` should remain (or become) a thin sequencer calling into these components in the same order as today, preserving its public return contract (`tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]`) and its rollback-on-failure behavior (`shutdown_all()` on any startup exception).

## Target Files or Areas
- `scripts/agent/startup.py` — primary target
- `scripts/agent/repl.py` — consumer of `StartupOrchestrator`; must continue to work unmodified
- `scripts/agent/repl_health.py` — referenced (`audit_security_defaults`, `check_readiness`, `check_routing_drift`, `check_routing_safety_tiers`, `check_workflow_definition`, `check_workflow_schema`); not modified by this issue (see `refactor_004`)
- `scripts/agent/factory.py` — referenced by `build_agent_context`, `init_tracer`
- `scripts/agent/orchestrator.py` — referenced by `Orchestrator`
- `scripts/agent/services/mcp_tool_discovery.py`, `services/rag_maintenance_service.py` — referenced dependencies, not modified
- `scripts/agent/shared/health_models.py` — referenced by `StartupCheckStatus`, `StartupValidationResult`
- `scripts/agent/workflow/approval_ops.py`, `workflow/state_store.py` — referenced dependencies, not modified
- `tests/agent/test_startup.py`, `test_startup_routing_drift.py`, `test_startup_consistency.py`, `tests/agent/shared/test_startup_validation_pipeline.py` — to be reorganized alongside the split
- Documentation: `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` is the likely candidate — confirm against `docs/00_index.md`'s task-scope mapping before editing

## Required Changes
- Extract the six groupings listed under Implementation Intent into separate modules/classes.
- Factor the duplicated retry-once-with-delay pattern in `_start_servers`/`_start_http_subprocess_once` and `_verify_mcp_health` into one shared helper.
- Replace `_report_readiness()`'s five repeated per-source counting blocks with a shared helper parameterized by source name.
- Reduce `StartupOrchestrator` to a thin sequencer wiring these components together in `run()`.
- Preserve `StartupOrchestrator.__init__(ctx, view, shutdown_event)` and `run() -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]` exactly, including the rollback-on-failure `shutdown_all()` behavior in `run()`'s exception handler.

## Constraints
- Do not change the startup sequence's order (`_initialize` → `_start_servers` → `_verify_mcp_health` → `_check_services` → `_recover_pending_approvals` → `_setup_prompt`).
- Do not change any fatal-vs-warning classification behavior (e.g. production-profile MCP subprocess start failures raising `RuntimeError`, non-production failures only warning).
- Do not change the `StartupInterrupted` exception's raise conditions or the `shutdown_event`-racing behavior in any of the interruptible-sleep call sites.
- Do not change any existing log message string or the `_view.write_*` output text shown to the user.
- `agent/repl.py`'s existing use of `StartupOrchestrator` must continue to work without modification.

## Acceptance Criteria
- Each resulting module/class addresses exactly one of the six groupings listed under Implementation Intent.
- The duplicated retry-once-with-delay logic in MCP subprocess startup and post-startup health verification is consolidated into one shared implementation.
- `_report_readiness()`'s per-source counting is expressed via one shared helper rather than five repeated blocks.
- `StartupOrchestrator.__init__` and `run()` retain their exact signatures, return types, and exception/rollback behavior.
- `scripts/agent/repl.py`'s usage of `StartupOrchestrator` continues to work unmodified.
- All pre-existing tests in the four affected test files pass unchanged in outcome (reorganized as needed).
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files.
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Run `test_startup.py`, `test_startup_routing_drift.py`, `test_startup_consistency.py`, and `tests/agent/shared/test_startup_validation_pipeline.py` (reorganized to match the new module layout) and confirm no behavioral regression.
- Add or confirm a test for the consolidated retry-once-with-delay helper covering: success on first attempt, success on retry, failure on both attempts (production profile raises, non-production warns), and shutdown-event interruption during the retry delay.
- Run the full `uv run pytest` suite once after implementation and compare against the pre-change baseline for new failures.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
`docs/05_agent_10_01_operations-and-observability-startup-and-health.md` is the likely candidate for referencing `StartupOrchestrator`'s current structure or startup sequence — check `docs/00_index.md`'s "Document References by Task" table against whichever files this issue's implementation actually touches, and update only the matched row(s) without duplicating implementation detail (per `skills/DESIGN.md` Avoid implementation-reference duplication).

## Out of Scope
- Changing the startup sequence's order or any fatal-vs-warning classification behavior.
- Changing the retry counts, delays, or timeout values used in subprocess startup or health checking.
- Adding new startup validation checks.
- Changing the `StartupValidationResult`/`StartupCheckStatus` data model.
- Modifying `scripts/agent/repl_health.py`, `scripts/agent/http_lifecycle.py`, or `scripts/agent/factory.py` internals (tracked separately in `refactor_004`/`refactor_007`, and out of scope here).
- Performance optimization of the startup sequence.

## Dependencies
N/A: none

## Unresolved Questions
- Exact module names and file layout for the six extracted groupings are left to the `issue-to-plan` / `plan-to-implementation-procedure` phases.
- Whether the consolidated retry-once-with-delay helper should be generic enough to also serve future retry use cases outside `startup.py`, or scoped narrowly to this file's two call sites, is left to the implementer to decide and document in the resulting plan.

## AI Implementation Instruction
- Do not change observable behavior: preserve the startup sequence order, fatal-vs-warning classification, `StartupInterrupted` raise conditions, log message text, and user-facing output text exactly.
- Extract the six concerns into separate modules/classes; you may follow the composition/delegation pattern used in `scripts/agent/orchestrator.py`'s and `scripts/rag/ingestion/ingester.py`'s splits as a reference, but it is not mandatory.
- Consolidate the duplicated retry-once-with-delay logic and the duplicated per-source counting logic in `_report_readiness()` — these are concrete, low-risk wins worth doing even if the broader module split is deferred.
- Verify `scripts/agent/repl.py` still works against the refactored `StartupOrchestrator` unmodified.
- Do not touch out-of-scope items (sequence order, timeout/retry values, new checks, other files' internals).
- If a required design decision (module layout, retry-helper scope) is unclear, stop and record it under Unresolved Questions rather than guessing.
