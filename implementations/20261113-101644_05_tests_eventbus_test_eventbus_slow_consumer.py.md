## Goal
- Make `test_overflow_disconnects_subscriber` finish in about 2 s or less instead of about 11 s by filling a small subscriber queue, while still asserting the queue is full, the overflow is counted, and the disconnect signal is set (`REQ-005`; `REQ-001`: record that the cost is publish volume).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: a new fixture `small_queue_client` (new) and the one test body of `TestSlowConsumer.test_overflow_disconnects_subscriber`.
- Not in scope: the shared helper `tests/eventbus/eventbus_helpers.py`, other tests of the file except as stated in Details.

## Assumptions
- The cost is publishing 1001 events to fill a queue of the default `subscriber_queue_maxsize` of 1000. Falsifier: with a small queue the test is still slow.
- `EventBroker.__init__` copies `subscriber_queue_maxsize`, `slow_consumer_threshold`, and `backlog_health_threshold` from the config when the app starts (`app.state.broker = EventBroker(app.state.config)` in the lifespan), and `subscribe` builds each queue from the copied value. So the config must be adjusted before the `TestClient` is entered.
- `make_eventbus_client` patches `eb_app.load_config` with a lambda that returns the config object, so calling `eb_app.load_config()` after it returns the same object, which can be adjusted with `object.__setattr__` (the dataclass validation in `__post_init__` is bypassed, so the three values must be kept consistent by hand: threshold below maxsize, backlog threshold at most maxsize).

## Design decisions
- A dedicated fixture, so the shared `client` fixture and the helper stay untouched.
- Values: queue maxsize 20, `slow_consumer_threshold` 10, `backlog_health_threshold` 20.

## Alternatives considered
N/A: changing `eventbus_helpers.make_eventbus_client` would touch a shared helper outside the Plan's target rows.

## Implementation
### Target file
`tests/eventbus/test_eventbus_slow_consumer.py`

### Procedure
1. Measure first: `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py --durations=5 -o addopts=""`.
2. After the `client` fixture, add the fixture `small_queue_client` (new) taking `tmp_path` and `monkeypatch`: build the client with `make_eventbus_client(tmp_path, monkeypatch)`, get the config with `eb_app.load_config()` (import `eb_app` from `eventbus` inside the fixture, as the file's tests do), set the three values above with `object.__setattr__`, then enter the client as a context manager and yield it.
3. Switch `test_overflow_disconnects_subscriber` to `small_queue_client` (new); read the queue size from `eb_app.app.state.config.subscriber_queue_maxsize` and publish that many plus one events instead of the literal 1001; update the comment that mentions `maxsize=1000`.
4. Re-run the command and note the duration.

### Method
The test keeps subscribing with `eb_app.app.state.broker.subscribe([], consumer_id="overflow-test")`, posting events through `client.post("/publish", ...)`, and asserting `sub.queue.full()`, `overflow_disconnect_count() >= 1`, and `sub.disconnect.is_set()`; only the queue size, and so the count, shrinks.

### Details
- Keep `unsubscribe` in the `finally` block.
- If the Phase 1 profile shows `test_reconnect_after_overflow_disconnect_resumes_from_offset` (publishes 1000 events) above the threshold, give it the same fixture and the same size derivation; do not touch other tests.
- Do not change `scripts/eventbus/config.py` or `tests/eventbus/eventbus_helpers.py`.

## Compatibility considerations
N/A: test-only change; no production source or default changes.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -o addopts=""` serially, then with `-n auto`, repeated a few times.
- `uv run ruff check tests/eventbus/test_eventbus_slow_consumer.py` and `uv run mypy --no-namespace-packages tests/eventbus`.

## Completion criteria
- The test finishes in about 2 s or less and still asserts the full queue, the overflow count, and the disconnect signal (`AC-005`).
- No file outside the test file changed.

## Out of Scope
- The shared eventbus test helper and the production configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (record the cause), REQ-005 (cut the publish volume)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/eventbus/test_eventbus_slow_consumer.py`
