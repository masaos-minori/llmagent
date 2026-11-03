## Goal
Make `EventBusSubscriber` resume after a reconnect without losing events: track the last processed `seq` and send it as `since_seq` on reconnect (`REQ-002`: seq tracking and `since_seq` resume), replace the per-attempt random `consumer_id` with a configured stable one (`REQ-001`: stable `consumer_id`), and handle HTTP 409 explicitly inside the unchanged retry budget (`REQ-003`: 409 handling).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Server `since_seq` is an exclusive lower bound (replay query `seq > ?` in `scripts/eventbus/subscribe_route.py`), verified against current source; passing the last processed `seq` neither skips nor repeats it.
- The server's persisted resume offset advances only on ACK and this subscriber never ACKs, so `since_seq` is the only effective resume input for this client (`scripts/eventbus/delivery_repo.py`, `scripts/eventbus/subscribe_route.py`).
- No importer of `EventBusSubscriber` under `scripts/` (rg-checked); only `tests/agent/test_eventbus_subscriber.py` instantiates it, so the behavior change has no production blast radius.
- `tools/check_plan_target_overlaps.py` re-run at Step 2 of this cycle: no finding names this Plan; compatible, no ordering needed.
- `implementations/done/20260927-123444_01_scripts_agent_eventbus_subscriber.py.md` and its `_02` test sibling created this module under a different Plan (`plans/20260927-120532_plan.md`); their scope is the initial SSE-client creation, not resume behavior, so this row is `Not implemented`.

## Design decisions
- The last processed `seq` lives in a local of `subscribe()` and is passed to `_stream_once` as a parameter; no instance attribute, so no hidden cross-call state.
- It is recorded after the generator resumes from the `yield`, as `max(last, event.seq)`: at-least-once toward a consumer whose hand-off was interrupted (the server re-delivers on reconnect), exactly-once in the normal gap case.
- Resume input is `since_seq` only, sent only when at least one event was processed; `Last-Event-ID` is not sent.
- `EventBusSubscriberConfig` gains a `consumer_id: str = ""` field (new), validated non-empty in `EventBusSubscriber.__init__` with `ValueError` (fail-fast, Plan UNK-02 choice).
- HTTP 409 is caught as `httpx.HTTPStatusError` with status 409 ahead of the generic `httpx.HTTPError` branch in `subscribe()`, logged with a distinct warning naming the `consumer_id`, and shares the existing attempt counter, `asyncio.sleep(reconnect_delay_sec)` and exhaustion tail (extract the shared tail; do not duplicate it).

## Alternatives considered
- Instance attribute for the last `seq` — rejected: adds hidden mutable state and an unspecified cross-`subscribe()` semantic.
- Recording the `seq` before the `yield` — rejected: risks losing an event the consumer never finished receiving.
- `Last-Event-ID` as resume input — rejected: lowest server precedence, triggers the server's 412 stale-rejection check, and `since_seq` is exact.
- Auto-generating and persisting the `consumer_id` — rejected: an authorization grant must name a known id, and persistence is out of scope.
- Failing immediately on 409, or a longer 409-specific wait — rejected: the Issue allows wait-and-retry (the old connection normally vanishes within the server's disconnect polling), and the retry-budget constraint forbids changing the delay.

## Implementation
### Target file
`scripts/agent/eventbus_subscriber.py`
### Procedure
1. Add the `consumer_id` field to `EventBusSubscriberConfig`; validate it non-empty in `EventBusSubscriber.__init__`, raising `ValueError` otherwise (REQ-001).
2. In `EventBusSubscriber.subscribe`, drop the per-attempt `uuid` generation and use the configured `consumer_id` for every connection attempt (REQ-001).
3. Keep the last processed `seq` in a local of `subscribe()`; record it once the consumer resumes the generator after an event, as `max(last, event.seq)`; pass it to `_stream_once` (REQ-002).
4. In `EventBusSubscriber._stream_once`, accept the resume value and add it as the `since_seq` query parameter only when at least one event was processed; the first connection sends no `since_seq` and no `Last-Event-ID` (REQ-002).
5. Add a 409 branch to `subscribe()` ahead of the generic `httpx.HTTPError` branch: distinct warning naming the `consumer_id`, then the same counter/delay/exhaustion tail as the generic branch; exhaustion raises `EventBusStreamError` chained to the 409 error (REQ-003, REQ-004).
6. Update the module docstring and the `subscribe` docstring that promise a "fresh consumer_id per attempt"; remove the now-unused `uuid` import; keep the first docstring line of each class and function unchanged so generated references do not drift (REQ-007).

### Method
Edit `EventBusSubscriberConfig`, `EventBusSubscriber.__init__`, `EventBusSubscriber.subscribe` and `EventBusSubscriber._stream_once` in place. `_parse_sse_lines`, `EventBusEvent` and `EventBusStreamError` stay unchanged. No new symbols beyond the dataclass field.

### Details
- Current behavior (verified against source): `subscribe` creates `uuid.uuid4().hex` as `consumer_id` per attempt; `_stream_once` sends only `consumer_id` and `topic` params; `_parse_sse_lines` fills `EventBusEvent.seq` but nothing stores or re-sends it.
- Server contract (`scripts/eventbus/subscribe_route.py`, reference only): `since_seq` exclusive lower bound; precedence `since_seq` then persisted resume position then `Last-Event-ID`; replay from the `events` table then live delivery discarding seqs at or below the last replayed; a still-registered `consumer_id` answers 409 (`ConsumerAlreadyConnectedError` raised by `EventBroker.subscribe`).
- 409 detection: `resp.raise_for_status()` in `_stream_once` raises `httpx.HTTPStatusError`; the new branch in `subscribe` checks its response status before the generic branch.
- Retry semantics preserved (REQ-004): attempt counter resets after a yielded event; `max_reconnect_attempts` (5) and `reconnect_delay_sec` (1.0) defaults and their semantics are unchanged.

### Companion test files
- `tests/agent/test_eventbus_subscriber.py`
  - Procedure: add `consumer_id` to the `config` fixture; rewrite `test_subscribe_sends_bearer_auth_and_fresh_consumer_id` and `test_reconnects_with_fresh_consumer_id_after_disconnect` for the stable id; add the gap-event test (fake `stream()` honoring `since_seq`, collected seqs exactly `[1, 2]` and `since_seq == 1` on the second request), first-connect no-`since_seq`/no-`Last-Event-ID`, 409-then-success (same id, warning names the id via `caplog`), 409-exhaustion (`EventBusStreamError` with `__cause__` the status error), empty-`consumer_id` `ValueError`, and attempt-counter-reset tests (Plan `TEST-1`–`TEST-7`).
  - Validation: `uv run pytest tests/agent/test_eventbus_subscriber.py` all green; `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_restart_resume.py` stay green (no server file changes).

## Compatibility considerations
- Two existing tests encode the old fresh-uuid behavior and are rewritten with the companion — tests are the only callers, so no other consumer is affected.
- The new dataclass field has a default, so existing construction calls remain valid; refusing an empty `consumer_id` at construction is a deliberate behavior change for those callers only.
- First docstring lines are kept so `registry/manifests/agent_api.yaml` and `docs/23_agent/agent_13_reference-api-generated.md` do not drift; verified with `uv run python tools/generate_reference_table.py --check`.
- All other `subscribe` behavior is unchanged: any `httpx.HTTPError`/`OSError` is still retried inside the budget, and a clean stream end still reconnects immediately without counting an attempt.

## Security considerations
- A stable `consumer_id` is the precondition for the `(consumer_id, topic)` grant model (`scripts/eventbus/auth.py`); a random id can never hold a grant (403 against an authorization-enabled broker).
- Bearer-token header handling is unchanged; no new credential is introduced. Provisioning the grant for the chosen id is out of scope (Plan UNK-01).

## Rollback considerations
- N/A: revert the commit — single commit, no schema, config, or deploy change (module is rsynced).

## Validation plan
- `uv run pytest tests/agent/test_eventbus_subscriber.py -v` — all pass, including the gap-event test asserting exactly `[1, 2]`.
- `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_restart_resume.py` — pass unchanged (read-only server tests).
- `uv run ruff format` / `uv run ruff check` on both files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/agent/eventbus_subscriber.py -c pyproject.toml -ll` — no findings.
- `uv run radon cc scripts/agent/eventbus_subscriber.py -s` — no rank worse than the current B for `_stream_once`; `uv run python tools/check_module_size.py` — gate passes.
- Diff-scoped coverage per `rules/toolchain.md` section 7 — `diff-cover --fail-under=90` on changed lines.
- `uv run python tools/generate_reference_table.py --check` — no drift.
- Scope guard: `git diff --stat` shows no change under `scripts/eventbus/`, `registry/manifests/eventbus_api.yaml`, `scripts/agent/factory.py` or `scripts/agent/startup*.py`; `rg "eventbus_subscriber" scripts/` finds no importer.

## Completion criteria
- A reconnect request carries `since_seq` equal to the last processed `seq`, and a gap event is delivered exactly once in `seq` order with no duplicate of a pre-disconnect event (AC-1).
- Every connection attempt of one `subscribe()` call sends the configured `consumer_id`; none is a random uuid (AC-2).
- A 409 is retried with the same `consumer_id` and a warning naming it; exhaustion raises `EventBusStreamError` chained to the 409 error (AC-3).
- Retry defaults and attempt-counting semantics are unchanged (AC-4).
- Construction with an empty `consumer_id` raises `ValueError` (AC-5).
- The first connection sends no `since_seq` and no request sends `Last-Event-ID` (AC-6).
- No out-of-scope file changed and no importer added (AC-8).

## Out of Scope
- Wiring `EventBusSubscriber` into `factory.py` or `startup*.py`; sending ACKs; resume across process restarts or separate `subscribe()` calls (Plan UNK-03); a TOML loader for the subscriber config; provisioning the `(consumer_id, topic)` grant in `config/eventbus.toml` (Plan UNK-01); any change under `scripts/eventbus/` or `registry/manifests/eventbus_api.yaml`; `EventBusClient` and `EventBusTopicAdminClient` behavior; the `docs/` wording update (covered by sibling procedure `implementations/20261103-235225_03_docs_23_agent_agent_02_runtime-architecture.md.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the companion test file first per Plan Phase 1 (`TEST-1`–`TEST-7`); new tests fail for the right reason | Pending | — | — | |
| 2 | Implement the subscriber changes per Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. the scope guard | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (stable `consumer_id`), REQ-002 (last-`seq` tracking and `since_seq` resume), REQ-003 (HTTP 409 handling), REQ-004 (retry budget unchanged), REQ-007 (change stays in scope)
- **Source issue**: `issues/20261003-180343_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-152158_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-235225
- **Related target files**: `scripts/agent/eventbus_subscriber.py`, `tests/agent/test_eventbus_subscriber.py`
