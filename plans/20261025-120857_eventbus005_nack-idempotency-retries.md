## Goal
- Define one NACK idempotency key contract from the caller through the HTTP route to durable delivery state so that a retry of the same delivery attempt does not increment the per-consumer failure counter again, and make the repository guard live instead of being dead because the route mints a fresh UUID per request.

## Priority
High

## Scope
- **In-Scope**:
  - Replace the per-request `uuid.uuid4()` in `_nack_and_promote()` with a caller-supplied idempotency key passed unchanged to `nack_event()`.
  - Define the delivery-attempt identity contract (client-generated stable key, and optionally a server-issued attempt identifier on the SSE stream) so a client can produce a key that is stable across retries of one NACK call.
  - Define and document the deduplication scope: which keys are remembered per `(consumer_id, event_id)` — the latest key only, or a bounded set of recent keys — and implement it in `delivery_repo.py`.
  - Decide and document the behavior for a NACK request without a key (reject 400 or server-derived key) and for the unreachable `consumer_id=None` repository path (internalize or remove).
  - If a storage change is adopted for a bounded key set, add it and bump `PRAGMA user_version` (the database is recreated, never migrated).
  - Update the ACK/NACK endpoint contract, the idempotency-key scope/retention, and the delivery-attempt definition in the docs and ADR-006; add tests for every acceptance criterion.
- **Out-of-Scope**:
  - DLQ requeue (memo task H-01) and ACK semantics.
  - Changing the DLQ promotion rule (INV-13) or the per-consumer failure-counter semantics beyond idempotency.
  - Any client implementation (none exists in this repository; the contract is for external subscribers).
  - Lazy loading of the Step 0 mandatory-load set — no action required (fixed load absorbed by prompt cache, user decision 2026-10-24).
- **Dependencies**:
  - Related memo task H-01 (DLQ promotion) and L-01 (stale ACK/NACK comments). No open issue under `issues/` overlaps.
  - Owner decisions on the three unknowns below gate implementation; they are recorded, not guessed.

## Background
Confirmed against HEAD (adversarial re-verification):
- `scripts/eventbus/ack_route.py::_nack_and_promote()` (lines 157-206) generates `attempt_id = str(uuid.uuid4())` inside the function body on every request and passes it as `last_nack_attempt` to `nack_event()`.
- `scripts/eventbus/delivery_repo.py::nack_event()` (lines 37-143) suppresses a repeat only when the stored `consumer_last_nack_attempt` equals the new key (lines 86-108). A UUID per request never matches, so the guard is dead and every NACK increments `consumer_delivery_failure_count`.
- Storage holds one key per `(consumer_id, event_id)` row (single column `consumer_last_nack_attempt` in `scripts/eventbus/schema.sql:27`). Even with a caller-supplied key, only a repeat of the most recent attempt is deduplicated: `NACK(A)`, `NACK(B)`, `NACK(A retry)` increments the count a second time for A. The memo's "retention and replay-window semantics" therefore has a concrete current limit of one remembered key.
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md:59` documents the intended contract ("Duplicate NACK (same delivery attempt) → 200, No-op: a NACK repeating the stored `consumer_last_nack_attempt` leaves counters unchanged"), which the implementation violates.
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md:278` tracks this as **EVENTBUS-023** ("a repeated NACK request is counted again; the route generates a new attempt identifier per request"); governance_03 Part 1 (`docs/00_governance/governance_03_issue-and-uncertainty-management.md:174`).
- `subscribe_route.py` emits only `id:{seq}` and `data:{json(payload)}` where the payload is `_row_to_dict(row)` over `seq, event_id, topic, payload, producer, published_at` — no delivery-attempt identifier. A client cannot currently generate a stable key for a retry.
- No NACK client exists under `scripts/` (grep outside `scripts/eventbus/` finds nothing).
- `nack_event()` still accepts `consumer_id=None`; the route always requires `consumer_id` (`Query(...)`), so that path is internal-only today and is exercised only by direct repo calls in `test_eventbus_ack_nack.py` (`test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, `test_nack_no_consumer_id_unaffected_by_consumer_acks`).
- `auth.py` registers an `X-Request-Id` middleware that mints a per-request UUID (`request.state.request_id`, line 366); it is per-request by nature and therefore cannot serve as a retry-stable idempotency key.

## Problem
A retry of the same NACK is indistinguishable from a new delivery attempt and increments the failure counter again, moving the event to `max_retry` and the DLQ earlier than intended. The documented duplicate-NACK no-op behavior is not enforced because the route's per-request UUID never matches the repository's single remembered key.

## Reason for Change
Network and proxy retries are normal in an at-least-once system; double counting violates the documented duplicate-NACK behavior (EVENTBUS-023) and prematurely exhausts a consumer's retry budget.

## Implementation Intent
The same delivery attempt reuses the same caller-supplied key; a genuinely new attempt uses a new key. The key is scoped by consumer ID, event ID, and delivery attempt, passed unchanged from the route to the repository, and its retention and replay-window semantics are defined. The repository guard becomes live by comparing the incoming key against the remembered key(s). Whether the key is client-generated or server-issued, whether more than the latest key must be remembered (and thus whether the schema changes), and what a keyless NACK does are owner decisions recorded as unknowns.

## Requirements
- `REQ-001`: One NACK idempotency key contract MUST span caller → route → repository: the same delivery attempt reuses the same key; a new attempt uses a new key. (Acceptance 3)
- `REQ-002`: `_nack_and_promote()` MUST NOT use a per-request `uuid.uuid4()` as the idempotency source; the key passed to `nack_event()` MUST be the caller-supplied key (or an explicitly stated server-derived fallback), passed unchanged. (Problem, Required change 2)
- `REQ-003`: Retrying the same delivery attempt MUST NOT increment `consumer_delivery_failure_count`; a distinct attempt MUST increment it exactly once. (Acceptance 1, 2)
- `REQ-004`: The deduplication scope MUST be defined and implemented — latest remembered key only (single column, no schema change) or a bounded set of recent keys (storage change + `user_version` bump). Owner decision (UNK-03). (Required change 3, Acceptance 4)
- `REQ-005`: The delivery-attempt identity MUST be obtainable by the client — either the server issues an attempt identifier per delivered event (SSE field) or the NACK carries a client-generated stable idempotency key. Owner/design decision (UNK-02). (Required change 1, Acceptance 3)
- `REQ-006`: Behavior for a NACK without a key MUST be decided explicitly (reject with 400, or fall back to a server-derived key). Owner decision (UNK-01). (Constraints)
- `REQ-007`: The `consumer_id=None` repository path MUST be removed or explicitly internalized (unreachable via the route, which requires `consumer_id`). (Required change 4)
- `REQ-008`: A storage change (if adopted) MUST bump `PRAGMA user_version` (the database is recreated, never migrated). (Constraints)

## Implementation Target Files
**Freeze status**: Frozen (set once `issue-to-plan` Step 8's Implementation Target
Files Validation passed — `check_workitem_structure.py` reports No findings;
`check_plan_target_overlaps.py` reports one cross-plan overlap on
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, shared with
`plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`. Non-contradictory:
Issue 4 records INV-01/EVENTBUS-022 and Issue 5 closes EVENTBUS-023 — additive edits to
different sections of the same ADR; sequence the two implementations so they do not
rewrite the same region concurrently. Every row is `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/ack_route.py` | `_nack_and_promote()`: drop per-request UUID; accept an idempotency key from the query; pass it unchanged to `nack_event()`; apply the UNK-01 fallback if chosen | Removes the dead-key source; wires the caller key through (REQ-001, REQ-002); enforces UNK-06 (REQ-006) | REQ-001, REQ-002, REQ-006; Acceptance 3 | `_nack_and_promote()` ack_route.py:157-206 (UUID at 166); `/nack` ack_route.py:124-137 | `tests/eventbus/test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_dlq_promotion.py`, `test_eventbus_auth.py` | Verified |
| `scripts/eventbus/delivery_repo.py` | `nack_event()`: enforce the defined dedup scope (latest key or bounded set); internalize/remove the `consumer_id=None` path (REQ-007) | Makes the guard live; implements REQ-004/REQ-007 | REQ-003, REQ-004, REQ-007; Acceptance 1, 2, 4 | `nack_event()` delivery_repo.py:37-143 (guard 86-108); single column delivery_repo.py:116-122 | `tests/eventbus/test_eventbus_ack_nack.py` | Verified |
| `scripts/eventbus/subscribe_route.py` | Optionally emit a delivery-attempt identifier in the SSE stream (only if the server-issued model, UNK-02, is chosen) | Gives the client a server-assisted attempt identity if that model is adopted | REQ-005; Acceptance 3 | SSE emission subscribe_route.py:188-192, 258-261 (`id:{seq}`, `data:{json}`) | `tests/eventbus/test_eventbus_subscribe.py` | Verified |
| `scripts/eventbus/schema.sql` | Conditional: add a bounded per-`(consumer_id,event_id)` key store AND bump `PRAGMA user_version` (1→2) ONLY IF the bounded-set model (UNK-03) is adopted | Storage for remembering >1 key; DB is recreated, never migrated (REQ-008) | REQ-004, REQ-008; Acceptance 4 | `consumer_delivery` + `consumer_last_nack_attempt` schema.sql:22-27; `PRAGMA user_version = 1` schema.sql:43 | `tests/db/test_create_schema.py` | Verified |
| `tests/eventbus/test_eventbus_ack_nack.py` | Repo-level idempotency tests: same key repeated sequentially and concurrently, retry after simulated timeout, different keys, boundary at `max_retry - 1`; update `consumer_id=None` tests if REQ-007 removes that path | Covers Acceptance 1, 2, 4 at the repository layer | REQ-003, REQ-004, REQ-006; Acceptance 1, 2, 4 | existing `test_nack_event_increments_failure_count`/`_again`/`_no_consumer_id` test_eventbus_ack_nack.py:340-475 | this file | Verified |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | HTTP-level idempotency: same key repeat returns no-op 200; distinct attempt increments once; boundary case; keyless handling per UNK-01 | Covers Acceptance 1, 2, 4 at the route layer | REQ-002, REQ-006; Acceptance 1, 2, 4 | ACK/NACK endpoint tests test_eventbus_ack_endpoint.py | this file | Verified |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Document the NACK idempotency key contract, key scope, and retention/replay window; reconcile the `eventbus_12:59` no-op table with the fixed behavior | Canonical ops contract for subscribers | REQ-001, REQ-004, REQ-005; Acceptance 3, 4 | duplicate-NACK table eventbus_12:59 | N/A | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Record the idempotency invariant and retention policy; close EVENTBUS-023 (ADR-006:278) | Canonical governance record | REQ-003, REQ-004; Acceptance 1, 2 | EVENTBUS-023 adr_02_04_006:278 | N/A | Verified |

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
- `schema.sql` is a conditional row: it is modified only if the bounded-set model is
  adopted (UNK-03). If the latest-key-only model is chosen, this row stays unmodified
  and the schema is unchanged.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/db.py` | Facade re-export of `nack_event`; needed to know the public signature surface and how the route imports it | `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`; REQ-002 |
| `scripts/eventbus/dlq.py` | `is_promotable`/`promote_single` used by `_nack_and_promote()`; preserve INV-13 promotion semantics | `scripts/eventbus/ack_route.py`; REQ-003 |
| `scripts/eventbus/auth.py` | `X-Request-Id` middleware (per-request UUID); read to confirm the idempotency key must be decoupled from request identity | `scripts/eventbus/ack_route.py`; REQ-001 |
| `scripts/eventbus/_constants.py` | Column constants used by `nack_event()` (`_COL_CONSUMER_LAST_NACK_ATTEMPT`, `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`) | `scripts/eventbus/delivery_repo.py`; REQ-004 |
| `implementations/done/20261022-145114_04_scripts_eventbus_ack_route_py.md` | Most recent implementation record for `ack_route.py` context | `scripts/eventbus/ack_route.py`; Background |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | EVENTBUS-023 tracking (Part 1); confirms scope and that deploy/readiness gaps are separate | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; Scope |

## Acceptance Criteria
- Retrying the same delivery attempt does not increment the counter and a distinct attempt increments it exactly once (REQ-003; Acceptance 1).
- Duplicate retries cannot accelerate DLQ promotion (REQ-003; Acceptance 2).
- API, client contract, route, repository, documentation and tests use the same idempotency key contract (REQ-001; Acceptance 3).
- The documented retention window is tested at its boundary (for example `NACK(A)`, `NACK(B)`, `NACK(A retry)` behaves exactly as the contract states) (REQ-004; Acceptance 4).
- A keyless NACK behaves as decided and documented (UNK-01) (REQ-006).
- If a storage change is adopted, `PRAGMA user_version` is bumped and the DB recreation is reflected (REQ-008).

## Tests
- Same key repeated sequentially: second NACK is a no-op, counter unchanged (REQ-003).
- Same key repeated concurrently: concurrent retries collapse to one increment (REQ-003).
- Retry after a simulated timeout: a retried attempt within the retention window is deduplicated (REQ-004).
- Different keys: each distinct key (distinct attempt) increments exactly once (REQ-003).
- Duplicate at `max_retry - 1`: a duplicate does not push the consumer over the promotion threshold; a distinct one does (REQ-003; Acceptance 2).
- Boundary of the retention window: the sequence `NACK(A)`, `NACK(B)`, `NACK(A retry)` behaves exactly as the documented scope states (REQ-004; Acceptance 4).
- Keyless NACK: behavior matches UNK-01 (reject 400 or server-derived key) (REQ-006).
- Then ruff and mypy.

## Documentation Impact
Yes. The NACK endpoint contract, the idempotency key scope and retention, and the delivery-attempt definition must be documented. Target docs named via `docs/00_index.md` / `routing.md` Docs mapping:
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` — NACK idempotency key contract, key scope, retention/replay window (reconcile the `eventbus_12:59` no-op table). Drives REQ-001, REQ-004, REQ-005.
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` — idempotency invariant + retention policy; close EVENTBUS-023. Drives REQ-003, REQ-004.
No deployment-script documentation is in scope.

## Assumptions
- The idempotency key identifies a delivery attempt and is stable across network/proxy retries of one logical NACK; the client owns or echoes it.
- A client-generated key can be derived from `(consumer_id, event_id, attempt_number)` or be a client-stored UUID reused across retries; the server treats any non-empty key opaquely.
- The single column `consumer_last_nack_attempt` suffices for "latest key only" dedup with no schema change; a bounded set of recent keys needs a new store and a `user_version` bump.
- `deploy.sh` rsyncs `scripts/` and `docs/` wholesale to `/opt/llm/`, so every target row's `deploy.sh Impact` is "not applicable (rsynced)".
- The three owner decisions (UNK-01/02/03) are mutually consistent: the chosen key origin (UNK-02) and dedup scope (UNK-03) together define what "same delivery attempt" means.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What happens to a NACK request without a key: reject with 400, or fall back to a server-derived key? | Owner availability; no existing policy in repo | Owner decision; documented in `eventbus_12`; non-blocking sign-off gate before implementation (per `rules/coding.md` Explicit sign-off gates) | True |
| UNK-02 | Where does the client obtain the attempt identity: server-issued SSE field versus client-generated key? | Trade-off between server-assisted identity and client responsibility; no client in repo to constrain | Design decision; recorded in design; drives `subscribe_route.py` change (or none) | False |
| UNK-03 | Must retries of an older attempt (`NACK(A)`, `NACK(B)`, `NACK(A retry)`) be deduplicated, or only the latest? Decides whether the schema changes. | Product expectation for out-of-order retries; current storage remembers one key | Owner decision; latest-only = no schema change; bounded set = schema change + `user_version` bump (REQ-008) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/ack_route.py` | `_nack_and_promote()` key source + query param; optional keyless handling | `/nack` exercised by 3 test files; 1 prod caller of `nack_event` | 10 (last change 2026-10-23) | N/A (git-fame unavailable) | not applicable (rsynced) |
| `scripts/eventbus/delivery_repo.py` | `nack_event()` dedup scope + `consumer_id=None` handling | 1 prod caller (route via facade); repo also used by offset/replay | 16 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `scripts/eventbus/subscribe_route.py` | Optional SSE delivery-attempt field | SSE consumers external to repo; no internal caller of the payload shape | 3 (last change 2026-10-09) | N/A | not applicable (rsynced) |
| `scripts/eventbus/schema.sql` | Conditional bounded key store + `user_version` bump | DB recreated on bump; only affects fresh eventbus DB | 0 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_ack_nack.py` | Repo-level idempotency tests; update `consumer_id=None` tests if removed | Test-only | 14 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | HTTP-level idempotency tests | Test-only | 7 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | NACK contract + retention doc | Doc-only | 0 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Idempotency invariant + EVENTBUS-023 close | Doc-only | 0 | N/A | not applicable (rsynced) |

Baseline complexity (radon): `nack` = B (8); `nack_event` = C (12); `_do_ack` = C (12).
bandit reports only `B101 assert_used` (Low, contract-invariant asserts); vulture is
clean. Keep `nack_event()` complexity at or below baseline when adding a bounded-key
read path.

## Design
**North star (REQ-003):** a NACK that retries the same delivery attempt is a no-op on the
per-consumer failure counter; a genuinely new attempt increments it exactly once. The
repository guard becomes live by comparing the incoming key against the remembered
key(s) per `(consumer_id, event_id)`.

**Key origin (UNK-02) — recommended: client-generated stable key.**
- The client generates/holds an idempotency key identifying the delivery attempt and
  sends it on every NACK (e.g. a query parameter such as `attempt_id` or
  `idempotency_key`). A retry of the same failed attempt reuses the same key; advancing
  to a new attempt uses a new key. The server treats the key opaquely and passes it
  unchanged through `_nack_and_promote()` → `nack_event()`.
- This is robust for network/proxy retries because the key is client-stored, not tied to
  the HTTP request. The `auth.py` `X-Request-Id` middleware is per-request and MUST NOT
  be used as the idempotency key (each retry is a new request with a new request-id).
- Optional server-assisted variant: if the owner wants the server to drive identity,
  `subscribe_route.py` emits an `attempt_id` in each SSE event (JSON field and/or a
  separate SSE `id:` namespace); the client echoes it on NACK. This distinguishes
  sequential attempts but does not by itself dedup a raw HTTP retry (the client must
  still store it). Recommended only if UNK-02 selects the server-issued model.

**Dedup scope (UNK-03) — two options:**
1. **Latest key only (no schema change).** The single column `consumer_last_nack_attempt`
   is compared against the incoming key. With a well-formed client whose key encodes the
   attempt number, a retry of attempt N always sends key-N (deduped) and attempt N+1 sends
   key-N+1 (counted once). The pathological `NACK(A)`, `NACK(B)`, `NACK(A retry)` sequence
   only arises from a client sending arbitrary keys; the contract defines it as "a
   non-latest key counts as a new attempt." This matches the currently documented
   `eventbus_12:59` behavior and requires NO schema change. **Recommended default.**
2. **Bounded set of recent keys (schema change).** Remember the last K keys per
   `(consumer_id, event_id)` (new table `consumer_nack_keys(consumer_id, event_id,
   nack_attempt)` or a bounded JSON column) so an out-of-order retry of a recent attempt
   is still deduped. Requires bumping `PRAGMA user_version` (1→2); the DB is recreated,
   never migrated (REQ-008). Adopt only if the owner explicitly wants out-of-order retry
   deduplication.

**Keyless NACK (UNK-01):** decide and document — reject with 400, or derive a server key
(e.g. `f"{consumer_id}:{event_id}:{current_attempt}"`) and treat it as the latest key.
If rejected, the route validates key presence before calling the repository.

**`consumer_id=None` path (REQ-007):** the route requires `consumer_id`, so the None path
is unreachable in production. Two acceptable outcomes (owner preference): (a) keep it and
mark it internal-only with an explicit comment (minimal change; the 3 direct-repo tests
stay valid), or (b) remove it and update those 3 tests to supply a `consumer_id`. Both
satisfy REQ-007; (a) is the lower-risk default.

**Import-linter:** `eventbus-is-isolated` is KEPT (verified above). No file crosses into
`shared/`; a conditional new schema table stays within the eventbus database.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Route — pass the caller key through**
   - [ ] In `scripts/eventbus/ack_route.py`, read the idempotency key from the NACK query (per UNK-02); apply the UNK-01 keyless handling (validate presence for 400, or server-derived fallback). (REQ-002, REQ-006; `scripts/eventbus/ack_route.py`)
   - [ ] Replace the per-request `uuid.uuid4()` in `_nack_and_promote()` with the caller key and pass it unchanged to `nack_event(last_nack_attempt=key)`. (REQ-001, REQ-002; `scripts/eventbus/ack_route.py`)
2. **Phase 2: Repository — make the guard live**
   - [ ] In `scripts/eventbus/delivery_repo.py`, enforce the chosen dedup scope in `nack_event()`: latest-key comparison, or a bounded-key read + membership check if UNK-03 selects the storage change. (REQ-003, REQ-004; `scripts/eventbus/delivery_repo.py`)
   - [ ] If UNK-03 selects a storage change, add the key store to `scripts/eventbus/schema.sql` and bump `PRAGMA user_version` (REQ-008; `scripts/eventbus/schema.sql`).
   - [ ] Resolve the `consumer_id=None` path: internalize with an explicit comment, or remove and update the 3 direct-repo tests (REQ-007; `scripts/eventbus/delivery_repo.py`).
3. **Phase 3: SSE identity (only if UNK-02 selects the server-issued model)**
   - [ ] Emit a delivery-attempt identifier in `scripts/eventbus/subscribe_route.py` SSE output. (REQ-005; `scripts/eventbus/subscribe_route.py`)
4. **Phase 4: Tests**
   - [ ] Add repo-level idempotency tests to `tests/eventbus/test_eventbus_ack_nack.py` (sequential/concurrent/timeout/different-keys/boundary); update `consumer_id=None` tests if removed. (REQ-003, REQ-004, REQ-006; `tests/eventbus/test_eventbus_ack_nack.py`)
   - [ ] Add HTTP-level idempotency tests to `tests/eventbus/test_eventbus_ack_endpoint.py` (same-key no-op, distinct-once, boundary, keyless handling). (REQ-002, REQ-006; `tests/eventbus/test_eventbus_ack_endpoint.py`)
5. **Phase 5: Documentation**
   - [ ] Document the NACK idempotency key contract, key scope, and retention window in `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; reconcile the no-op table. (REQ-001, REQ-004, REQ-005; `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`)
   - [ ] Record the idempotency invariant + retention policy and close EVENTBUS-023 in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`. (REQ-003, REQ-004; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
6. **Phase 6: Validation**
   - [ ] Run ruff, mypy, bandit, vulture, lint-imports, and the affected test files; confirm no double counting and INV-13 promotion unchanged. (Acceptance 1-4)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/delivery_repo.py` | Unit: same key repeat (sequential + concurrent), different keys, timeout retry, boundary at `max_retry - 1` | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Same-key repeat = no-op; distinct key = +1; no DLQ acceleration |
| `scripts/eventbus/ack_route.py` | Integration: HTTP `/nack` with repeated vs distinct keys; keyless handling | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_dlq_promotion.py tests/eventbus/test_eventbus_auth.py` | Repeated key = 200 no-op; distinct = counted once; keyless per UNK-01 |
| `scripts/eventbus/schema.sql` (if changed) | Schema creation + `user_version` bump | `uv run pytest tests/db/test_create_schema.py` | New store present; `user_version` bumped to 2 |
| `scripts/eventbus/*` | Static: complexity, dead code, security | `uv run radon cc scripts/eventbus/ack_route.py scripts/eventbus/delivery_repo.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `nack_event` complexity ≤ C(12); bandit/vulture clean |
| Import boundaries | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Types / format | Quality gates | `uv run mypy`, `uv run ruff` | Pass |

## Risks
- **Risk**: Changing the NACK signature (requiring a key) breaks the 3 `/nack` test files and any external caller not yet updated. → **Mitigation**: blast radius measured (3 test files); keyless handling (UNK-01) preserves backward compatibility until the contract is enforced; contract documented for external subscribers.
- **Risk**: A bounded-key storage change (UNK-03) bumps `user_version`, recreating the eventbus DB and losing data. → **Mitigation**: adopt only with explicit owner sign-off; schema change path documented with the recreation consequence (REQ-008).
- **Risk**: `nack_event()` complexity grows beyond C(12) when adding a bounded-key read path. → **Mitigation**: keep the latest-key-only default (single read); isolate the bounded-set read behind the UNK-03 branch.
- **Risk**: Removing the `consumer_id=None` path (REQ-007) breaks the 3 direct-repo tests. → **Mitigation**: default to internalize-with-comment (lower risk); removal path includes the 3 test updates.
- **Risk**: Conflating `X-Request-Id` with the idempotency key would make dedup impossible (each retry has a new request-id). → **Mitigation**: design explicitly decouples the two; `auth.py` is a reference file, not modified unless the server-issued model requires a separate stable header.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: route passes caller key through (drop UUID, UNK-01 keyless handling) | Pending | — | — | Sign-off gate on UNK-01/UNK-02 before implementation |
| 2 | Phase 2: repository makes guard live (dedup scope UNK-03; internalize/remove `consumer_id=None`) | Pending | — | — | |
| 3 | Phase 3: SSE delivery-attempt identity (only if UNK-02 selects server-issued model) | Pending | — | — | No `subscribe_route.py` change under recommended model |
| 4 | Phase 4: repo- and HTTP-level idempotency tests | Pending | — | — | |
| 5 | Phase 5: document NACK contract, key scope, retention; close EVENTBUS-023 | Pending | — | — | |
| 6 | Phase 6: ruff/mypy/bandit/vulture/lint-imports + affected test runs | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: keyless-NACK behavior is an owner decision (sign-off gate) | — | — |
| 3 | UNK-02/UNK-03: key origin and dedup scope are owner decisions gating `subscribe_route.py`/`schema.sql` | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-120857
- **Related target files**: `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_ack_endpoint.py`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary; Required change 1; Acceptance 3 | `scripts/eventbus/ack_route.py`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | 1, 5 | One key contract caller→route→repo | Contract doc review; endpoint test | Draft |
| REQ-002 | Problem; Required change 2; Acceptance 2 | `scripts/eventbus/ack_route.py` | 1 | No per-request UUID as key source | Endpoint same-key no-op test | Draft |
| REQ-003 | Problem; Acceptance 1, 2 | `scripts/eventbus/delivery_repo.py`, `tests/eventbus/test_eventbus_ack_nack.py` | 2 | Retry does not increment; distinct increments once | Sequential/concurrent/boundary tests | Draft |
| REQ-004 | Unresolved Q3; Acceptance 4 | `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/schema.sql` (conditional) | 2, 3 | Retention window honored at boundary | `NACK(A)/NACK(B)/NACK(A retry)` boundary test | Draft |
| REQ-005 | Unresolved Q2; Acceptance 3 | `scripts/eventbus/subscribe_route.py`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | 3 | Client can obtain attempt identity | Doc contract; SSE field test (if adopted) | Draft |
| REQ-006 | Unresolved Q1; Constraints | `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_ack_endpoint.py` | 1 | Keyless NACK behaves as decided | Keyless-endpoint test | Draft |
| REQ-007 | Required change 4 | `scripts/eventbus/delivery_repo.py`, `tests/eventbus/test_eventbus_ack_nack.py` | 2 | `consumer_id=None` path internalized/removed | Direct-repo tests updated or retained | Draft |
| REQ-008 | Constraints | `scripts/eventbus/schema.sql` (conditional) | 2 | `user_version` bumped on storage change | `test_create_schema.py` | Draft |
