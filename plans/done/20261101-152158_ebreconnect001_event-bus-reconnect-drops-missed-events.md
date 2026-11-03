## Goal
- Make `EventBusSubscriber` (`scripts/agent/eventbus_subscriber.py`) resume after a reconnect without losing events: track the last processed `seq`, send it as `since_seq` on reconnect, and replace the per-attempt random `consumer_id` with a stable `consumer_id` from a new `EventBusSubscriberConfig` field, with explicit handling of HTTP 409 (`ConsumerAlreadyConnectedError`) while the previous connection is still registered, proven by a disconnect/reconnect test in which an event is published during the gap.

## Priority
Low

## Scope
- **In-Scope**:
  - A new `consumer_id` field on `EventBusSubscriberConfig`, used for every connection attempt of `EventBusSubscriber.subscribe()` (no `uuid` generation any more).
  - Tracking the last processed `seq` across reconnects within one `subscribe()` call and sending it as the `since_seq` query parameter on reconnect.
  - Explicit, separately logged handling of HTTP 409 on the reconnect path, inside the existing bounded retry budget.
  - Tests: a disconnect/reconnect test with an event published during the gap (asserting exactly-once delivery), updates to the two existing tests that assert the old fresh-`consumer_id` behavior, and tests for the stable id, the 409 path and the empty-`consumer_id` guard.
  - Updating the one `docs/` statement that says the subscriber reconnects "with a fresh `consumer_id`", only as part of the implementation phase (after the code behaves that way).
- **Out-of-Scope**:
  - Wiring `EventBusSubscriber` into `factory.py` or `startup*.py` (no runtime component imports it today; separate future task).
  - Any change to the broker, the server resume logic (`scripts/eventbus/subscribe_route.py`, `scripts/eventbus/delivery_repo.py`), the authorization layer (`scripts/eventbus/auth.py`) or `registry/manifests/eventbus_api.yaml`.
  - `EventBusTopicAdminClient` and `EventBusClient` behavior.
  - Changing the bounded retry budget (`max_reconnect_attempts`, `reconnect_delay_sec` defaults and semantics).
  - Sending ACKs from the subscriber, persisting the last `seq` across process restarts or across separate `subscribe()` calls, a TOML loader for the subscriber config, and provisioning the authorization grant for the chosen `consumer_id` in `config/eventbus.toml` (deployment decisions; see Unknowns).
- **Dependencies**: N/A: none. The Issue lists none; no other active or archived Plan under `plans/` or `plans/done/` targets `scripts/agent/eventbus_subscriber.py` as a modification target (`tools/check_plan_target_overlaps.py` was run in Step 8b; result recorded in Assumptions). The archived Plan `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` only cites the subscriber as a client relying on the omitted-`topic` behavior, which this Plan does not change.

## Background
`EventBusSubscriber` is the Agent-side SSE client for `GET /subscribe`. It, `EventBusClient` and `EventBusTopicAdminClient` are instantiated only in tests; no runtime module imports them (`docs/23_agent/agent_02_runtime-architecture.md` says the same). The event bus server already supports resume: `subscribe` in `scripts/eventbus/subscribe_route.py` accepts `since_seq`, otherwise resumes from the persisted per-consumer resume position (`get_resume_position` in `scripts/eventbus/delivery_repo.py`), otherwise from `Last-Event-ID`, replays from the SQLite `events` table in batches and then switches to live delivery, discarding live events at or below the last replayed `seq`. Authorization requires an explicit `(consumer_id, topic)` grant (`authorize_consumer_access` in `scripts/eventbus/auth.py`), and the broker rejects a second connection for a `consumer_id` that is still registered with HTTP 409 (`EventBroker.subscribe` raising `ConsumerAlreadyConnectedError`). The gap is client-side only.

## Problem
`EventBusSubscriber.subscribe()` creates `uuid.uuid4().hex` as `consumer_id` for every attempt. `_stream_once` sends only `consumer_id` and `topic`; it parses `seq` from the SSE `id:` line (`_parse_sse_lines`) but nothing stores it, and neither `since_seq` nor `Last-Event-ID` is ever sent. After a successful reconnect the subscription starts at the live edge, so events published during the outage are lost with no error surfaced. A random `consumer_id` can never hold a grant, so a broker with authorization enabled answers 403 (and, for a principal that holds grants, an empty `consumer_id` is answered 400). Repository evidence adds one fact the Issue does not state: the server-side persisted offset advances only when an ACK is processed (`delivery_repo.py` offset upsert in the ACK path), and the subscriber never ACKs, so for this client `since_seq` is the only effective resume input.

## Reason for Change
If the subscriber is wired into the live agent, a transient network blip, well inside the bounded retry budget, would silently and permanently drop every event published during the outage, including event types the agent may rely on for correctness. Fixing it before wiring avoids shipping a client that cannot authenticate against an authorization-enabled broker and loses events on reconnect.

## Implementation Intent
Keep the change inside the subscriber. Add a configured `consumer_id` and use it unchanged for all attempts. Keep the last processed `seq` in a local of `subscribe()`; once an event has been handed to the consumer and the consumer asks for the next one, record its `seq`; on every connection attempt after at least one event was processed, pass `since_seq=<last seq>` (server semantics: events with `seq` greater than the value). Treat HTTP 409 as a retryable condition that is logged distinctly and consumes the same retry budget as any other failure; when the budget is exhausted the existing `EventBusStreamError` (chained to the HTTP error) surfaces it. No server, broker, manifest or wiring change.

## Requirements
- `REQ-001`: `EventBusSubscriberConfig` gains a `consumer_id` field, and `EventBusSubscriber` sends that same value as the `consumer_id` query parameter on every connection attempt; no per-attempt random id is generated. An empty `consumer_id` is rejected when the subscriber is constructed (fail fast; see UNK-02).
- `REQ-002`: `EventBusSubscriber.subscribe()` records the last processed `seq` and, on every connection attempt after at least one event was processed, sends it as the `since_seq` query parameter; the first connection of a `subscribe()` call sends no `since_seq`. `Last-Event-ID` is not sent.
- `REQ-003`: HTTP 409 on a (re)connect attempt is handled explicitly: logged with a message that names the conflicting `consumer_id`, retried with the same `consumer_id` after the existing delay, and counted against the existing attempt budget; exhaustion raises `EventBusStreamError` chained to the 409 error. No other status-code behavior changes.
- `REQ-004`: The bounded retry behavior is unchanged: attempt counting (reset after a yielded event), `max_reconnect_attempts`, `reconnect_delay_sec` and their defaults.
- `REQ-005`: Tests prove the behavior: a disconnect/reconnect cycle with an event published during the gap is delivered exactly once and in order after reconnect, the two existing tests that assert a fresh uuid `consumer_id` are rewritten for the stable id, and the 409 and empty-`consumer_id` paths are covered.
- `REQ-006`: The documentation statement that the subscriber reconnects "with a fresh `consumer_id`" is corrected to say it reconnects with its configured stable `consumer_id` and resumes via `since_seq`, in the same change that implements REQ-001 and REQ-002 (not before).
- `REQ-007`: The change stays inside the stated scope: `EventBusSubscriber` is not imported by `scripts/agent/factory.py` or any `startup*.py`, and no file under `scripts/eventbus/` or `registry/manifests/eventbus_api.yaml` changes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/eventbus_subscriber.py` | Add `consumer_id` to `EventBusSubscriberConfig`, validate it in `EventBusSubscriber.__init__`, drop the `uuid` generation in `EventBusSubscriber.subscribe`, track the last processed `seq`, pass `since_seq` and the stable `consumer_id` from `_stream_once`, add the distinct 409 handling, and correct the module/`subscribe` docstrings that promise a fresh `consumer_id` | Implements the client-side resume and stable identity; the current code generates `uuid.uuid4().hex` per attempt, never stores the parsed `seq` and never sends `since_seq` | REQ-001, REQ-002, REQ-003, REQ-004, REQ-007; AC-1, AC-2, AC-3, AC-4, AC-6 | Symbols `EventBusSubscriberConfig`, `EventBusSubscriber.subscribe`, `EventBusSubscriber._stream_once`, `_parse_sse_lines` read in full; `uuid` import and the module docstring "fresh consumer_id per attempt" present; no importer under `scripts/` besides the file itself (checked in Step 2 and Step 3) | `tests/agent/test_eventbus_subscriber.py` | Verified |
| `tests/agent/test_eventbus_subscriber.py` | Add `consumer_id` to the `config` fixture; rewrite `test_subscribe_sends_bearer_auth_and_fresh_consumer_id` and `test_reconnects_with_fresh_consumer_id_after_disconnect` (they assert a 32-char uuid and differing ids); add a disconnect/reconnect test against a fake server that honors `since_seq`, a 409-then-success test, a 409-exhaustion test and an empty-`consumer_id` test | The Issue requires a gap-event regression test; the two named tests encode the behavior being replaced and would fail after the change | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; AC-1, AC-2, AC-3, AC-4, AC-5 | Both named tests and the `_FakeStreamResponse` / `_FakeStreamContextManager` / `_mock_http_with_lines` helpers read in full; the fixture has no `consumer_id` today (checked in Step 2) | itself | Verified |
| `docs/23_agent/agent_02_runtime-architecture.md` | Correct the "EventBus Client Modules" paragraph that says `EventBusSubscriber` reconnects "with a fresh `consumer_id`" | That sentence becomes false once REQ-001 and REQ-002 land; the Issue asks for docs to state the resume only once implemented | REQ-006; AC-7 | The paragraph under "EventBus Client Modules" contains the phrase "reconnecting with a fresh `consumer_id`" (checked in Step 2) | `uv run python tools/check_docs_consistency.py --domain agent` (docs validation, no pytest target) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/subscribe_route.py` | Server contract: `since_seq` is an exclusive lower bound, precedence `since_seq` then resume position then `Last-Event-ID`, 409 on `ConsumerAlreadyConnectedError`, `Last-Event-ID` above max seq answers 412, replay then live with de-duplication by `seq` | REQ-002, REQ-003 |
| `scripts/eventbus/broker.py` | `EventBroker.subscribe` raises `ConsumerAlreadyConnectedError` for a registered `consumer_id`; `unsubscribe` releases it | REQ-003 |
| `scripts/eventbus/auth.py` | `authorize_consumer_access` needs an explicit `(consumer_id, topic)` grant, which is why the id must be stable and configured | REQ-001 |
| `scripts/eventbus/delivery_repo.py` | The persisted offset advances only on ACK (`get_resume_position`, ACK path), so the ACK-less subscriber depends on `since_seq` | REQ-002 |
| `scripts/eventbus/app.py` | `resolve_subscribe_identity` passes the real `consumer_id` and `topic` into the grant check on `GET /subscribe` | REQ-001 |
| `registry/manifests/eventbus_api.yaml` | Server API manifest; unchanged, read to confirm the `subscribe` signature already has `since_seq` and `consumer_id` | REQ-007 |
| `registry/manifests/agent_api.yaml` | Generated agent manifest entries for the subscriber classes; their summaries come from the first docstring line, which the change keeps, so no regeneration is expected | REQ-006 |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference table for the subscriber classes; same reasoning as above | REQ-006 |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Documents `GET /subscribe` resume precedence, duplicate-connection 409 and idle timeout; wording to align with | REQ-002, REQ-003, REQ-006 |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Documents the offset/resume-position rules and that offsets advance on ACK | REQ-002 |
| `config/eventbus.toml` | Shows where grants are configured (`consumer_authorization`, commented example); read-only, grant provisioning is out of scope | REQ-001 |
| `tests/eventbus/test_eventbus_subscribe.py` | Existing server-side subscribe tests; relevant eventbus broker tests the Issue asks to re-run | REQ-005 |
| `tests/eventbus/test_eventbus_restart_resume.py` | Existing server-side resume tests (same `consumer_id` reconnect); style reference for the gap scenario | REQ-005 |
| `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` | Archived Plan that records the subscriber's dependence on the omitted-`topic` behavior and UNK-02 about deployed consumers | REQ-001 |
| `skills/deploy/SKILL.md` | The deploy hand-off step cites it | Implementation step 4 |

## Acceptance Criteria
- `AC-1` (REQ-002, REQ-005): After a disconnect, the reconnect request carries `since_seq` equal to the last processed `seq`, and an event published during the gap is delivered exactly once, in `seq` order, with no duplicate of an event delivered before the disconnect.
- `AC-2` (REQ-001, REQ-005): Every connection attempt of one `subscribe()` call sends the configured `consumer_id`; none is a random uuid.
- `AC-3` (REQ-003, REQ-005): A 409 on reconnect is retried with the same `consumer_id` and, if the next attempt succeeds, events resume; if every attempt gets 409, `EventBusStreamError` is raised chained to the HTTP error. The 409 log line names the `consumer_id`.
- `AC-4` (REQ-004, REQ-005): The existing tests for `max_reconnect_attempts` exhaustion and for the attempt counter reset still pass unchanged in meaning; the defaults of `max_reconnect_attempts` (5) and `reconnect_delay_sec` (1.0) are unchanged.
- `AC-5` (REQ-001, REQ-005): Constructing `EventBusSubscriber` with an empty `consumer_id` raises `ValueError`.
- `AC-6` (REQ-002): The first connection of a `subscribe()` call sends no `since_seq`, and no request sends `Last-Event-ID`.
- `AC-7` (REQ-006): The `docs/` statement about the subscriber's reconnect behavior names the configured stable `consumer_id` and `since_seq` resume, and `tools/check_docs_consistency.py --domain agent` passes.
- `AC-8` (REQ-007): `git diff` shows no change under `scripts/eventbus/`, `registry/manifests/eventbus_api.yaml`, `scripts/agent/factory.py` or `scripts/agent/startup*.py`, and `rg "eventbus_subscriber" scripts/` finds no importer.

## Tests
- `TEST-1` (REQ-002, REQ-005): Disconnect/reconnect with a gap event. A fake `stream()` backed by an in-memory event list that honors `since_seq` (returns events with `seq` greater than the parameter): the first stream yields `id:1`, then raises `httpx.ReadTimeout`; an event `seq=2` is appended while "disconnected"; the second stream is built from the request's `since_seq`. Assert the collected sequence is exactly `[1, 2]` and the second request had `since_seq == 1`.
- `TEST-2` (REQ-001, REQ-005): Replacement of `test_subscribe_sends_bearer_auth_and_fresh_consumer_id` and `test_reconnects_with_fresh_consumer_id_after_disconnect`: assert the configured `consumer_id` is sent on the first and on the reconnect request, and the bearer header is unchanged.
- `TEST-3` (REQ-002, REQ-005): First request has no `since_seq` and no `Last-Event-ID` header; after a reconnect before any event was processed the request still has no `since_seq`.
- `TEST-4` (REQ-003, REQ-005): First attempt raises `httpx.HTTPStatusError` with status 409 (constructed from an `httpx.Response(409, request=...)`), second attempt succeeds: events are delivered, both requests used the same `consumer_id`, and a warning mentioning the `consumer_id` is logged (`caplog`).
- `TEST-5` (REQ-003, REQ-004, REQ-005): 409 on every attempt raises `EventBusStreamError` after `max_reconnect_attempts`, with `__cause__` the status error; the existing `test_raises_typed_error_after_max_reconnect_attempts` stays.
- `TEST-6` (REQ-001, REQ-005): Empty `consumer_id` raises `ValueError` at construction.
- `TEST-7` (REQ-004): Attempt counter still resets after a yielded event (disconnect, one event, disconnect again does not exhaust a budget of 2).
- Existing server-side checks the Issue asks to re-run: `tests/eventbus/test_eventbus_subscribe.py` and `tests/eventbus/test_eventbus_restart_resume.py` (read-only here; they must stay green because no server file changes).

## Documentation Impact
`docs/23_agent/agent_02_runtime-architecture.md` must be updated (REQ-006; AC-7): its "EventBus Client Modules" paragraph says `EventBusSubscriber` reconnects "with a fresh `consumer_id`", which the change makes false. The Issue marked documentation impact as `N/A`, but its own note ("state in `docs/` that the subscriber resumes via `since_seq` once implemented, not before") plus this stale claim make the update required, and only in the implementation phase. Route through `skills/python-documentation/SKILL.md` per `routing.md`, then run the docs checkers from `routing.md` Tools ("When to run which tool") for a `docs/*.md` edit. `docs/24_eventbus/*` already describes the server side correctly and does not change (the server is unchanged). The generated reference docs and manifests are not expected to change (first docstring lines kept); verify with `uv run python tools/generate_reference_table.py --check`.

## Assumptions
- The server's `since_seq` is an exclusive lower bound (`seq > since_seq`); verified in `subscribe_route.py` (replay query `seq > ?` seeded with `after_seq`), so passing the last processed `seq` neither skips nor repeats it.
- `since_seq` is global across topics (a single `events.seq` sequence), so one integer is enough even when `topics` has several entries.
- A subscriber principal holding grants and omitting `topic` is narrowed to its granted topics by the server (`effective_topics`), so the existing omitted-`topic` behavior needs no client change (ebauth001).
- Existing behavior kept deliberately: any `httpx.HTTPError` (including 401, 403, 412 as `HTTPStatusError`) and `OSError` is retried inside the budget, and a clean stream end reconnects immediately without counting an attempt; neither is part of this Issue.
- Last-`seq` state is local to one `subscribe()` call (not instance state, not persisted); a new `subscribe()` call or a process restart starts without `since_seq`. This is a judgment call to keep hidden state out of the client; see UNK-03 for the residual gap.
- The `consumer_id` is recorded when the consumer resumes the generator after receiving an event (at-least-once toward the consumer; an event whose hand-off was interrupted is re-delivered by the server on reconnect rather than lost).
- Step 8b overlap check (`tools/check_plan_target_overlaps.py`) was run after freezing: no finding names this Plan or any of its three target files; the 24 findings it listed concern other Plans only. Recorded result: compatible, no ordering needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Where the stable `consumer_id` comes from in a deployment (configuration key, who owns it) and how its `(consumer_id, topic)` grant is provisioned in `config/eventbus.toml` | No TOML loader or `config/agent.toml` section exists for `EventBusSubscriberConfig`, and the subscriber is not wired; the Issue itself lists this as an owner decision | Owner decides when the subscriber is wired in (separate task); this Plan only adds the dataclass field | False |
| UNK-02 | Behavior for an empty `consumer_id` (this Plan chooses fail-fast `ValueError` at construction) | Needs confirmation of the owner's preference; the only evidence is that an authorization-enabled server rejects an empty id for a principal with grants (`subscribe_route.py` answers 400, and `authorize_consumer_access` denies without grants), so an empty id is never usable against such a broker | Implement fail-fast; if the owner wants an unauthenticated local mode, relax it in the same file and test | False |
| UNK-03 | Whether resume must also cover (a) a reconnect before any event was processed, and (b) a restart or a second `subscribe()` call | Server offsets advance only on ACK and the subscriber never ACKs; with no `since_seq` the server falls back to the persisted offset (0 without ACKs), so events published before the first processed event, or across a restart, are not replayed. Needs confirmation of whether the future wiring requires it | Owner decides before wiring: ACK from the subscriber or persisting the last `seq`; both are out of scope here and would be a new Issue | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/eventbus_subscriber.py` | Modify | Low: no importer under `scripts/` besides the module itself; only `tests/agent/test_eventbus_subscriber.py` constructs it; config dataclass gains a field | 0 commits | High: 1 author, 1 commit | not applicable (rsynced) |
| `tests/agent/test_eventbus_subscriber.py` | Modify | Low: test-only | 0 commits | High: 1 author, 1 commit | not applicable (rsynced) |
| `docs/23_agent/agent_02_runtime-architecture.md` | Modify | Low: one paragraph; also cited by docs consistency checks | 22 commits (high-churn document; merge conflicts possible with parallel docs work) | Moderate: 2 name spellings of the same author, 25 commits | not applicable (rsynced) |

## Design
Path B analysis (architecture, dependency graphing, historical, operational), summarized:
- Architecture: `lint-imports` reports 6 contracts kept, 0 broken; the subscriber imports only `httpx`, `orjson` and the standard library, so no layering change. Callers: none in `scripts/` (searched with `rg` for `eventbus_subscriber`); only tests instantiate it. `radon cc`: `_stream_once` B (7), `subscribe` A (5); `vulture scripts/ --min-confidence 80` reports nothing for this module; `bandit` on the module reports no issues (all checked in Step 5). `uv run python tools/check_module_size.py` is expected to stay below its gate (module is about 4.7 KB).
- Operational: no process, port or database is touched by planning; implementation is client-only.

Design decisions (applied narrowly, per `skills/python-design` Step 4 decision entries):
1. Where the last `seq` lives. Chosen: a local variable in `subscribe()` passed to `_stream_once` as a parameter. Alternative: an instance attribute (would also resume across separate `subscribe()` calls, but adds hidden mutable state and an unspecified cross-call semantic). Compatibility: neither changes a public signature; `_stream_once` is private.
2. When to record it. Chosen: after the generator resumes from the `yield` (the consumer asked for the next event), as `max(last, event.seq)`. Alternative: before the `yield` (risks losing an event the consumer never finished receiving). Resulting delivery toward the consumer is at-least-once across a mid-handoff failure, exactly-once in the normal gap case.
3. Resume input. Chosen: `since_seq` only. `Last-Event-ID` is not sent: it has the lowest precedence, it triggers the server's 412 stale check against the current max seq, and `since_seq` is exact. Chosen: send `since_seq` only when at least one event was processed, so the first connection keeps today's behavior (server may still apply a persisted offset or start at the live edge).
4. `consumer_id` source. Chosen: a required-in-practice string field `consumer_id: str = ""` on the existing dataclass, validated non-empty in `EventBusSubscriber.__init__` (UNK-02). Alternative: auto-generate and persist an id (rejected: a grant must name a known id, and persistence is out of scope). Compatibility: adding a defaulted field keeps existing constructor calls valid at the dataclass level; the subscriber itself now refuses an empty value, which is a deliberate behavior change for the only callers (tests).
5. 409 handling. Chosen: catch `httpx.HTTPStatusError` with status 409 ahead of the generic `httpx.HTTPError` branch in `subscribe()`, log a distinct warning naming the `consumer_id`, then share the same attempt counter, `asyncio.sleep(reconnect_delay_sec)` and exhaustion path as the generic branch (extract the shared tail, do not duplicate it). Alternative: fail immediately on 409 (rejected: the old connection normally vanishes within the server's disconnect polling interval, and the Issue allows wait-and-retry). Alternative: a longer 409-specific wait (rejected: the Issue's constraint forbids changing the retry budget).

Interfaces: no public function signature changes; one new dataclass field; one new `ValueError` at construction; `since_seq` query parameter added to `GET /subscribe` calls after the first event.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add `consumer_id` to the `config` fixture, rewrite the two uuid-asserting tests, add the gap-event, no-`since_seq`-first-connect, 409 retry, 409 exhaustion, empty-id and counter-reset tests (REQ-001..REQ-005; `tests/agent/test_eventbus_subscriber.py`). Run the file to see the new tests fail for the right reason.
2. **Phase 2: Subscriber implementation**
   - [ ] Add the `consumer_id` field and the construction-time check; remove `uuid`; keep the last processed `seq`; send `consumer_id` and `since_seq` from `_stream_once`; add the 409 branch sharing the existing retry tail; update the module docstring and the `subscribe` docstring (REQ-001, REQ-002, REQ-003, REQ-004, REQ-007; `scripts/agent/eventbus_subscriber.py`). Keep the first docstring line of each class unchanged so generated references do not drift.
3. **Phase 3: Documentation**
   - [ ] Correct the "EventBus Client Modules" paragraph to the stable `consumer_id` and `since_seq` resume (REQ-006; `docs/23_agent/agent_02_runtime-architecture.md`); run the docs checkers named in Documentation Impact.
4. **Phase 4: Deployment and verification**
   - [ ] Run the Validation plan commands. Hand off to `skills/deploy/SKILL.md` for the `scripts/` change: prerequisite is that the change is committed and pushed first, and deploying is the user's decision (approval gate); the code is not wired into any service, so deployment has no runtime effect until the future wiring task (REQ-007; `scripts/agent/eventbus_subscriber.py`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_eventbus_subscriber.py` | Unit, fake `httpx` stream backed by an in-memory event list honoring `since_seq` | `uv run pytest tests/agent/test_eventbus_subscriber.py` | All pass, including the gap-event test (exactly `[1, 2]`) |
| Server-side resume (read-only) | Existing integration tests, unchanged | `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_restart_resume.py` | Pass (no server file changes) |
| `scripts/agent/eventbus_subscriber.py` | Static checks | `uv run ruff check scripts/agent/eventbus_subscriber.py tests/agent/test_eventbus_subscriber.py`, `uv run ruff format --check` on both, `uv run mypy`, `uv run bandit -r scripts/agent/eventbus_subscriber.py -c pyproject.toml` | No findings |
| `scripts/agent/eventbus_subscriber.py` | Complexity/size baseline | `uv run radon cc scripts/agent/eventbus_subscriber.py -s`, `uv run python tools/check_module_size.py` | No rank worse than the current B for `_stream_once`; size gate passes |
| Coverage of the changed lines | Diff-scoped coverage per `rules/toolchain.md` section 7 | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` after producing `coverage.xml` as that section describes | At least 90% on changed lines (the baseline number is to be recorded then; no coverage run was made while planning) |
| Generated references | Drift check | `uv run python tools/generate_reference_table.py --check` | No drift (first docstring lines kept) |
| `docs/23_agent/agent_02_runtime-architecture.md` | Docs checkers | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` | Pass |
| Scope guard | Negative check | `git diff --stat` and `rg "eventbus_subscriber" scripts/` | No change under `scripts/eventbus/`, `registry/manifests/eventbus_api.yaml`, `factory.py`, `startup*.py`; no importer |

## Risks
- **Risk** (likelihood: Medium): With a stable `consumer_id`, a reconnect can meet HTTP 409 until the server notices the old connection is gone (disconnect polling about 1 second, idle timeout 60 seconds by default), and the unchanged budget (5 attempts, 1 second apart) may be shorter than that → **Mitigation**: the 409 path retries inside the budget and surfaces `EventBusStreamError` chained to the 409; the budget can be raised by the existing `max_reconnect_attempts` and `reconnect_delay_sec` config fields without a code change; the constraint forbids changing the defaults here; record observed timing when the wiring task integrates against a real broker.
- **Risk** (likelihood: Medium): Residual loss window: with no event processed yet (or after a restart / new `subscribe()` call) no `since_seq` is sent and the server falls back to a persisted offset that only ACKs advance → **Mitigation**: documented as UNK-03 and in the Assumptions; the Plan does not claim cross-restart resume; the owner decides on ACK or persisting `seq` before wiring.
- **Risk** (likelihood: Low): The existing broad retry also retries non-recoverable statuses (401, 403, 412) and a clean stream end reconnects immediately without a delay, which a stable `consumer_id` can turn into repeated 409s → **Mitigation**: unchanged behavior is out of scope (retry budget constraint); the clean-end path is exercised by the new 409 tests, and any change is a separate Issue.
- **Risk** (likelihood: Low): Rewriting two existing tests could weaken coverage of the reconnect path → **Mitigation**: the replacements assert the stable id on both requests, and TEST-1 and TEST-7 add stronger reconnect coverage; diff-cover gate at 90%.
- **Risk** (likelihood: Low): `docs/23_agent/agent_02_runtime-architecture.md` is high-churn (22 commits in 30 days), so the one-paragraph edit may conflict with parallel documentation work → **Mitigation**: keep the edit to the single sentence; `tools/check_plan_target_overlaps.py` found no other active Frozen Plan targeting it; re-run it before implementation.
- **Risk** (likelihood: Low): Someone wires the subscriber before UNK-01 and the grant are settled, and the broker answers 403 → **Mitigation**: REQ-007 keeps the wiring out of scope; the construction-time check (REQ-001) makes a missing id an immediate local error rather than a runtime 403 or 400.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Tests first in `tests/agent/test_eventbus_subscriber.py` | In Progress | — | — |  |
| 2 | Phase 2: Subscriber implementation in `scripts/agent/eventbus_subscriber.py` | In Progress | — | — |  |
| 3 | Phase 3: Documentation correction in `docs/23_agent/agent_02_runtime-architecture.md` | In Progress | — | — |  |
| 4 | Phase 4: Verification and deploy hand-off (`scripts/agent/eventbus_subscriber.py`) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261103-235225_01_scripts_agent_eventbus_subscriber.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261103-235225_03_docs_23_agent_agent_02_runtime-architecture.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180343_ebreconnect001_event-bus-reconnect-drops-missed-events.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-152158
- **Related target files**: scripts/agent/eventbus_subscriber.py, tests/agent/test_eventbus_subscriber.py, docs/23_agent/agent_02_runtime-architecture.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (stable `consumer_id`), Acceptance Criteria 2; `uuid.uuid4().hex` in `subscribe` | `scripts/agent/eventbus_subscriber.py` | Step 2 | AC-2, AC-5 | TEST-2, TEST-6 | Confirmed by repository evidence |
| REQ-001 | Same; existing uuid-asserting tests in the test file | `tests/agent/test_eventbus_subscriber.py` | Step 1 | AC-2, AC-5 | TEST-2, TEST-6 | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (track `seq`, send `since_seq`); `_parse_sse_lines` parses but nothing stores `seq` | `scripts/agent/eventbus_subscriber.py` | Step 2 | AC-1, AC-6 | TEST-1, TEST-3 | Confirmed by repository evidence |
| REQ-002 | Issue Testing Expectations (gap-event test) | `tests/agent/test_eventbus_subscriber.py` | Step 1 | AC-1, AC-6 | TEST-1, TEST-3 | Explicit in issue |
| REQ-003 | Issue Required Changes (409 handling), Unresolved Questions; `ConsumerAlreadyConnectedError` to 409 in `subscribe_route.py` | `scripts/agent/eventbus_subscriber.py` | Step 2 | AC-3 | TEST-4, TEST-5 | Derived from confirmed evidence |
| REQ-003 | Same | `tests/agent/test_eventbus_subscriber.py` | Step 1 | AC-3 | TEST-4, TEST-5 | Derived from confirmed evidence |
| REQ-004 | Issue Constraints and Acceptance Criteria 3 (retry budget unchanged) | `scripts/agent/eventbus_subscriber.py` | Step 2 | AC-4 | TEST-5, TEST-7 | Explicit in issue |
| REQ-004 | Same | `tests/agent/test_eventbus_subscriber.py` | Step 1 | AC-4 | TEST-5, TEST-7 | Explicit in issue |
| REQ-005 | Issue Required Changes (test) and Testing Expectations | `tests/agent/test_eventbus_subscriber.py` | Step 1 | AC-1 to AC-5 | TEST-1 to TEST-7 | Explicit in issue |
| REQ-006 | Issue Documentation Impact; stale phrase in `agent_02_runtime-architecture.md` | `docs/23_agent/agent_02_runtime-architecture.md` | Step 3 | AC-7 | `check_docs_consistency.py --domain agent` and the docs checkers | Derived from confirmed evidence |
| REQ-007 | Issue Constraints and Out of Scope | `scripts/agent/eventbus_subscriber.py` | Step 2, Step 4 | AC-8 | Scope guard row of the Validation plan | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-235225 -->