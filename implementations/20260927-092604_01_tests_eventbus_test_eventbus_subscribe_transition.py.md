## Goal

Redesign `tests/eventbus/test_eventbus_subscribe_transition.py::TestReconnectResumeSemantics::test_since_seq_precedence_over_consumer_offset`'s scenario so it can verify `since_seq`-overrides-consumer-offset precedence without also asserting a self-contradictory no-overlap condition against its own first subscription's necessarily-overlapping result set (REQ-001).

## Scope

In scope: this one test's scenario in this file. Out of scope: the subscribe/reconnect resume/offset-precedence logic itself (`scripts/eventbus/subscribe_route.py` or equivalent — no evidence of a production defect; the contradiction is confirmed to originate in the test's own assertions).

## Assumptions

- No Requirement/design doc governing the exact "T-7 since_seq precedence" scenario was found at Plan-creation time; absent one, this document designs the corrected scenario per the Plan's own Implementation intent (a genuinely disjoint two-subscription setup) as the best-available interpretation — search once more for such a doc before finalizing, per Implementation step 1 below.

## Design decisions

- Redesign so the first subscription intentionally disconnects after receiving only a subset of events (e.g. 3 of 5), and the second subscription's explicit `since_seq` value differs from what the stored consumer offset would otherwise produce — proving the explicit parameter, not the stored offset, determines the resume point, while keeping the two subscriptions' expected event sets genuinely disjoint.

## Alternatives considered

- Removing the `isdisjoint` assertion entirely while keeping the original 5-events-then-since_seq=3 setup: rejected — this would stop verifying "no duplicate delivery," which per the test's own docstring intent is part of what it should confirm; a corrected scenario that preserves both properties (precedence AND no duplication) is preferable to dropping one.

## Implementation

### Target file

`tests/eventbus/test_eventbus_subscribe_transition.py`

### Procedure

1. Search `plans/done/*.md`/`issues/done/*.md` for "T-7" or "since_seq precedence" to check for a governing Requirement/design doc before finalizing the corrected scenario (per the Plan's Unknown UNK-01's resolution path). If found and it specifies a different intended scenario, follow it instead of step 2 below.
2. If no such doc is found, redesign the test: have the first subscription disconnect after receiving only 3 of the 5 published events (`if len(event_ids_first) == 3: break`), then reconnect with an explicit `since_seq=1` (differs from the stored offset of 3), so the override is provable: the second subscription should receive events 2 and 3 again — an intentional, expected re-delivery proving the explicit parameter overrode the stored offset. Corrected per Step 4a adversarial verification: the stored per-consumer offset is not exposed via any endpoint (confirmed via Read of `scripts/eventbus/subscribe_route.py`/`scripts/eventbus/offsets.py` — no route reads it back), so it cannot be directly confirmed via `/replay`; keep `/replay`'s existing role as a total-published-count sanity check only (mirroring sibling test T-6), and assert the override result as an exact set (`{2, 3}`) rather than an `isdisjoint` check, since re-delivery of 2 and 3 is now the expected, intentional outcome.
3. Update the test's inline comments to describe the corrected scenario accurately (the current comments describe the original, self-contradictory setup).

### Method

Redesign of the test's own scenario (event counts and `since_seq` value), not a mechanical one-line fix — requires judgment per the Plan's own Design section. Re-verify per Completion criteria that the corrected test is genuinely meaningful (would fail if precedence were hypothetically not implemented) before considering this done.

### Details

- Original (self-contradictory) setup: first subscription reads all 5 events (`len(event_ids_first) == 5`); second subscription with `since_seq=3` expects re-delivery of events 4-5, which the first subscription's full read already necessarily contains — making `isdisjoint` unsatisfiable by construction.
- Corrected setup (pending step 1's Requirement-doc search): first subscription reads only a subset (e.g. 3 events); second subscription's explicit `since_seq` targets a range that both (a) differs from the stored-offset-implied resume point and (b) does not overlap the first subscription's actually-received subset.

## Compatibility considerations

- No production code changes; test-only scenario redesign.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior (self-contradictory) scenario.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_subscribe_transition.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -q` | All tests pass |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py::TestReconnectResumeSemantics::test_since_seq_precedence_over_consumer_offset -q` passes.
- The corrected test is confirmed genuinely meaningful: reasoning through (or trying) the offset-only code path (ignoring the explicit `since_seq`) would cause it to fail, confirming it actually tests precedence and is not merely passing by coincidence.
- `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -q` (full file) passes with no regression in other reconnect/resume tests.

## Out of scope

- Other eventbus test files tracked under separate Plans/issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm intended since_seq precedence semantics (REQ-001) | Completed | 20260927-190000 | 20260927-190500 | Searched plans/done/ and issues/done/ for T-7/since_seq precedence: no separate governing Requirement/design doc found beyond the source issue eb006 and this document's own source plan (20260927-083642_plan.md). Proceeded per UNK-01's resolution path using the Plan's own Implementation intent. |
| 2 | Redesign the test scenario | Completed | 20260927-190500 | 20260927-191500 | Redesigned: first subscription breaks after 3 events (offset=3); reconnect uses since_seq=1 (differs from offset); asserts exact set {2,3} instead of isdisjoint, since re-delivery of 2,3 is now the expected proof of precedence. Corrected the procedure doc per Step 4a: stored consumer offset is not exposed via any endpoint (confirmed via Read of subscribe_route.py/offsets.py), so /replay keeps its prior role as a total-count sanity check only. |
| 3 | Verify the corrected test passes and is meaningful | Completed | 20260927-191500 | 20260927-192345 | Targeted test passes; reasoned meaningfulness confirmed inline in the test's own comment (offset-only precedence would yield {4,5}, not {2,3}). Full file (9 tests) passes with no regression. Full repo suite (uv run pytest -q) run once: 8 failed/7996 passed/24 skipped — all 8 failures are pre-existing/unrelated to this file (test_orchestrator.py x3 concurrent WIP by another process, test_eventbus_dlq_promotion.py + test_eventbus_requeue_edge_cases.py are this batch's own not-yet-executed files 3/4, test_eventbus_ack_endpoint.py unrelated, test_check_docs_quality.py regression caused by the earlier, separate, already-committed governance_03 Known-Issues-removal commit ae00c05e — none in tests/eventbus/test_eventbus_subscribe_transition.py. |

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
- **Requirement ID**: REQ-001: redesign `test_since_seq_precedence_over_consumer_offset`'s scenario
- **Source issue**: issues/20260927-075247_eb006_eventbus-subscribe-reconnect-delivers-duplicate-events.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-083642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092604
- **Related target files**: tests/eventbus/test_eventbus_subscribe_transition.py