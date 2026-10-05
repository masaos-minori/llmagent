## Goal

Map the per-consumer ACK case to `ERR_EVENT_ALREADY_ACKED` in the `nack` route's invalid-transition branch so that a NACK from consumer C for event E, when C has already ACKed E, returns HTTP 409 with detail `event already acknowledged` (`REQ-001`, `REQ-003`). Keep the events-level and fallback branches intact.

## Scope

**In**:
- Modify `scripts/eventbus/ack_route.py` only — in the `failure_count == -2` branch, check the requesting consumer's `consumer_delivery.acked_at` first and raise `ERR_EVENT_ALREADY_ACKED`; keep the events-level and fallback branches.

**Out**:
- No changes to the `nack_event()` function itself — that is the paired doc `20261005-151801_01_scripts_eventbus_delivery_repo_py.md`.
- No changes to error messages beyond using the existing `ERR_EVENT_ALREADY_ACKED` constant.
- No test authoring here — tests owned by the paired doc `20261005-151801_03_tests_eventbus_test_eventbus_ack_nack_py.md`.

## Assumptions

1. The per-consumer check (paired doc applied): differing current value → keep + log "Keeping existing"; `None` or equal → set (+ "Overwriting" when equal). This doc assumes that change exists; running these tests before it produces false failures.
2. `_mask_secrets()` delegates to `agent.secrets_masker._mask_secrets`, so patching `agent.workflow.approval_ops.find_all_pending_approvals` is not needed here — the function is imported directly from `agent.secrets_masker`.

## Design decisions

- In the `failure_count == -2` branch, first look up `consumer_delivery.acked_at` for the requesting consumer. If found and non-null, raise `ERR_EVENT_ALREADY_ACKED`.
- Only then fall back to the existing `events.acked_at` / `events.dlq_at` inspection.
- This keeps the DLQ 409 and the fallback `invalid NACK transition` branches intact.

## Alternatives considered

- **Sentinel-only replacement**: Replace the entire match with `***MASKED***` without preserving the key name. Rejected — loses useful context (which key was found) and breaks downstream consumers that parse the masked output.
- **Different sentinel format**: Use a different sentinel string. Rejected — the existing regression test asserts `"MASKED" in msg`; changing the sentinel would require updating that test and all downstream consumers.
- **Multiple regex passes**: Run separate passes for key extraction and value masking. Rejected — unnecessary complexity; a single lambda replacement achieves the same result.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

In the invalid-transition branch, check the requesting consumer's `consumer_delivery.acked_at` first and raise `ERR_EVENT_ALREADY_ACKED`; keep the events-level and fallback branches.

### Method

Add a lookup of `consumer_delivery.acked_at` for the requesting consumer in the `failure_count == -2` branch before the existing `events.acked_at` / `events.dlq_at` checks.

### Details

Before (lines 174–187):
```python
if failure_count == -2:
    # Invalid transition: event is already ACKed or DLQ'd
    # Determine which state by checking the event directly
    row = await run_with_db_lock(
        lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    )
    if row and row["acked_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    elif row and row["dlq_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
    else:
        raise HTTPException(status_code=409, detail="invalid NACK transition")
```

After:
```python
if failure_count == -2:
    # Invalid transition: event is already ACKed or DLQ'd
    # Determine which state by checking the event directly
    # First check per-consumer ACK (REQ-001, REQ-003)
    consumer_row = await run_with_db_lock(
        lambda: db.execute(
            "SELECT acked_at FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
    )
    if consumer_row and consumer_row["acked_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    # Then check events-level state
    row = await run_with_db_lock(
        lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    )
    if row and row["acked_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    elif row and row["dlq_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
    else:
        raise HTTPException(status_code=409, detail="invalid NACK transition")
```

Behavior after the change:
- Consumer C ACKs event E → `consumer_delivery.acked_at` is set for `(C, E)`.
- Consumer C sends NACK for event E → `consumer_row` found with non-null `acked_at` → HTTP 409 `event already acknowledged`.
- Consumer D (different consumer) sends NACK for event E → `consumer_row` has null `acked_at` → falls through to events-level check → DLQ 409 or `invalid NACK transition` as before.
- `consumer_id is None` → `consumer_row` lookup fails → falls through to events-level check as before.

## Compatibility considerations

- No public-API change: `nack_event()` signature and return contract are unchanged.
- The `***MASKED***` sentinel is retained, so downstream consumers/tests that look for `"MASKED"` continue to work.
- The masked output format changes slightly: previously `password=h***MASKED***` (one value char leaked); now `password=***MASKED***` (zero value chars). Callers that parse the masked output by splitting on `=` will see the value portion replaced entirely — this is the intended behavior.
- `retry_helper._mask_secrets` delegates to this helper; its callers inherit the fix transitively.

## Security considerations

- This change directly addresses a security concern: short secret values were not masked at all, giving a false sense of protection. The fix ensures ALL values are masked regardless of length.
- No new attack surface introduced — the patterns and sentinel are unchanged; only the replacement expression is modified.
- The fix does not introduce any new dependencies or external calls.

## Rollback considerations

- If the change causes unexpected issues, reverting the replacement expression restores the original behavior. The patterns themselves are unchanged, so the rollback is a single-line revert.
- Downstream consumers that rely on the old masked format (e.g., parsing the masked output) may need adjustment if they expect the partial-value leakage.

## Validation plan

- Run the validation sequence on `scripts/eventbus/delivery_repo.py`: `ruff format/check`, `mypy`, `bandit`.
- Run the new test module: `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v`.
- Confirm existing regression test still passes: `uv run pytest tests/agent/test_http_lifecycle_command_validator.py::test_masked_secrets_in_stderr -v`.

## Completion criteria

- All secret values (short and long) are fully masked — no character of the value appears in the output.
- The key name and separator are preserved in the output.
- The `***MASKED***` sentinel is present in the output.
- Text with no secrets is returned unchanged.
- Empty string returns empty string.
- Arbitrary text never raises.
- Existing regression test `test_masked_secrets_in_stderr` still passes.
- `ruff format/check`, `mypy`, `bandit` clean on `scripts/agent/secrets_masker.py`.

## Out of scope

- Adding patterns for non-`key=value` credential forms (`Authorization: Bearer ...`, `Cookie`, etc.).
- Introducing a general log-redaction framework.
- Changes to call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`, `startup_mcp_starter.py`, `retry_helper.py`).
- Source code changes — covered by the paired doc `20261005-151801_01_scripts_eventbus_delivery_repo_py.md`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-163102 | 20261005-163102 | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20261005-163102 | 20261005-163102 | Tests owned by paired doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `TestStartupOrchestratorRecoverPendingApprovals` | Completed | 20261005-163102 | 20261005-163102 | Cross-row dependency: implement paired test doc first so assertions reflect gated behavior |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-163102 | 20261005-163102 | N/A: doc update covered by paired doc `20261005-151801_04_docs_24_eventbus_eventbus_03_dlq_operations_md.md` |

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
- **Requirement ID**: `REQ-001` — reject NACK when same consumer ACKed; `REQ-003` — route reports `event already acknowledged` for per-consumer case
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-151801
- **Related target files**: scripts/eventbus/ack_route.py