## Goal

Align the slow-consumer threshold wording in `docs/24_eventbus/eventbus_07_configuration-and-operations.md` with the code's `>=` comparison (`REQ-004`: the docs say the threshold is reached, not exceeded).

## Scope

Change two sentences in `docs/24_eventbus/eventbus_07_configuration-and-operations.md`: the metrics paragraph (line 138) and the Monitoring Slow Consumers paragraph (line 158). English only, no other section.

## Assumptions

- Source claims re-verified this cycle: line 138 says `/health` reports `slow_consumers_detected` "when a subscriber's queue depth exceeds `slow_consumer_threshold`"; line 158 says "A subscriber queue holding more than `slow_consumer_threshold` events is considered slow"; the code compares `queue.qsize() >= threshold` (`scripts/eventbus/broker.py:134`), and line 61 already requires the threshold to be strictly less than `subscriber_queue_maxsize`.
- The wording change treats "exceeds" as a mismatch (Plan UNK-02, non-blocking, owner may veto); the sibling `backlog_health_threshold` wording is out of scope.
- This file has high churn (21 commits in 30 days); rebase before committing. No overlap with another Frozen Plan on this file.

## Design decisions

- Use "reaches" for the metrics sentence and "at least" for the monitoring sentence, the smallest edits that match `>=`.

## Alternatives considered

N/A: two-word documentation fix.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

1. Open the file and locate the two sentences by searching for `exceeds` near `slow_consumer_threshold` (line 138) and `more than` near `slow_consumer_threshold` (line 158).
2. Apply the replacements in Method; change nothing else on those lines.

### Method

- Line 138: `when a subscriber's queue depth exceeds `slow_consumer_threshold`` becomes `when a subscriber's queue depth reaches `slow_consumer_threshold``.
- Line 158: `A subscriber queue holding more than `slow_consumer_threshold` events is considered slow.` becomes `A subscriber queue holding at least `slow_consumer_threshold` events is considered slow.`

### Details

- Do not add the gauge refresh triggers here; they belong in `eventbus_10_health_endpoint.md` (seq 04).

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: no security-relevant content.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_japanese.py`.
2. `uv run python tools/stale_detector.py implementations/20261029-101659_05_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md`.

## Completion criteria

- Neither "exceeds" nor "more than" describes `slow_consumer_threshold` in the file; the wording says the threshold is reached.
- All docs checkers above pass.

## Out of Scope

- `backlog_health_threshold` wording, the gauge trigger text (seq 04), and code or tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two wording replacements (Implementation > Procedure/Method/Details) | Completed | 20261029-115800 | 20261029-115441 | Changed: docs/24_eventbus/eventbus_07_configuration-and-operations.md (two threshold wordings). Matches the Event Bus (config/ops) row; stale check: clean |
| 2 | Run the documentation checkers named in Validation plan | Completed | 20261029-115441 | 20261029-115441 | check_docs_quality, structure, content_policy (also --strict), japanese, needs_confirmation_inventory, consistency --domain eventbus: all pass; docs-only row, full suite not re-run (code validated by seq 01-03) |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261029-090247_eventbus002_slow-consumer-gauge-refresh.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092153_eventbus002_slow-consumer-gauge-refresh.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101659
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`