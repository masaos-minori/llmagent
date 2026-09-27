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
2. If no such doc is found, redesign the test: have the first subscription disconnect after receiving only 3 of the 5 published events (`if len(event_ids_first) == 3: break`), confirm via `/replay` (or equivalent) that the stored consumer offset would resume at seq 4, then reconnect with an explicit `since_seq` value that differs from 3 (e.g. `since_seq=1`, so the override is provable: the second subscription should receive events 2 and 3 again — an intentional, expected re-delivery proving the explicit parameter overrode the stored offset — while genuinely not overlapping with event 1, which the first subscription's truncated read never saw... re-derive the exact disjoint pairing based on the corrected first-subscription's truncated event set, not the original full-5 set).
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
| 1 | Confirm intended since_seq precedence semantics (REQ-001) | Pending | — | — | |
| 2 | Redesign the test scenario | Pending | — | — | |
| 3 | Verify the corrected test passes and is meaningful | Pending | — | — | |

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
