## Goal

State in `docs/24_eventbus/eventbus_10_health_endpoint.md` exactly when `eventbus_slow_consumer_current` is refreshed and when it returns to zero (`REQ-004`: documented trigger set equals what the code and tests demonstrate).

## Scope

Rewrite the Slow Consumer Metric paragraph (line 82) of `docs/24_eventbus/eventbus_10_health_endpoint.md`. English only, operational behavior only. No other section, no front matter change.

## Assumptions

- Source claim re-verified this cycle: line 82 reads "It returns to zero after recovery, unsubscribe, an overflow disconnect and shutdown, and repeated `/health` polls do not inflate it."; under Option B the code (seq 01, 02) refreshes the gauge on `/health` reads and on unsubscribe (including an overflow disconnect), sets it to zero at shutdown, and does not refresh it when a queue drains by itself. `subscribe()` does not refresh it.
- Docs content policy (`skills/DESIGN.md`): no file or function names, no signatures, no line numbers in the text.
- Option B is the Plan's decision (UNK-01); if the owner picks Option A, this wording changes.
- The sibling row `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (seq 05) is edited separately; no overlap with another Frozen Plan on this file.

## Design decisions

- Name the triggers by behavior (health read, subscriber removal, shutdown), not by method.
- Keep the existing sentence that `/health` polls do not inflate the gauge; add that the `slow_consumers` field in `/health` is computed fresh.

## Alternatives considered

N/A: documentation-only wording of the Plan's decision.

## Implementation

### Target file

`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure

1. Open the file and locate the "Slow Consumer Metric" paragraph (line 82).
2. Replace that paragraph with the text in Method.

### Method

> `eventbus_slow_consumer_current` is a gauge reporting the current number of slow consumers (not a cumulative counter). A consumer is slow when its queue depth reaches `slow_consumer_threshold`. The gauge is refreshed on every `/health` read and whenever a subscriber is removed (an unsubscribe or an overflow disconnect), and it is set to zero at shutdown. It is not refreshed when a queue drains on its own, so after a consumer recovers the gauge keeps its previous value until the next `/health` read or subscriber removal. Repeated `/health` polls do not inflate it, and the `slow_consumers` field in the `/health` body is always computed fresh.

### Details

- The gauge is in-process only (no scrape endpoint), already stated in `eventbus_07_configuration-and-operations.md` and `eventbus_09_publish_durability.md`; do not repeat it here.

## Compatibility considerations

N/A: documentation-only; the wording matches behavior after seq 01 and seq 02.

## Security considerations

N/A: no credentials or security-relevant content.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_japanese.py`.
2. `uv run python tools/stale_detector.py implementations/20261029-101659_04_docs_24_eventbus_eventbus_10_health_endpoint.md.md`.

## Completion criteria

- The paragraph lists the refresh triggers, the shutdown zero, and the no-refresh-on-drain case, matching the tests from seq 03.
- All docs checkers above pass.

## Out of Scope

- `eventbus_07_configuration-and-operations.md` (seq 05), code (seq 01, 02), tests (seq 03), and any integrity or scrape-endpoint text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the Slow Consumer Metric paragraph (Implementation > Procedure/Method/Details) | Completed | 20261029-115800 | 20261029-115441 | Changed: docs/24_eventbus/eventbus_10_health_endpoint.md (Slow Consumer Metric paragraph). No docs/00_index.md task-scope row lists this document; it is the procedure's named target; stale check: clean |
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
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`