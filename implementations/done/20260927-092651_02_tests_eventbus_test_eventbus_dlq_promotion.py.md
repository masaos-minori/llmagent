## Goal

Remove the stale `dlq_imminent` assertion in `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_delivery_failure_count_gte_max_retry`, consistent with the field's confirmed, cross-documented removal decision (REQ-002).

## Scope

In scope: this one test in this file. Out of scope: `scripts/eventbus/dlq_route.py`'s requeue response shape (confirmed already correct per 3 corroborating implementation-procedure docs).

## Assumptions

- Same as the sibling `test_eventbus_requeue_edge_cases.py` implementation procedure document (same Plan): the `dlq_imminent` removal decision is still current (confirmed via `grep -rl "dlq_imminent"` finding no more-recent reintroduction).

## Design decisions

- Remove the assertion outright, consistent with the confirmed "field no longer included" design decision — do not replace it with an assertion on a different field unless investigation reveals the test's remaining intent needs one.

## Alternatives considered

- N/A: a single, well-evidenced removal with 3 corroborating implementation-procedure documents; no alternative approach considered.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure

1. Re-confirm the test's exact current assertion via Read: `assert data["dlq_imminent"] is True, ("dlq_imminent should be true when delivery_failure_count >= max_retry")`.
2. Remove the assertion and its preceding comment ("Requeue the event — should return dlq_imminent warning") if it becomes misleading.
3. Confirm the test still has a meaningful remaining assertion (e.g. `resp.status_code == 200`) after the removal — if the test's only remaining content is the earlier setup/promotion steps with no post-removal assertion, consider whether the test should instead assert on `new_event_id`/`new_seq` (the confirmed current response fields) to preserve some coverage of the requeue-at-max-retry scenario, rather than leaving the test with no meaningful final assertion.

### Method

Direct assertion/comment removal, with a follow-up check that the test retains a meaningful assertion.

### Details

- Before: `assert data["dlq_imminent"] is True, (...)`. After: assertion removed; confirm `assert resp.status_code == 200` (already present earlier in the test, per the Plan's evidence) remains as the test's meaningful check, or add an assertion on `new_event_id`/`new_seq` if the test would otherwise have no post-removal assertion of substance.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the removed assertion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | All tests pass |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_delivery_failure_count_gte_max_retry -q` passes.
- The test retains at least one meaningful assertion after the `dlq_imminent` removal.

## Out of scope

- `tests/eventbus/test_eventbus_requeue_edge_cases.py` (covered by its own implementation procedure document from this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-195500 | 20260927-195800 | Removed the stale dlq_imminent assertion and its comment; the existing 'assert resp.status_code == 200' remained as a meaningful post-removal assertion, so no new_event_id/new_seq assertion was added (not needed per the procedure's own conditional). Updated the docstring/comment to describe confirmed current behavior. Pre-execution stale_detector.py flagged 4 symbol_missing findings (new_event_id, new_seq x2) — confirmed via rg these do not appear in this test file; these are the procedure's own OPTIONAL fallback suggestion ('add if the test would otherwise have no meaningful assertion'), not a claim about current source, and that fallback was confirmed unneeded here — false positive, not a genuine staleness signal. |
| 2 | Add or update tests per Validation plan | Completed | 20260927-195800 | 20260927-195900 | N/A: removing the stale assertion is itself the fix N/A: removing the stale assertion is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-195900 | 20260927-200200 | ruff/mypy clean; bandit: 1 pre-existing Medium B608 in unrelated _get_field-style helper, unchanged by this cycle. Targeted file: 5/5 pass. Full repo suite run once: 5 failed/7999 passed/24 skipped — down from the pre-cycle 6 (this file's failure now fixed); remaining 5 are pre-existing/unrelated (test_orchestrator.py x3 concurrent WIP by another process, test_eventbus_ack_endpoint.py unrelated, test_check_docs_quality.py regression from the earlier, separate governance_03 commit ae00c05e). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-200200 | 20260927-200251 | N/A: no docs/00_index.md task-scope mapping for this test file N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-002: remove the stale `dlq_imminent` assertion
- **Source issue**: issues/20260927-075248_eb007_eventbus-requeue-response-missing-dlq_imminent-and-conflicting-status.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-083955_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092651
- **Related target files**: tests/eventbus/test_eventbus_dlq_promotion.py