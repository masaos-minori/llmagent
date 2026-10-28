# Procedure: set the slow-consumer gauge from the computed count and refresh it on state changes

## Goal

Make `eventbus_slow_consumer_current` always equal the current slow-consumer count, including zero, and refresh it on unsubscribe, overflow disconnect and shutdown (Plan REQ-002).

## Scope

- Modify only `scripts/eventbus/broker.py`.
- In scope: `slow_consumer_count`, `unsubscribe`, `shutdown` and one private helper.
- Out of scope: metric names, thresholds, health route, tests, docs.

## Assumptions

- The overflow disconnect path in `publish` already calls `unsubscribe`, so refreshing in `unsubscribe` covers it.
- Callers other than `health_route.py` do not call `slow_consumer_count` today.
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- One private helper computes the count and sets the gauge; every state-changing method and the public getter call it.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/broker.py`

### Procedure

- Add `_refresh_slow_consumer_gauge(self) -> int` (new): count subscribers whose `queue.qsize()` is at or above `self._slow_consumer_threshold` over `list(self._subscribers)`, call `_slow_consumer_current.set(count)` unconditionally and return the count.
- Make `slow_consumer_count` return `self._refresh_slow_consumer_gauge()`; remove the `if count > 0` condition.
- Call `_refresh_slow_consumer_gauge()` (new) at the end of `unsubscribe` and, in `shutdown`, set the gauge to 0 after the sentinels are queued.

### Method

Extract the counting loop into one helper and add three calls.

### Details

- `unsubscribe` is idempotent; the refresh is cheap (a loop over current subscribers) and runs on the event loop thread like the callers.
- The gauge name and help text are unchanged.

## Compatibility considerations

- The gauge value now goes back to zero after recovery; nothing else changes.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py tests/eventbus/test_eventbus_broker.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/broker.py`; `uv run ruff check scripts/eventbus/broker.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/broker.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- The gauge reads zero after recovery, after unsubscribe, after an overflow disconnect and after shutdown.

## Out of Scope

- Thresholds, health route.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-165731 | 20261028-165731 | Applied after tests 06 (4 red); gauge also set to 0 in shutdown |
| 2 | Add or update tests per Validation plan | Completed | 20261028-165731 | 20261028-165731 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-165731 | 20261028-165731 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-165731 | 20261028-165731 |  |

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
- **Requirement ID**: REQ-002 (gauge reflects current state)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: scripts/eventbus/broker.py