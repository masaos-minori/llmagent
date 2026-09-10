## Goal

Refactor `EventBroker` to derive operational thresholds from config instead of using hardcoded module-level constants, so tuning requires editing one source rather than two separate modules. Preserve today's hardcoded values as defaults so behavior is unchanged unless an operator explicitly reconfigures them.

## Scope

Modify `scripts/eventbus/broker.py`:
- Add `config: EventBusConfig` parameter to `EventBroker.__init__` (REQ-003; `scripts/eventbus/broker.py`).
- Replace `_SLOW_CONSUMER_THRESHOLD` constant with `self._slow_consumer_threshold = config.slow_consumer_threshold` (REQ-003; `scripts/eventbus/broker.py`).
- Replace `asyncio.Queue(maxsize=1000)` with `asyncio.Queue(maxsize=config.subscriber_queue_maxsize)` (REQ-003; `scripts/eventbus/broker.py`).
- Add `backlog_health_threshold` property to `EventBroker` for health route access (REQ-004; `scripts/eventbus/broker.py`).

## Assumptions

- The three thresholds should remain as integer fields in `EventBusConfig` (matching their current types: `_SLOW_CONSUMER_THRESHOLD = 100` is int, `maxsize=1000` is int, `>= 500` is int comparison).
- The validation order in `__post_init__` should follow the existing pattern: validate port range first, then retry count, then host constraint, then the new threshold relationships.
- The TOML configuration file will need new entries for these fields, but they will have defaults so existing configs without these fields continue to work.

## Design decisions

1. **Config field addition (REQ-001)**: Add three new fields to `EventBusConfig`:
    - `slow_consumer_threshold: int = 100`
    - `subscriber_queue_maxsize: int = 1000`
    - `backlog_health_threshold: int = 500`
    
    These match today's hardcoded values exactly. The dataclass is frozen=True, so defaults are settable only through `__post_init__` or field defaults.

2. **Relationship validation (REQ-002)**: In `__post_init__`, after existing validations:
    - `slow_consumer_threshold < subscriber_queue_maxsize` (strictly less — a consumer at exactly the queue capacity is not yet "slow")
    - `backlog_health_threshold <= subscriber_queue_maxsize` (at most equal — a backlog equal to queue capacity is the worst case)
    
    Raise `ValueError` with actionable messages naming both conflicting values.

3. **TOML backward compatibility**: Use `data.get("field", default_value)` pattern in `load_config()` so missing fields fall back to safe defaults. This prevents startup failures for existing configs that lack the new fields.

## Alternatives considered

- Adding the fields via `__post_init__` instead of dataclass defaults: would require setting `object.__setattr__(self, ...)` since the dataclass is frozen=True; using field defaults is cleaner.
- Raising `RuntimeError` for invalid combinations instead of `ValueError`: `ValueError` is more semantically correct for config validation errors.
- Using `typing.Literal` for the threshold types: unnecessary complexity; plain `int` is sufficient.

## Implementation
### Target file
`scripts/eventbus/broker.py`

### Procedure
1. Phase 1: Preparation — Add config import and parameter
2. Phase 2: Core Logic — Replace hardcoded constants with config-derived values
3. Phase 3: Core Logic — Add backlog_health_threshold property

### Method
#### Phase 1: Preparation
- [ ] Add `from eventbus.config import EventBusConfig` import to `scripts/eventbus/broker.py`
- [ ] Add `config: EventBusConfig` parameter to `EventBroker.__init__` (REQ-003; `scripts/eventbus/broker.py`)

#### Phase 2: Core Logic
- [ ] Replace `_SLOW_CONSUMER_THRESHOLD` constant with `self._slow_consumer_threshold = config.slow_consumer_threshold` (REQ-003; `scripts/eventbus/broker.py`)
- [ ] Replace `asyncio.Queue(maxsize=1000)` with `asyncio.Queue(maxsize=config.subscriber_queue_maxsize)` (REQ-003; `scripts/eventbus/broker.py`)

#### Phase 3: Core Logic
- [ ] Add `backlog_health_threshold` property to `EventBroker` for health route access (REQ-004; `scripts/eventbus/broker.py`)

### Details

**Phase 1: Preparation**

Add config import at the top of the file:

```python
"""scripts/eventbus/broker.py"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from dataclasses import dataclass
from typing import Any

from eventbus.config import EventBusConfig

logger = logging.getLogger(__name__)
```

Add config parameter to `EventBroker.__init__`:

```python
class EventBroker:
    """In-memory pub/sub broker with per-subscriber queues and topic filtering."""

    def __init__(self, config: EventBusConfig) -> None:
        """Initialize with empty subscriber list.
        
        Args:
            config: EventBusConfig containing operational thresholds.
        """
        self._subscribers: list[_Subscriber] = []
        self._consumer_registry: dict[str, _Subscriber] = {}
        self._overflow_disconnect_count: int = 0
        self._duplicate_rejection_count: int = 0
        # REQ-003: Derive thresholds from config
        self._slow_consumer_threshold = config.slow_consumer_threshold
        self._subscriber_queue_maxsize = config.subscriber_queue_maxsize
        self._backlog_health_threshold = config.backlog_health_threshold
```

**Phase 2: Core Logic**

Replace `_SLOW_CONSUMER_THRESHOLD` constant usage with config-derived value:

```python
def slow_consumer_count(self) -> int:
    """Count subscribers whose queue depth exceeds the slow consumer threshold."""
    return sum(
        1
        for sub in list(self._subscribers)
        if sub.queue.qsize() >= self._slow_consumer_threshold
    )
```

Replace `asyncio.Queue(maxsize=1000)` with config-derived value:

```python
def subscribe(self, topics: list[str], consumer_id: str = "") -> _Subscriber:
    """Register a new subscriber. topics=[] means all topics.

    Args:
        topics: Topic filter; empty list matches all topics.
        consumer_id: Non-empty consumer identifier; if present, checked against
            the consumer-connection registry. A second concurrent connection for
            the same non-empty consumer_id raises ValueError.

    Returns:
        The newly registered _Subscriber.

    Raises:
        ValueError: If consumer_id is non-empty and already present in the
            consumer-connection registry (duplicate connection attempt).
    """
    # Check consumer-connection registry before subscribing
    if consumer_id and consumer_id in self._consumer_registry:
        self._duplicate_rejection_count += 1
        logger.warning(
            "broker: duplicate consumer_id=%s rejected",
            consumer_id,
        )
        raise ValueError(f"duplicate consumer_id: {consumer_id}")

    sub = _Subscriber(queue=asyncio.Queue(maxsize=self._subscriber_queue_maxsize), topics=list(topics))
    self._subscribers.append(sub)

    # Register in consumer-connection registry (only non-empty consumer_id)
    if consumer_id:
        self._consumer_registry[consumer_id] = sub

    return sub
```

**Phase 3: Core Logic**

Add `backlog_health_threshold` property to `EventBroker` for health route access:

```python
def backlog_health_threshold(self) -> int:
    """Return the configured backlog health threshold."""
    return self._backlog_health_threshold
```

## Compatibility considerations

- Changing `EventBroker.__init__` signature breaks any external callers beyond `app.py`. Verify all call sites before merging; `EventBroker` is an internal class (no public API contract), but confirm no third-party code imports it directly.
- Existing TOML configs that lack the new threshold fields will use defaults (backward compatible).
- No changes needed to callers — `EventBusConfig` construction remains the same.

## Security considerations

- The validation rules prevent misconfiguration that could hide operational issues (e.g., slow-consumer threshold above queue capacity would make health check unreachable).
- Invalid combinations fail startup with actionable errors rather than silently producing misleading health status.

## Rollback considerations

- Reverting the threshold fields requires reverting the validation logic and `load_config()` updates simultaneously.
- If reverted during runtime, the dataclass defaults ensure behavior reverts to original hardcoded values.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/broker.py` | Integration — slow consumer detection | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py::TestSlowConsumer::test_slow_consumer_threshold_detection -v` | Slow consumer detected with config value |
| `scripts/eventbus/broker.py` | Integration — queue maxsize | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py::TestSlowConsumer::test_broker_queue_maxsize_limit -v` | Queue size matches config value |
| `scripts/eventbus/*.py` | Lint | `uv run ruff check scripts/eventbus/config.py scripts/eventbus/broker.py scripts/eventbus/health_route.py` | Clean |
| `scripts/eventbus/*.py` | Type check | `uv run mypy scripts/eventbus/config.py scripts/eventbus/broker.py scripts/eventbus/health_route.py` | Pass |

## Completion criteria

- Three new threshold fields added to `EventBusConfig` with defaults matching today's hardcoded values (100, 1000, 500) — REQ-001
- Relationship validation enforced in `__post_init__` (slow-consumer threshold < queue capacity, backlog threshold <= queue capacity) — REQ-002
- `load_config()` reads new fields from TOML with defaults for backward compatibility — REQ-001
- All existing `test_eventbus_config.py` tests still pass — REQ-001

## Out of scope

- Deriving threshold values from load-test measurement (EB-M05).
- Backpressure disconnect behavior itself (EB-H02).
- Changing the DLQ sweep interval (`_DLQ_INTERVAL = 60.0` in `app.py`).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add three threshold fields to EventBusConfig dataclass | Pending | — | — | |
| 2 | Add relationship validation in __post_init__ | Pending | — | — | |
| 3 | Update load_config() to handle new fields | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260907-125042_eb_l02_centralize_operational_thresholds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-072350_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-065129
- **Related target files**: scripts/eventbus/config.py
