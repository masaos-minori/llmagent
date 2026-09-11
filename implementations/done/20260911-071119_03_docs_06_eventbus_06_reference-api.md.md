## Goal

Document the closed `format` enum and the snapshot-consistency guarantee for JSON replay pages so operators have one canonical specification rather than scattered hardcoded values across multiple modules. Specifically: document the `format` parameter accepts only `sse` or `json` (returning 422 for others), add a subsection describing the snapshot-consistency guarantee for JSON responses, and document paging behavior when offset exceeds available results.

## Scope

Modify `docs/06_eventbus_06_reference-api.md`:
- Update Replay Route section in `docs/06_eventbus_06_reference-api.md` to specify that `format` accepts only `sse` or `json` (returning 422 for others) (REQ-004; `docs/06_eventbus_06_reference-api.md`).
- Add a subsection describing the snapshot-consistency guarantee for JSON responses (REQ-004; `docs/06_eventbus_06_reference-api.md`).
- Document paging behavior when offset exceeds available results (REQ-004; `docs/06_eventbus_06_reference-api.md`).

## Assumptions

- The `Literal["sse", "json"]` annotation will work correctly with FastAPI's query parameter handling — if it doesn't (FastAPI sometimes struggles with Literal types on query params), fall back to a custom `Enum` class.
- Combining `_fetch()`/`_count()` into a single closure means the DB connection must remain open for the duration of both queries — this is safe since SQLite supports concurrent readers.
- The default `format` value should remain `"sse"` — changing the default would break existing clients.

## Design decisions

1. **Format validation approach (REQ-001)**: Use `Literal["sse", "json"]` type annotation on the `fmt` query parameter in both `app.py` and `replay_route.py`. If FastAPI doesn't support Literal on query params, fall back to a custom `Enum` class.

2. **Snapshot consistency (REQ-003)**: Combine `_fetch()` and `_count()` into a single closure that executes both queries inside the same `run_with_db_lock()` call. This ensures the lock is held across both reads, preventing interleaving with `/publish`.

3. **Precedence of defaults**: Keep `default="sse"` for backward compatibility. If a client sends `?format=json`, they get a JSON response; otherwise, SSE streaming.

4. **Validation mechanism**: Rely on FastAPI's built-in validation — no manual validation needed. Unsupported values will be rejected with HTTP 422 automatically.

5. **OpenAPI exposure**: FastAPI will automatically document the `Literal` type in the OpenAPI schema, listing only `sse` and `json` as valid values.

## Alternatives considered

- Using a custom `Enum` class instead of `Literal`: more verbose but guaranteed to work with all FastAPI versions.
- Adding manual validation logic: unnecessary complexity when FastAPI provides automatic validation.
- Accepting any string value and validating downstream: defeats the purpose of strict API contract enforcement.

## Implementation
### Target file
`docs/06_eventbus_06_reference-api.md`

### Procedure
1. Phase 1: Preparation — Update Configuration Fields section
2. Phase 2: Core Logic — Update Delivery Operations section

### Method
#### Phase 1: Preparation
- [ ] Add the three new fields to the Configuration Fields section (REQ-005; `docs/06_eventbus_05_configuration-and-operations.md`)

#### Phase 2: Core Logic
- [ ] Update the Delivery Operations section to state that thresholds are now config-driven (REQ-005; `docs/06_eventbus_05_configuration-and-operations.md`)

### Details

**Phase 1: Preparation**

Update the Configuration Fields section to add the three new threshold fields:

```markdown
### Configuration Fields

- `port` — HTTP listening port (startup fails if outside 1024–65535)
- `db_path` — SQLite DB path
- `storage_dir` — JSONL archive directory
- `offsets_dir` — Consumer offset directory
- `deadletter_dir` — DLQ directory
- `max_retry` — Retry threshold before DLQ promotion (startup fails if < 1)
- `host` — Listening address (default: `127.0.0.1`; must be `127.0.0.1` or `::1` — see Bind Address below)
- `slow_consumer_threshold` — Queue depth at which a consumer is considered slow (default: `100`)
- `subscriber_queue_maxsize` — Maximum size of each subscriber's delivery queue (default: `1000`)
- `backlog_health_threshold` — Queue depth at which the health endpoint reports degraded status due to broker backlog (default: `500`)

Validation for `port`, `max_retry`, and the threshold relationships is performed in `EventBusConfig.__post_init__()`.
```

**Phase 2: Core Logic**

Update the Delivery Operations section to state that thresholds are now config-driven:

```markdown
### Monitoring Slow Consumers

A process queue exceeding `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration (default: `100`). This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

If a consumer is slow, events are discarded from the queue. The consumer must reconnect and replay from SQLite.

**Threshold validation rules:**
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`
- `backlog_health_threshold` must be less than or equal to `subscriber_queue_maxsize`

Invalid combinations fail startup with actionable error messages naming both conflicting values.
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
| `scripts/eventbus/config.py` | Unit — config validation | `uv run pytest tests/eventbus/test_eventbus_config.py -k "threshold" -v` | New validation tests pass |
| `scripts/eventbus/config.py` | Unit — default preservation | `uv run pytest tests/eventbus/test_eventbus_config.py -v` | All config tests pass |
| `scripts/eventbus/broker.py` | Integration — slow consumer detection | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py::TestSlowConsumer::test_slow_consumer_threshold_detection -v` | Slow consumer detected with config value |
| `scripts/eventbus/broker.py` | Integration — queue maxsize | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py::TestSlowConsumer::test_broker_queue_maxsize_limit -v` | Queue size matches config value |
| `scripts/eventbus/health_route.py` | Integration — health degraded threshold | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -k "503" -v` | 503 triggered at config threshold |
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
