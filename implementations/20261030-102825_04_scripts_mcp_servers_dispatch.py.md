# Implementation Procedure: scripts/mcp_servers/dispatch.py

## Goal

Make the durable dedup store (not the per-process `_duplicate_cache`) the truth for
duplicate handling in `dispatch_tool`, record the execution snapshot in the audit path,
apply the REQ-005 replay policy, and run the opportunistic retention sweep (REQ-003
dispatcher cutover; REQ-005; REQ-009).

## Scope

**In scope:**
- `scripts/mcp_servers/dispatch.py`: store-backed lookup/policy in `dispatch_tool`
  (`:152`), `_duplicate_cache` (`:102`) demoted to a completed-only fast-path overlay fed
  from the store, snapshot/dedup state surfaced on `DispatchResult` (`:49`), retention
  sweep flag.

**Out of scope:**
- Store internals (row 02), snapshot builder (row 03), agent-side audit serialization
  (row 05).

## Assumptions

- Needs Confirmation: propagating `dedup_state` (new)/snapshot values from the dispatch response
  back into the agent-side `audit_tool_exec` call in `scripts/agent/tool_runner.py:216`
  crosses files outside the frozen table. This row only emits the fields on
  `DispatchResult` / the transport payload; if the executor call-site edit is needed it is
  an additional-target-file discovery to resolve with the plan owner before implementation.
- `_duplicate_cache` entry shape (`_CacheEntry` at `:98`) stays for the overlay; TTL 3600
  and `_IDEMPOTENCY_CACHE_MAX_ENTRIES = 1024` (`:78`) semantics stay as overlay bounds.

## Design decisions

- Lookup order in the key+side-effecting branch (currently `:189-215`): overlay hit →
  return (fast path kept); else `mcp_dedup.lookup` (row 02 API):
  - `completed` + `snapshots_equal(recorded_snapshot, build_execution_snapshot())` →
    return stored `result_json` (new) payload, populate overlay, audit the duplicate attempt
    exactly as today (the "Duplicate tool call detected" path `:193-200` semantics).
  - same key + different `args_hash` → existing rejection
    `error_type="idempotency_key_reused"` (`:203-215`) — preserved unchanged (REQ-010).
  - `completed` + snapshot mismatch → proceed to a fresh execution on the same key; mark
    the outcome with a new `snapshot_mismatch` (new) tag on `DispatchResult` (new field
    `dedup_state: str = ""`) for the audit path (REQ-005).
  - `pending`/interrupted + `retryable` (per `retry_class` (new), row 02) → re-execute the same
    key: `record_pending` (new) refresh then normal dispatch (replay).
  - interrupted + `non_retryable` (new) → refuse: `DispatchResult(output=..., is_error=True,
    error_type="dedup_unreplayable")` (new taxonomy value, document in the module
    taxonomy docstring `:56` list and row 12) with `dedup_state="unreplayable"`.
- Store writes never span the handler call: `record_pending` (new) before `await handler(args)`
  (`:217` region), `record_completed` (new)/`record_failed` (new) immediately after it returns —
  the transaction boundaries live in row 02.
- Retention: one `purge_expired` (new) sweep per process lifetime, triggered inside
  `dispatch_tool` behind a module-level `_purge_done` (new) flag (REQ-009 "at most one
  sweep per process").

## Alternatives considered

- Removing `_duplicate_cache` entirely — rejected: REQ-003 explicitly keeps it as a
  store-fed overlay so completed-hit latency does not grow.
- Store sweep on a timer/thread — rejected: REQ-009 fixes an opportunistic in-dispatch
  sweep.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
1. Import `shared.mcp_dedup` and `shared.execution_snapshot` (module-level imports must
   respect the import-layer contract: `mcp_servers` may import `shared`).
2. Restructure the `if key and side_effecting:` branch per the Design decisions order.
3. Add store pending/completed/failed writes around the handler call.
4. Add `dedup_state` (new) to `DispatchResult` and set it on every dedup branch.
5. Add the one-shot purge hook.

### Method
Overlay write on completed hits uses the existing `_idem_store` (`:131`) helper unchanged.
Store calls are sync row-02 functions; if event-loop stalls are measured, wrap via
`asyncio.to_thread` (Needs Confirmation — deferred to measurement, per row 02).

### Details
- `args_hash` cross-check between dispatcher normalization and the store row uses the
  same canonical form (row 02 re-implementation; row 17 pins equality).
- Expired-overlay fallthrough (`:199-201`) behavior now re-checks the store instead of
  executing blindly.

## Compatibility considerations

- `DispatchResult` gains one defaulted field — callers unaffected (`test_mcp_dispatch.py`
  fixtures per row 19 adapt cache assumptions; other servers construct via
  `_to_call_tool_response` `:147` unchanged).
- New `error_type` value `dedup_unreplayable` (new) extends the taxonomy — consumers key on
  existing values only, none removed (REQ-010).

## Security considerations

- Stored `result_json` (new) is replayed as-is: same trust level as the original handler output;
  no new injection surface (no eval/interp of stored payloads).

## Rollback considerations

- Reverting this row returns pure overlay behavior; durable rows become inert (row 02
  module unused). No schema change lives in this file.

## Validation plan

- Row 19 (`tests/mcp_servers/test_mcp_dispatch.py`): completed-hit after store reopen
  without re-execution, overlay fast-path still hit, replay-allow for retryable
  interrupted, refuse + `dedup_unreplayable` (new) for non-retryable, snapshot-mismatch fresh
  attempt, one-shot purge behavior.
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py`; `uv run mypy
  --no-namespace-packages scripts/ tests/mcp_servers`; `lint-imports`.

## Completion criteria

- Restarting the server process between two identical calls yields a completed-hit with
  zero handler invocations (plan Phase 6 staging check); every dedup branch is audited as
  today plus `dedup_state` (new); no store transaction is open across `await handler(args)`.

## Out of Scope

- Agent-side turn semantics (rows 07-09); workflow tables (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement store-backed lookup/policy + overlay demotion | Pending | — | — | |
| 2 | Land row 19 test updates (test-first) before or with this row | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Staging check: restart dispatcher between identical calls (plan Phase 6) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (durable dedup at dispatcher), `REQ-005` (replay policy), `REQ-009` (retention sweep)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/mcp_servers/dispatch.py
