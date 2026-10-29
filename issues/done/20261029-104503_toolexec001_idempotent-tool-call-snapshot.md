# Establish end-to-end execution consistency with durable tool-call identity and immutable runtime snapshots

## Priority
High

## Summary
Give every logical tool call a deterministic identity that survives retries and process restarts, bind it to exactly one validated runtime configuration generation (an immutable snapshot), persist the tool-call lifecycle, and never guess whether an external side effect occurred after a crash, so routing, approval, execution, recovery, and audit evidence can be reconstructed from persisted identifiers.

## Background
Source: `memo-issue.md` item H-01 (original tasks H-01 and H-03), re-verified against current source on 2026-10-29. The memo is partly ahead of the code but not already implemented: idempotency exists at the transport and server layers, without durability or a snapshot concept.

Existing (`Explicit in code`):
- `scripts/shared/http_transport.py:170-186` generates one random `uuid4` `X-Idempotency-Key` per logical call and reuses it across the transport's own retries within that call.
- `scripts/mcp_servers/dispatch.py:156-215` deduplicates side-effecting tools by that key: a matching prior call is served from `_duplicate_cache`, a reused key with different content is rejected (`idempotency_key_reused`), keyless calls always execute, and error and dry-run results are never cached. `_duplicate_cache` is a module-level `OrderedDict` with TTL and a size bound (`dispatch.py:102, 125-128`), i.e. in-process memory.
- `scripts/agent/workflow/idempotency_ops.py` (`begin_stage_if_new`, `processed_events`) deduplicates workflow stage starts by `event_id`; its docstring notes that `processed_events` means "started", not "completed". `scripts/agent/tool_audit.py:159-188` accepts an `idempotency_key` for audit records.
- `scripts/shared/tool_executor_helpers.py:44` states that the real duplicate-call cache lives server-side in `dispatch.py`.

Absent (`Explicit by absence search` over `scripts/`):
- No `RuntimeConfigurationSnapshot`, snapshot identifier, or generation identifier covering routing, posture, approval, workflow definition, schema, and binary revision.
- No persisted tool-call lifecycle (`planned`, `approved`, `dispatching`, `dispatched`, `outcome_recorded`, `verified`).

Derived (`Derived from confirmed evidence`): because the key is a fresh random value per logical call and the dedup cache is in memory, a call replayed after an agent crash or an MCP server restart gets a new key (or loses its cache entry), so server-side dedup cannot recognize it.

## Problem
Workflow persistence and external MCP side effects cannot share one transaction. After a write-capable tool succeeds and before the workflow outcome is committed, a crash leaves no durable identity for the call, so recovery can repeat the side effect. Separately, routing, posture, approval policy, workflow definition, schema, and binary revision are established in separate startup steps, so an audit record cannot prove that tool exposure, routing, approval, and execution used one effective configuration.

## Reason for Change
Duplicate external side effects after crash recovery are a data-integrity risk for write-capable tools (Priority High on that basis); the evidence for the replay path is derived, not reproduced, and it needs the confirmation listed under Unresolved Questions. The two concerns (call identity and configuration generation) define the execution identity of one logical tool call, so they are filed together. Not tied to a specific date.

## Implementation Intent
Define an immutable runtime configuration snapshot published only after all startup checks succeed, and a deterministic idempotency key derived from the snapshot ID, workflow, task, stage, attempt, tool-call ID, tool name, and canonical argument hash, so a retry after restart reproduces the same key. Persist the tool-call lifecycle in the workflow database and propagate the key and snapshot ID through the tool executor, the HTTP transport, write-capable MCP servers, audit records, and workflow persistence. Make server-side duplicate detection durable for supported write tools, classify tools that cannot guarantee idempotency as non-retryable, and route indeterminate outcomes to operator reconciliation. Deliver in phases (snapshot, then identity, then lifecycle and persistence, then durable server-side dedup); phase boundaries are for the Plan to set. New workflow tables should land through the migration framework tracked in `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`.

## Target Files or Areas
- `scripts/agent/workflow/workflow_engine.py`, `state_store.py`, `idempotency_ops.py`, `models.py`
- `scripts/agent/startup_validation.py`, `scripts/agent/context.py`, `scripts/agent/llm_turn_runner.py`
- `scripts/agent/tool_audit.py`, `scripts/agent/tool_policy.py`
- `scripts/shared/tool_executor.py`, `scripts/shared/http_transport.py`, `scripts/shared/runtime_tool_registry.py`
- `scripts/mcp_servers/dispatch.py` and the write-capable MCP request handlers
- Workflow schema DDL (`scripts/db/schema_sql.py`) and the tests for each of the above

## Required Changes
- Define an immutable `RuntimeConfigurationSnapshot` published only after every startup check passes, including deployed and binary revision, workflow-definition and Agent-configuration hashes, registry and posture generations, tool-definition and policy hashes, schema versions, disabled components, and partial-availability reasons.
- Define a deterministic `idempotency_key` from the identifiers listed in Implementation Intent.
- Persist tool-call lifecycle states and propagate key and snapshot ID through the executor, transport, write-capable MCP servers, audit records, and workflow persistence.
- Make server-side duplicate detection durable for supported write tools.
- Classify tools that cannot guarantee idempotency as non-retryable and route indeterminate outcomes to operator reconciliation.
- Separate reloadable policy fields from restart-only discovery and posture fields.
- Add crash fault-injection tests for failure after the external side effect and before the workflow commit.

## Constraints
- Fail closed: an incomplete startup snapshot is never published, and no warning-only continuation replaces a failed check.
- Preserve existing keyless-call behavior and existing dispatch semantics (error and dry-run results are not cached) unless an Accepted ADR is changed.
- Do not convert an indeterminate outcome into success or failure without evidence.
- Do not introduce a fallback that no Accepted ADR authorizes; changes to ADR-001's persistence decisions need an approval record.

## Acceptance Criteria
- A retried logical tool call cannot repeat a supported external side effect, including across an agent or MCP server restart.
- Every tool call and audit event references exactly one runtime snapshot ID, and exposure, routing, approval, and execution cannot use different generations.
- An incomplete startup snapshot is never published.
- Indeterminate outcomes stay indeterminate; non-idempotent tools are not retried automatically.
- Tests demonstrate recovery after process termination at each persisted lifecycle boundary.

## Testing Expectations
- Regression tests that fail before the change and pass after: same key after restart, dedup after server restart, snapshot publication only after successful checks, one snapshot ID per call and audit event.
- Fault-injection tests at each lifecycle boundary and concurrency tests for the durable dedup store.
- `uv run pytest tests/agent tests/shared tests/mcp_servers`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Documentation Impact
Yes. The workflow, tool-execution, and audit documents and the relevant ADRs must state the execution-identity contract, the lifecycle states, the snapshot contents, and the failure behavior for indeterminate outcomes; operational behavior only, no implementation locations (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Unrelated refactoring or formatting-only changes.
- Idempotency for EventBus NACK (already keyed by the caller's idempotency key) and for stage start deduplication beyond what the lifecycle requires.
- Weakening fail-closed behavior or treating a derived artifact as a replacement for canonical state.

## Dependencies
- Depends on `issues/20261029-104500_dbmig001_forward-only-db-migrations.md` for any `workflow.sqlite` schema change (recommended order: migrations first).
- Coordinate with `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` (posture and tool-definition generation identifiers) and `issues/20261029-104504_adrauth001_adr-authority-model.md` (authority ADR for the new contract).
- Related, archived: `issues/done/20260914-123621_arch02_tool-call-execution-id-idempotency-guard-missing.md` (earlier idempotency guard work); re-verify this issue against it.

## Unresolved Questions
- `Needs confirmation`: whether workflow recovery actually re-executes a tool call after a crash (the replay path is derived from the code above, not reproduced).
- `Needs confirmation`: which write-capable tools can guarantee idempotency, and which must be classified non-retryable.
- `Needs confirmation`: where the durable dedup store should live (a table in `workflow.sqlite`, or per MCP server) and its retention.
- `Needs confirmation`: the deployed revision and binary revision sources that the snapshot should record.

## AI Implementation Instruction
- Read ADR-001, ADR-003, `scripts/mcp_servers/dispatch.py`, `scripts/shared/http_transport.py`, and the workflow engine before editing; build on the existing key propagation instead of replacing it.
- Do not start phase work until the Plan sets phase boundaries; this issue is too large for one change set.
- Keep fail-closed behavior; stop and report open questions about recovery semantics and idempotency classification instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104503
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/startup_validation.py`, `scripts/agent/context.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_policy.py`, `scripts/shared/tool_executor.py`, `scripts/shared/http_transport.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/mcp_servers/dispatch.py`, `scripts/db/schema_sql.py`
