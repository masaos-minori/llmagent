## Goal

Make `EventBusSubscriber` resume after a reconnect without losing events: send a
configured stable `consumer_id` on every attempt and the last processed `seq` as
`since_seq`, and handle HTTP 409 distinctly (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `since_seq` is an exclusive lower bound (`seq > since_seq`); verified in
  `subscribe_route.py` where the replay query is `seq > ?` seeded with `since_seq`.
  Passing the last processed `seq` neither skips nor repeats it.
- `since_seq` is global across topics (a single `events.seq`), so one integer is
  enough even when `topics` has several entries.
- Last-`seq` state is local to one `subscribe()` call (not instance state, not
  persisted). A new `subscribe()` call or a process restart starts without
  `since_seq` (UNK-03 residual gap documented, out of scope).
- The `consumer_id` is recorded when the consumer resumes the generator after
  receiving an event (at-least-once toward the consumer; an event whose hand-off
  was interrupted is re-delivered by the server on reconnect rather than lost).
- Adding a defaulted `consumer_id` field keeps existing constructor calls valid at
  the dataclass level; the subscriber itself now refuses an empty value (UNK-02).

## Design decisions
1. **Where the last `seq` lives.** A local variable in `subscribe()` passed to
   `_stream_once` as a parameter. Alternative: an instance attribute (would also
   resume across separate `subscribe()` calls, but adds hidden mutable state and an
   unspecified cross-call semantic). Neither changes a public signature;
   `_stream_once` is private.
2. **When to record it.** After the generator resumes from the `yield` (the consumer
   asked for the next event), as `max(last, event.seq)`. Resulting delivery toward
   the consumer is at-least-once across a mid-handoff failure, exactly-once in the
   normal gap case.
3. **Resume input.** `since_seq` only. `Last-Event-ID` is not sent: it has the
   lowest precedence, triggers the server's 412 stale check, and `since_seq` is
   exact. Send `since_seq` only when at least one event was processed, so the first
   connection keeps today's behavior.
4. **`consumer_id` source.** A required-in-practice string field
   `consumer_id: str = ""` on `EventBusSubscriberConfig`, validated non-empty in
   `EventBusSubscriber.__init__`. Alternative: auto-generate and persist an id
   (rejected: a grant must name a known id, and persistence is out of scope).

## Alternatives considered
- Instance attribute for last `seq` (rejected: hidden cross-call state, unspecified
  cross-call semantic).
- Fail immediately on 409 (rejected: the old connection normally vanishes within the
  server's disconnect polling interval ~1s; the Issue allows wait-and-retry inside
  the budget).
- A longer 409-specific wait (rejected: the Issue's constraint forbids changing the
  retry budget).

## Implementation
### Target file
`scripts/agent/eventbus_subscriber.py`

### Procedure
1. Add `consumer_id: str = ""` to `EventBusSubscriberConfig` (after
   `reconnect_delay_sec`).
2. In `EventBusSubscriber.__init__`, validate `config.consumer_id` is non-empty and
   raise `ValueError` otherwise (REQ-001, AC-5).
3. In `subscribe()`, remove `import uuid` and the `uuid.uuid4().hex` generation.
   Track a local `last_seq (new): int | None = None`. Pass the stable
   `self._config.consumer_id` and `last_seq (new)` to `_stream_once`. After each
   `yield event`, set `last_seq = event.seq if last_seq is None else max(last_seq,
   event.seq)` (REQ-002, AC-1, AC-6).
4. In `_stream_once`, add a `last_seq (new): int | None` parameter and send
   `since_seq=<last_seq>` in `params` only when `last_seq is not None` (REQ-002,
   AC-6). Never send `Last-Event-ID`.
5. In `subscribe()`, keep the single generic `except (httpx.HTTPError, OSError)`
   branch but add an inner check: when the caught exception is
   `httpx.HTTPStatusError` with `e.response.status_code == 409`, log a warning
   naming the `consumer_id` ("already connected (HTTP 409); retrying"); otherwise
   log the normal disconnect warning. Share ONE retry tail (log +
   `asyncio.sleep(reconnect_delay_sec)` + `attempt += 1` + exhaustion
   `raise EventBusStreamError`) between the two cases — do not duplicate it. This
   keeps the original fail-closed handling for `OSError`/non-status
   `httpx.HTTPError` while distinguishing the 409 (REQ-003, AC-3).
6. Update the module docstring (line 4) and the `subscribe` docstring (lines 74-77)
   to describe the stable `consumer_id` and `since_seq` resume. Keep the first
   docstring line of each class unchanged so generated references do not drift.
7. Remove the now-unused `import uuid`.

### Method
- Thread `last_seq (new)` through `subscribe()` → `_stream_once` as an extra parameter.
  Keep the bounded `while True` retry loop intact.
- Detect 409 as `isinstance(e, httpx.HTTPStatusError) and e.response.status_code ==
  409`, matched before the generic `except (httpx.HTTPError, OSError)` branch so it
  does not get shadowed.
- Share one retry tail (log warning + `asyncio.sleep` + `attempt += 1` + exhaustion
  `raise EventBusStreamError`) between the 409 and generic branches.

### Details
- `EventBusSubscriberConfig`: add `consumer_id: str = ""`.
- `__init__`: `if not self._config.consumer_id: raise ValueError("consumer_id must not be empty")`.
- `subscribe()`:
  ```python
  attempt = 0
  last_seq: int | None = None
  consumer_id = self._config.consumer_id
  while True:
      try:
          async for event in self._stream_once(consumer_id, last_seq):
              attempt = 0
              yield event
              last_seq = event.seq if last_seq is None else max(last_seq, event.seq)
      except (httpx.HTTPError, OSError) as e:
          attempt += 1
          if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 409:
              logger.warning(
                  "EventBusSubscriber consumer_id %s already connected (HTTP 409); retrying",
                  consumer_id,
              )
          else:
              logger.warning(
                  "EventBusSubscriber stream disconnected (attempt %d/%d): %s",
                  attempt,
                  self._config.max_reconnect_attempts,
                  e,
              )
          if attempt >= self._config.max_reconnect_attempts:
              raise EventBusStreamError(
                  f"subscribe stream failed after {attempt} attempts"
              ) from e
          await asyncio.sleep(self._config.reconnect_delay_sec)
          continue
  ```
  (Adjust the exact log wording; the 409 line MUST name the `consumer_id`.)
- `_stream_once(self, consumer_id: str, last_seq: int | None)`:
  ```python
  params: dict[str, Any] = {"consumer_id": consumer_id}
  if last_seq is not None:
      params["since_seq"] = last_seq
  if self._config.topics:
      params["topic"] = self._config.topics
  ```

## Compatibility considerations
- New defaulted dataclass field keeps existing constructor calls valid.
- New `ValueError` at construction for an empty `consumer_id` affects only the test
  callers (no runtime module imports the subscriber today).
- No public signature change; `_stream_once` is private and gains one parameter.

## Security considerations
- A stable `consumer_id` is required for authorization
  (`authorize_consumer_access` needs an explicit `(consumer_id, topic)` grant); the
  empty-id fail-fast prevents a later 403/400 against an authorization-enabled
  broker.
- 409 is retried, never treated as success: the path fails closed.

## Rollback considerations
- Single-module change; revert the commit.

## Validation plan
- Unit: `uv run pytest tests/agent/test_eventbus_subscriber.py` — all pass,
  including the gap-event test (exactly `[1, 2]`) and the 409/empty-id paths.
- Static: `uv run ruff check scripts/agent/eventbus_subscriber.py
  tests/agent/test_eventbus_subscriber.py`, `uv run ruff format --check` on both,
  `uv run mypy`, `uv run bandit -r scripts/agent/eventbus_subscriber.py -c
  pyproject.toml` — no findings.
- Server-side (read-only): `uv run pytest tests/eventbus/test_eventbus_subscribe.py
  tests/eventbus/test_eventbus_restart_resume.py` — pass (no server file changes).
- Scope guard: `git diff --stat` shows no change under `scripts/eventbus/`,
  `registry/manifests/eventbus_api.yaml`, `scripts/agent/factory.py`,
  `scripts/agent/startup*.py`; `rg "eventbus_subscriber" scripts/` finds no importer
  (AC-8).

## Completion criteria
- Every attempt sends the configured `consumer_id` (no random uuid); the first
  request carries no `since_seq`; a reconnect after processing an event carries
  `since_seq == last processed seq`; a gap event is delivered exactly once in order;
  a 409 is retried with the same id and logged distinctly; an empty `consumer_id`
  raises `ValueError` at construction.

## Out of Scope
- Any change to `scripts/eventbus/`, the broker, `auth.py`, `delivery_repo.py`, or
  `registry/manifests/eventbus_api.yaml`.
- Wiring into `factory.py`/`startup*.py`; changing the retry budget; sending ACKs;
  persisting `seq` across restarts; a TOML loader for the subscriber config.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261103-160500 | 20261103-161000 | Added stable consumer_id config field + empty-id fail-fast; rewrote subscribe() to resume via since_seq with single-branch 409 handling; removed import uuid |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261103-161000 | 20261103-162000 | Rewrote 2 tests for stable id; added gap-event/no-since_seq-first/409-then-success/409-exhaustion/empty-id/attempt-reset tests (11 total) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103-162000 | 20261103-163000 | ruff check/format pass; mypy clean on file; bandit 0; client 11 passed; server 42 passed; scope guard clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103-163000 | 20261103-163500 | Module + subscribe docstrings updated for stable consumer_id and since_seq resume |

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
- **Requirement ID**: `REQ-001` (stable configured `consumer_id`, empty-id fail-fast), `REQ-002` (`since_seq` resume), `REQ-003` (distinct 409 handling), `REQ-004` (unchanged retry budget), `REQ-007` (scope stays inside the subscriber)
- **Source issue**: `issues/20261003-180343_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-152158_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-151102
- **Related target files**: `scripts/agent/eventbus_subscriber.py`, `tests/agent/test_eventbus_subscriber.py`

### Companion test files
- `tests/agent/test_eventbus_subscriber.py`
  - Procedure: add `consumer_id` to the `config` fixture; rewrite
    `test_subscribe_sends_bearer_auth_and_fresh_consumer_id` and
    `test_reconnects_with_fresh_consumer_id_after_disconnect` to assert the stable
    id; add a disconnect/reconnect gap-event test (honoring `since_seq`), a
    no-`since_seq`-first-connect test, a 409-then-success test, a 409-exhaustion
    test, an empty-`consumer_id` test, and an attempt-counter-reset test
    (`REQ-001`–`REQ-005`; `TEST-1`–`TEST-7`).
  - Validation: `uv run pytest tests/agent/test_eventbus_subscriber.py`.