## Goal

Wire the fail-closed rejection for a missing or freshly recreated dedup store into `dispatch_tool`, keep the retryable overlay-only `store_error` behaviour, and route the operator-resolution step (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: Empty-store fail-closed (Plan release unit: Phases 1, 2 — must land together with `mcp_dedup.py` seq 01 before this can be validated alone).

## Assumptions
- The out-of-band lost/recreated flag is produced by `mcp_dedup.py` (seq 01) and exposed on the store handle / open path.
- `retry_class(name, config)` classifies a dispatch-capable MCP tool; unknown tools default to `non_retryable` (`mcp_dedup.py` L166-170).
- The never-seen key on a genuinely fresh store must still execute once; only re-execution of a lost completed non-retryable call is blocked (Plan Risks).
- Open (flag, do not fabricate): how the dispatch path obtains the operator-resolution step and the exact never-seen-vs-lost discrimination (UNK-01) — coordinated with seq 01.

## Design decisions
- **Fail closed on empty/fresh store for non-retryable.** The current else-branch (`dispatch.py` L405-412) does `_store_op(record_pending)` then falls through to `await handler(args)` (L431) with no fresh-store check — this is the empty-store fail-open gap. When the store reports `lost_or_recreated` and the tool is non-retryable, return `dedup_store_error` instead of executing. Retryable tools keep the audited overlay-only `store_error` path.
- **Coordinate with the lookup-exception asymmetry.** `dispatch.py` L309-323 already distinguishes retryable (`store_error`, proceed) from non-retryable (`dedup_store_error`, refuse) when `lookup` raises. Apply the same non-retryable-fail-closed / retryable-overlay asymmetry to the empty/fresh-store case and to a failed `record_pending` (post-open write failure, REQ-002 via seq 02's own `DedupStoreWriteError` (new)).

## Alternatives considered
- **Fail closed for all tools on an empty store.** Rejected: a never-seen key on a genuinely fresh store must execute once (Plan Risks). The discrimination is by retry class, and the sentinel is operator-acknowledged so a genuine first run still executes.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
1. In `dispatch_tool`, after `_dedup_context()` returns a store (`dispatch.py` L304), consult the lost/recreated flag. When the store is missing/freshly recreated:
   - If `retry_class(name, config) == "retryable"`: keep the current overlay-only behaviour (`dedup_state = "store_error"`, proceed to `await handler(args)`).
   - Else (non-retryable): return `DispatchResult(is_error=True, error_type="dedup_store_error", dedup_state="store_error", ...)` WITHOUT calling the handler; log that the call is refused pending operator resolution.
2. Fail closed on a failed `record_pending` after a successful open (post-open write failure, REQ-002). Where `_store_op(..., "record-pending")` is called (`dispatch.py` L406-412), treat a write failure as a `dedup_store_error` refusal for non-retryable tools; raise a new `DedupStoreWriteError` (new) from dispatch.py's own write path (`_store_op`/`_write()`, seq 02) for the non-retryable case, while retryable write failures stay warning-only (the existing `_store_op` bool path).
3. Route the operator-resolution step: the refusal message / log references the operator-resolution step exposed by `mcp_dedup.py` (seq 01); do not invent a separate resolution command here.

### Method
- Reuse the existing non-retryable branch shape at `dispatch.py` L317-323 for the empty/fresh-store refusal so both paths produce identical `dedup_store_error` results.
- Keep `_dedup_context` fail-open (`dispatch.py` L186-193) intact; the flag, not an exception, carries the lost/recreated signal.

### Details
- Do not change the init-failure/disabled path (`dispatch.py` L413-428); it already fails non-retryable tools closed and retryable ones to `store_error`.
- Preserve the idempotency-key-reuse and snapshot-mismatch branches unchanged.

## Compatibility considerations
- Existing retryable tools are unaffected (still overlay-only `store_error`). Only a non-retryable tool against a store that reports lost/recreated changes behaviour — the exact regression scenario.
- A genuinely fresh store (operator-acknowledged sentinel present) behaves as before.

## Security considerations
- This hardens a safety input (non-retryable tools must not silently re-execute). The refusal must be observable (log + `dedup_store_error`), never a silent success.

## Rollback considerations
Revert the commit. No state or schema changes.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -v`:
  - Non-retryable tool rejected (`dedup_store_error`, handler `calls == 0`) against an empty/fresh store.
  - Retryable tool proceeds overlay-only (`store_error`, handler executed) against the same store.
  - First-ever key on a genuinely fresh store executes once.
  - Post-open write failure fails closed for non-retryable, warning-only for retryable.
- Impact-radius check for `dispatch_tool` / `DispatchResult`; full validation sequence.

## Completion criteria
- A non-retryable tool does not execute its side effect when the store reports lost/recreated.
- A retryable tool still proceeds overlay-only; a never-seen key on a fresh store executes once.
- `tests/mcp_servers/test_mcp_dispatch.py` covers all four points.

## Out of Scope
- Adding the detection/sentinel itself (`mcp_dedup.py`, seq 01).
- Config isolation (seq 03-06) and documentation (seq 10-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wire fail-closed rejection for lost/fresh store + post-open write failure in `dispatch.py` | Pending | — | — | Coordinated with seq 01 |
| 2 | Add/modify `tests/mcp_servers/test_mcp_dispatch.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Release unit Empty-store fail-closed |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — fail-closed rejection on loss/recreation, retryable overlay-only exception
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `scripts/mcp_servers/dispatch.py`

### Companion test files
- `tests/mcp_servers/test_mcp_dispatch.py`
  - Procedure: add empty/fresh-store non-retryable rejection, retryable overlay-only, first-ever-key-once, post-open write-failure asymmetry.
  - Validation: `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -v` passes.
