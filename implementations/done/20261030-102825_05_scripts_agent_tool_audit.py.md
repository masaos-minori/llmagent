# Implementation Procedure: scripts/agent/tool_audit.py

## Goal

Serialize the execution snapshot and dedup state into the `tool_exec` audit record so the
trace carries the REQ-004 snapshot and the REQ-005 dedup outcome (REQ-004 audit
serialization).

## Scope

**In scope:**
- `scripts/agent/tool_audit.py`: extend `audit_tool_exec` with snapshot/dedup capture and
  serialize the extra fields into the emitted JSON line.

**Out of scope:**
- `scripts/agent/shared/models.py` `ToolExecEvent` (`:45`) dataclass fields — kept
  untouched deliberately (see Design decisions); the producer wiring in
  `scripts/agent/tool_runner.py` (call site `:216-224`) is outside the frozen table.
  Owner decision 2026-10-31: the `tool_runner.py` wiring edit is approved as an
  additional target of the row 04/07 cycle, not of this row.

## Assumptions

- Evidence correction: the plan row states "Fields exist (`:159`, `:188`) but no producer"
  for the snapshot. At HEAD, `audit_tool_exec` parameters `idempotency_key` (`:159`) and
  `task_linkage` (`:160`) exist and `ToolExecEvent` carries them (`:187-188` of the
  event construction), but no `execution_snapshot_json` (new) or `dedup_state` (new) field exists
  anywhere (repo-wide grep for `execution_snapshot` (new) = 0 hits). This document adds them at
  the payload level.
- Needs Confirmation: whether the owner prefers real `ToolExecEvent` dataclass fields
  (models.py edit — an additional target) over this document's payload-extension design.
  Payload extension is chosen to respect the one-file constraint.
- `scripts/agent/tool_runner.py:224` already passes `idempotency_key`; this row keeps that
  signature-compatible (new params are defaulted), so no tool_runner edit is required to
  land this row.

## Design decisions

- Snapshot captured locally inside `audit_tool_exec`: call
  `execution_snapshot.build_execution_snapshot()` (row 03) and store it as
  `execution_snapshot_json` (new) (new payload key, canonical sorted JSON string) — no executor
  wiring needed for the snapshot itself (REQ-004 "recorded ... and serialized").
- `dedup_state` (new) arrives as a new optional parameter `dedup_state: str = ""` on
  `audit_tool_exec`, serialized only when non-empty; the dispatcher-side value (row 04
  `DispatchResult.dedup_state`) reaches it via the call-site wiring noted in Assumptions.
- Emission shape: `payload = dataclasses.asdict(evt)` then
  `payload["execution_snapshot_json"] = ...; payload["dedup_state"] = ...` before
  `_json_dumps` — `ToolExecEvent` and `write_round_exec` (`:195`) stay byte-identical.

## Alternatives considered

- New `ToolExecEvent` dataclass fields — rejected for this row (models.py is not a frozen
  target; see Assumptions for the confirmation path).
- Sampling snapshots only for MCP-sourced events — deferred: REQ-004 says "the dispatch
  audit record"; if volume proves excessive, gate on `source` in a follow-up (Needs
  Confirmation after measurement).

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Add `dedup_state: str = ""` parameter to `audit_tool_exec` (`:150-162` signature).
2. Build the snapshot via `execution_snapshot.snapshot_json(build_execution_snapshot())`
   inside the function after the existing early-return guards (`:163-167`).
3. Serialize: extend the dumped dict with `execution_snapshot_json` (new) and, when non-empty,
   `dedup_state` (new) (single payload mutation before `ctx.services_required.audit_logger.info`).

### Method
Import `shared.execution_snapshot` (agent → shared is contract-legal per `skills/DESIGN.md`).
Snapshot build failure must never break the audit write: wrap in the builder's own
tolerance (row 03 guarantees no raise) — no new try/except needed beyond mypy comfort.

### Details
- Line-size: snapshot JSON adds ~200-400 bytes per record — acceptable next to the
  existing `args_preview` bound (`_bounded_preview`).

## Compatibility considerations

- Existing audit consumers parse JSON-lines tolerantly (additive keys); no existing key
  changes (REQ-010). `test_tool_audit.py` assertions stay green: row's own tests add the
  new keys.

## Security considerations

- Snapshot contains hashes only (row 03); masked-args discipline (`mask_args`) untouched.

## Rollback considerations

- N/A: revert the commit; audit lines simply stop carrying the two new keys.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py` (row's tests run test-first within this
  row's step 2): snapshot key present and parseable, `dedup_state` (new) omitted when empty,
  existing record fields byte-stable.
- `uv run mypy --no-namespace-packages scripts/ tests/agent`; `lint-imports`.

## Completion criteria

- Every `tool_exec` line written through `audit_tool_exec` carries a valid
  `execution_snapshot_json` (new); dispatch-originated records carry `dedup_state` (new) once the
  call-site wiring lands; `tests/agent/test_tool_audit.py` passes.

## Out of Scope

- `ToolExecEvent` dataclass changes (models.py), `tool_runner.py` call-site wiring (both
  Assumptions-flagged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement parameter + snapshot capture + payload serialization | Completed | 20261031-162000 | 20261031-164500 | Payload-level design kept (no `ToolExecEvent` dataclass change): `execution_snapshot_json = snapshot_json(build_execution_snapshot())` inside the existing `extra` dict; `dedup_state: str = ""` keyword-only kwarg (additional target beyond the frozen table's description; existing callers unaffected); serialized only when non-empty per the procedure's "serialize when present" wording; ruff+mypy clean on both files |
| 2 | Extend `tests/agent/test_tool_audit.py` (test-first) | Completed | 20261031-162000 | 20261031-164500 | `TestAuditToolExecSnapshotDedup` appended (4 cases: snapshot+stamp parse, dedup_state present, dedup_state absent, snapshot fields per `ExecutionSnapshot`); test-first red→green confirmed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-164500 | 20261031-164500 | Gates fast-mode all Pass; lint-imports 6 kept; targeted 24 passed; full suite 10722 passed / 8 skipped; diff-cover 93% ≥ 90. Two batch-wide failures surfaced here and were fixed: `tests/agent/test_audit_log_format.py::test_no_key_value_format_in_agent_log` scanned the whole payload for `session=` and tripped on the snapshot's legitimate `schema_versions` value (`session=0;`) — now parses the JSON and excludes the snapshot field before scanning (out-of-table characterization test adjustment, recorded here); reference-table drift (`registry/manifests/agent_api.yaml`) from the row-04 `mcp_dedup` references fixed via `tools/generate_reference_table.py --manifests` (updated `docs/23_agent/agent_13_reference-api-generated.md`) |

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
- **Requirement ID**: `REQ-004` (snapshot serialized into the audit record)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/agent/tool_audit.py
