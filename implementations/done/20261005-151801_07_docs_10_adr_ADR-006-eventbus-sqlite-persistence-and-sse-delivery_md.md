## Goal

Remove the pointer to the source Issue from the EVENTBUS-011 Known Deviations bullet and keep the bullet consistent with the final NACK behavior; no Decision text changes (`REQ-007`).

## Scope

**In**:
- Modify `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` only — remove the pointer to the source Issue from the EVENTBUS-011 bullet.

**Out**:
- No source change to `scripts/eventbus/delivery_repo.py` or `scripts/eventbus/ack_route.py` — those are the paired docs `20261005-151801_01_scripts_eventbus_delivery_repo_py.md` and `20261005-151801_02_scripts_eventbus_ack_route_py.md`. The doc update reflects the corrected behavior.
- No changes to the ADR-006 Decision text — only the Known Deviations bullet is updated.
- No changes to other docs or configuration files.

## Assumptions

1. The masking fix (paired doc applied): the entire matched value is masked regardless of length while the key name and separator are preserved. This doc assumes that change exists; updating the doc before it produces stale claims.
2. The four `key=value` families remain the authoritative set: `password`/`passwd`/`pwd`, `api_key`/`apikey`, `secret`, `token` (case-insensitive). No new patterns are added.

## Design decisions

- Remove the limitation note verbatim (lines 91–93 and line 150) rather than softening it — the limitation no longer applies after the masking fix.
- Replace the limitation note with a clear statement of what the masker currently handles (the four `key=value` families, case-insensitive) and what it does not handle (non-`key=value` credential forms like `Authorization: Bearer ...`).

## Alternatives considered

- **Keep the limitation note but mark it as resolved**: Rejected — the limitation no longer applies; keeping it would mislead readers into thinking the gap still exists.
- **Add a separate section documenting the fix**: Rejected — the doc should describe current behavior, not historical limitations. A changelog entry is sufficient for tracking the change.
- **Update only the specific sentence about short values**: Insufficient — the limitation note spans multiple lines and references the defect broadly; a targeted edit risks leaving residual misleading context.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

Remove the Issue pointer from the EVENTBUS-011 bullet.

### Method

Edit the doc to remove the limitation note and replace it with an accurate description of the masker's current behavior.

### Details

Before (line 386):
```markdown
- **Known Issue**: EVENTBUS-011 — `nack_event()` now returns `(-2,-2)` for invalid transitions (already ACKed or DLQ'd), and `ack_route.py` converts this to HTTP 409. However, the caller (`_nack_and_promote()`) checks `failure_count == -2` but does not verify whether the event is actually in the database before raising 409 — if the event was deleted between the NACK call and the status check, a spurious 409 could be returned (the intended response is 404). Separately, a NACK after a same-consumer ACK is currently accepted rather than rejected with 409, because the per-consumer ACK path does not set `events.acked_at`; see `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`.
```

After:
```markdown
- **Known Issue**: EVENTBUS-011 — `nack_event()` now returns `(-2,-2)` for invalid transitions (already ACKed or DLQ'd), and `ack_route.py` converts this to HTTP 409. However, the caller (`_nack_and_promote()`) checks `failure_count == -2` but does not verify whether the event is actually in the database before raising 409 — if the event was deleted between the NACK call and the status check, a spurious 409 could be returned (the intended response is 404).
```

The second sentence about the same-consumer ACK is removed entirely — it is no longer a known issue after the fix.

## Compatibility considerations

- No public-API change: `_mask_secrets()` signature and return contract are unchanged.
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
- Validate doc consistency: `uv run check-agent-docs`.

## Completion criteria

- The "known defect / short values not masked" limitation note is removed from the doc.
- The doc states the final set of masked forms: the four `key=value` families (`password`/`passwd`/`pwd`, `api_key`/`apikey`, `secret`, `token`), case-insensitive.
- `check-agent-docs` reports no drift.

## Out of scope

- Adding patterns for non-`key=value` credential forms (`Authorization: Bearer ...`, `Cookie`, etc.).
- Introducing a general log-redaction framework.
- Changes to call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`, `startup_mcp_starter.py`, `retry_helper.py`).
- Source code changes — covered by the paired doc `20261005-151801_01_scripts_eventbus_delivery_repo_py.md`.
- Test authoring — covered by the paired doc `20261005-151801_03_tests_eventbus_test_eventbus_ack_nack_py.md`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-163536 | 20261005-163536 | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20261005-163536 | 20261005-163536 | Tests owned by paired doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `TestStartupOrchestratorRecoverPendingApprovals` | Completed | 20261005-163536 | 20261005-163536 | Cross-row dependency: implement paired test doc first so assertions reflect gated behavior |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-163536 | 20261005-163536 | N/A: doc update covered by paired doc `20261005-151801_04_docs_24_eventbus_eventbus_03_dlq_operations_md.md` |

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
- **Requirement ID**: `REQ-007` — update startup-and-health operations doc to remove the leakage limitation note and state the final masked forms
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-151801
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md