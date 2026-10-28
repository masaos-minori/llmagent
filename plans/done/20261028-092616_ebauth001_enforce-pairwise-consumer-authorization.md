## Goal
- Make EventBus consumer authorization honor the configured (consumer_id, topic) pairs for subscribe, ACK and NACK through one shared decision, and stop an omitted `topic` query from widening a restricted consumer's access.

## Priority
High

## Scope
- **In-Scope**:
  - Replace the independent `allowed_consumer_ids` / `allowed_topics` sets on `Principal` with an explicit set of (consumer_id, topic) grants built from both `consumer_authorization` and `topic_authorization`.
  - One shared authorization decision used by subscribe, ACK and NACK; remove the duplicated partial checks in `subscribe_route.py`.
  - Bind the requested `consumer_id` and the topic of the targeted event into the ACK and NACK decision.
  - Define and implement the omitted-`topic` behavior for subscribe (narrow to the consumer's authorized topics).
  - Keep control-plane credentials without implicit consumer authorization; keep the runtime update path (`POST /admin/topics/authorization`) consistent.
  - Update tests, ADR-013 prose that is not a Decision/Invariant, and the EventBus docs.
- **Out-of-Scope**: token roles and the credential config format; consumer-ID uniqueness across principals; rate limiting; audit changes; wildcard topic matching.
- **Dependencies**: N/A: none blocking. `issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md` and `issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md` also name `scripts/eventbus/app.py`; Step 8b overlap check decides ordering once those Plans exist.

## Background
`consumer_authorization` maps consumer_id to topics and `topic_authorization` maps topic to consumer_ids. The principal builder in `scripts/eventbus/auth.py` flattens both mappings into one set of consumer IDs and one set of topics held by the single CONSUMER-role token. ADR-013 INV-02 states a caller MUST NOT act as another consumer_id or access an unauthorized topic.

## Problem
- With `consumer-a -> topic-a` and `consumer-b -> topic-b`, the token is authorized for `consumer-a` on `topic-b` because the relationship is lost.
- `subscribe_route.subscribe` validates only requested topics. With no `topic` query the loop does not run, and `EventBroker.subscribe` treats `topics=[]` as all topics, so a restricted consumer receives every topic (live and replay).
- ACK and NACK check only `consumer_id` membership; the topic of the acknowledged event is never checked. The `topics` parameter of `require_consumer_identity` is bound as a JSON request body on those two POST routes (OpenAPI shows a request body), not as a query parameter, so it is caller-supplied and never derived from the event.

## Reason for Change
The authorization is broader than the configuration expresses on an authenticated endpoint, a security-boundary defect against ADR-013 INV-02. Severity is set by the boundary violation.

## Implementation Intent
Represent the grant as explicit (consumer_id, topic) pairs on `Principal` and evaluate subscribe, ACK and NACK through one function in `auth.py`. Routes stop re-deriving authorization after the dependency approved the request. Missing input fails closed or is narrowed to what the pair set allows, and the choice is documented.

## Requirements
- `REQ-001`: `Principal` holds (consumer_id, topic) grants built from the union of the pairs in `consumer_authorization` and `topic_authorization`; the independent sets are removed. Non-consumer principals hold no grants (deny-all).
- `REQ-002`: Subscribe without a `topic` query for a restricted principal is narrowed to the topics granted to the requested `consumer_id`; when that set is empty the request is rejected with HTTP 403. The decision is documented.
- `REQ-003`: Subscribe, ACK and NACK use one shared authorization function; `subscribe_route.py` no longer re-checks consumer_id or topic itself.
- `REQ-004`: ACK and NACK authorize the pair (query `consumer_id`, topic of the event named by `event_id`); a caller-supplied `topics` body is no longer an input. An `event_id` that does not exist keeps its existing not-found behavior.
- `REQ-005`: The shared `auth_token` and `admin_token` and every non-consumer role hold no consumer grants and cannot subscribe, ACK or NACK.
- `REQ-006`: `POST /admin/topics/authorization` repopulates principals with the same pairwise semantics (no code path builds sets separately).
- `REQ-007`: Existing semantics are preserved: empty mappings are deny-all, a consumer token without `consumer_authorization` is rejected at startup, unauthorized requests return 403 and documented malformed input returns 400.
- `REQ-008`: ADR-013 (non-Decision, non-Invariant text only) and the EventBus docs state the pairwise model, the omitted-topic behavior and the status codes as current behavior.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Principal grant model and shared decision | Replace the two sets with (consumer_id, topic) grants; add the shared authorization function; keep `require_consumer_identity` as the dependency | REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007 / AC-1, AC-2, AC-3 | `_populate_token_maps` builds `ids` and `topics` sets from both mappings; `Principal.allowed_consumer_ids` / `allowed_topics`; `require_consumer_identity` checks them independently (checked in Step 3) | `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py` | Verified |
| `scripts/eventbus/subscribe_route.py` | Subscribe route | Remove the duplicated consumer_id/topic checks; apply the narrowed topic list to the broker subscription and the replay query | REQ-002, REQ-003 / AC-2 | Checks at the `_identity`, `REQ-011` and `REQ-013` blocks; comment "empty topic list means subscribe to all topics"; `broker.subscribe(list(topic), ...)` (checked in Step 3) | `tests/eventbus/test_eventbus_subscribe.py` | Verified |
| `scripts/eventbus/ack_route.py` | ACK and NACK routes | Look up the event topic and authorize the pair before changing delivery state | REQ-004 / AC-4 | `_do_ack` and `nack` check only a non-empty `consumer_id` and call `ack_event_for_consumer` / `nack_event` (checked in Step 3) | `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_ack_endpoint.py` | Verified |
| `scripts/eventbus/app.py` | Route wiring | Replace `Depends(require_consumer_identity)` on ACK/NACK (it turns `topics` into a request body) with the shared decision; keep `resolve_subscribe_identity` for subscribe | REQ-003, REQ-004 / AC-3, AC-4 | `ack_event` and `nack` declare `_identity: Principal = Depends(require_consumer_identity)`; OpenAPI lists a request body for both routes (checked in Step 3) | `tests/eventbus/test_eventbus_ack_endpoint.py` | Verified |
| `scripts/eventbus/event_repo.py` | Event lookup | Add a read helper returning the topic of an event_id, next to `get_seq` | REQ-004 / AC-4 | `get_seq` is the existing by-event_id lookup; no topic lookup exists (checked in Step 3) | `tests/eventbus/test_eventbus_ack_nack.py` | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Principal construction and decision tests | Move direct `Principal(allowed_consumer_ids=..., allowed_topics=...)` construction to grants; add pairwise cases | REQ-001, REQ-003, REQ-005 / AC-1, AC-3 | `Principal(` with the old fields near the consumer principal setup (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Config-to-principal tests | Update assertions on `allowed_consumer_ids` / `allowed_topics`; add the consumer-a/topic-b matrix | REQ-001, REQ-007 / AC-1 | Assertions on `principal.allowed_consumer_ids` and `allowed_topics` (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_subscribe.py` | Subscribe route tests | Update `Principal(` construction; add omitted-topic tests | REQ-002 / AC-2 | `Principal(` with `allowed_consumer_ids=None` and a topic set (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_ack_nack.py` | NACK/ACK state tests | Update `Principal(` construction; add cross-consumer and cross-topic rejection | REQ-004 / AC-4 | `Principal(` overrides in two fixtures (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | ACK endpoint tests | Update the principal override; add a wrong-topic ACK case | REQ-004 / AC-4 | `Principal(... allowed_consumer_ids=frozenset({"consumer-A"}) ...)` override (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Runtime update tests | Update assertions after repopulation to the pairwise grants | REQ-006 / AC-5 | Assertions on `allowed_consumer_ids` / `allowed_topics` after the admin update (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | ADR-013 | Describe the pairwise grant and omitted-topic behavior in Implementation Notes only; Decisions and Invariants unchanged | REQ-008 / AC-6 | INV-02 and INV-07 already require explicit consumer_id and topic authorization; Decision Details 3 lists the 403 cases (checked in Step 3) | `tools/check_adr_preservation.py` | Verified |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | API reference index | Replace the `allowed_consumer_ids` membership statement with the pairwise rule | REQ-008 / AC-6 | Line stating consumer authorization requires `consumer_id` in `allowed_consumer_ids` (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | ACK/NACK doc | Replace `Principal.allowed_consumer_ids` wording; add the event-topic check and status codes | REQ-008 / AC-6 | Authentication section cites `allowed_consumer_ids`; error table lists only `consumer_id` outside authorization (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated API reference | Refresh the symbol rows for `Principal`, `require_consumer_identity` and any new function | REQ-008 / AC-6 | Rows for `Principal` and `require_consumer_identity` list the current signatures (checked in Step 3) | `tools/generate_reference_table.py --check` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/admin_route.py` | `update_topics_authorization` calls `_populate_token_maps`; confirms the runtime path needs no separate change | REQ-006 |
| `scripts/eventbus/broker.py` | `EventBroker.subscribe` treats `topics=[]` as all topics | REQ-002 |
| `scripts/eventbus/config.py` | Types of `consumer_authorization` (dict[str, list[str]]) and `topic_authorization` (dict[str, set[str]]) | REQ-001 |
| `scripts/eventbus/delivery_repo.py` | `ack_event_for_consumer` and `nack_event` behavior for a missing event_id | REQ-004 |
| `scripts/agent/eventbus_subscriber.py` | Client sends `consumer_id` and sends `topic` only when `topics` is set; relies on the omitted-topic behavior | REQ-002 |
| `config/eventbus.toml` | Documents the two authorization mappings | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-007): Only configured (consumer_id, topic) pairs are accepted; `consumer-a`/`topic-b` and `consumer-b`/`topic-a` are rejected with 403 while `consumer-a`/`topic-a` and `consumer-b`/`topic-b` succeed; empty mappings stay deny-all.
- AC-2 (REQ-002): Omitting `topic` never delivers an event whose (consumer_id, topic) pair is not granted, for live delivery and replay; an empty authorized set returns 403.
- AC-3 (REQ-003, REQ-005): A control-plane credential cannot subscribe, ACK or NACK; `subscribe_route.py` contains no consumer_id or topic membership check of its own.
- AC-4 (REQ-004): ACK and NACK are rejected with 403 for another consumer's ID or for an event whose topic is not granted to that `consumer_id`, and change no delivery state.
- AC-5 (REQ-006): After `POST /admin/topics/authorization`, the pairwise grants of the CONSUMER principal match the new mappings.
- AC-6 (REQ-008): Implementation, tests, ADR-013 and the EventBus docs describe the same contract, and the docs checkers pass.

## Tests
- Unit and route tests for the four-cell consumer/topic matrix (REQ-001, REQ-007).
- Subscribe with no topic query: narrowed live delivery and replay, plus the empty-authorized-set 403 (REQ-002).
- ACK and NACK with another consumer's ID, with a wrong-topic event, and with a nonexistent event_id (REQ-004).
- Control-plane tokens rejected on all three routes (REQ-005).
- Admin runtime update followed by pair assertions (REQ-006).
- Run: `uv run pytest tests/eventbus`; mypy and ruff on changed files; `tools/check_adr_preservation.py`; docs checkers (REQ-008).

## Documentation Impact
Yes (REQ-008). Update the ADR-013 implementation notes and the EventBus ACK/NACK, API index and API reference docs found through `docs/00_index.md` "Document References by Task". State current behavior only.

## Assumptions
- Narrowing an omitted `topic` to the consumer's granted topics satisfies the Issue's "fail closed or explicitly narrowed" requirement and keeps the default `EventBusSubscriberConfig` (`topics=None`) working; UNK-01 records the owner decision.
- The pair set is the union of pairs from both mappings, matching the existing union-apply owner decision for a single CONSUMER token.
- A `consumer_authorization` entry with an empty topic list grants nothing, so that consumer_id is rejected.
- Overlap judgment (compatible): `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py`, but it edits `_shutdown_lifespan` while this Plan edits the ACK/NACK route wiring; the two touch different functions and can land in either order.
- Overlap judgment (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits only the promotion block of `_nack_and_promote` and adds one transition-table row, while this Plan edits authorization at the start of the routes, the Authentication section and the error table.
- Topic matching stays exact; the wildcard-looking examples in `config/eventbus.toml` comments are not matched as patterns today.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner preference for an omitted `topic` query: narrow to granted topics (Plan default) or reject with 400/403 | Owner decision; the Issue lists both as acceptable | Owner confirms before `plan-to-implementation-procedure`; switching changes one function in `auth.py` and one block in `subscribe_route.py` | False |
| UNK-02 | Whether a deployed consumer relies on subscribing without `topic` while holding grants for several topics | No client other than `scripts/agent/eventbus_subscriber.py` found in `scripts/` | Narrowing keeps that behavior inside the granted set; verify the deployed config at deploy time | False |
| UNK-03 | `config/eventbus.toml` comments show topics such as `orders/*`, but matching is exact | Whether wildcard topics are intended | File a separate Issue if wildcard matching is wanted (out of scope here) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Modify | High | 7 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/subscribe_route.py` | Modify | Medium | 3 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Modify | Medium | 11 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Medium | 6 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/event_repo.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_subscribe.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_ack_nack.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (more than 3 files, public/runtime-facing authorization contract). Architecture check: `lint-imports` reports 6 contracts kept, 0 broken; the change stays inside `scripts/eventbus/`. Dependency check: tests construct `Principal(allowed_consumer_ids=..., allowed_topics=...)` in six test files, so the field replacement is a coordinated change; no module outside `scripts/eventbus/` and `tests/eventbus/` reads those fields.
- Decision 1, grant representation: `Principal.consumer_grants: frozenset[tuple[str, str]]` (consumer_id, topic). Alternative (dict consumer_id -> frozenset of topics) was rejected because a flat pair set makes the membership test and test construction one line each. `None` ("unrestricted") is removed; no code builds it today.
- Decision 2, shared decision: one function in `auth.py` taking the principal, the requested `consumer_id` and the topics to check, raising 403 and writing the existing audit records. `require_consumer_identity` stays the FastAPI dependency for subscribe and delegates to it.
- Decision 3, ACK/NACK: the route reads the event's topic with a new `event_repo` helper inside the existing DB-lock path, then calls the shared function. A missing event keeps its current not-found result without a pair check, so a 403 never reveals whether an event exists for a consumer that is not authorized for its topic.
- Decision 4, omitted topic (UNK-01): narrow to topics granted to the requested `consumer_id`; subscribe with an empty granted set returns 403. The narrowed list feeds both `broker.subscribe` and the replay query so live and replayed events agree.
- Compatibility: the ACK/NACK `topics` request body disappears from the OpenAPI schema; no client in `scripts/` sends it.
- Module size: `auth.py` is 15359 B and `subscribe_route.py` 12076 B against the 20480 B gate; `tools/check_module_size.py` confirms after the change.

## Implementation steps
1. **Phase 1: Grant model and shared decision (`scripts/eventbus/auth.py`)**
   - [ ] Replace the two sets on `Principal` with `consumer_grants`; build it from both mappings in `_populate_token_maps`, keeping deny-all and startup rejection (REQ-001, REQ-005, REQ-007; `scripts/eventbus/auth.py`)
   - [ ] Add the shared authorization function and make `require_consumer_identity` use it (REQ-003; `scripts/eventbus/auth.py`)
   - [ ] Update the principal tests for the new field (REQ-001; `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_admin_topics_authorization.py`)
2. **Phase 2: Subscribe**
   - [ ] Remove the duplicated checks and apply the narrowed topic list (REQ-002, REQ-003; `scripts/eventbus/subscribe_route.py`)
   - [ ] Add omitted-topic and matrix tests (REQ-002; `tests/eventbus/test_eventbus_subscribe.py`)
3. **Phase 3: ACK and NACK**
   - [ ] Add the event-topic lookup helper (REQ-004; `scripts/eventbus/event_repo.py`)
   - [ ] Authorize the (consumer_id, event topic) pair in the routes and rewire the dependencies (REQ-003, REQ-004; `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`)
   - [ ] Add cross-consumer, wrong-topic and missing-event tests (REQ-004; `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_ack_endpoint.py`)
4. **Phase 4: Documentation**
   - [ ] Update ADR-013 implementation notes and the three EventBus docs; refresh the generated reference (REQ-008; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_08_reference_api.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because `scripts/` changes; restart the EventBus service and confirm a subscribe/ACK round trip (REQ-007; `scripts/eventbus/auth.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py` | Unit: matrix, deny-all, control-plane rejection | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_consumer_authorization.py` | All pass |
| `scripts/eventbus/subscribe_route.py` | Route tests: omitted topic, replay narrowing | `uv run pytest tests/eventbus/test_eventbus_subscribe.py` | All pass |
| `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/event_repo.py` | Route tests: cross-consumer, wrong topic, missing event | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py` | All pass; no delivery state change on 403 |
| Runtime update | Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` | Pairs match new mappings |
| Whole package | Regression | `uv run pytest tests/eventbus`; `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `lint-imports` | Clean |
| Module size | Gate | `uv run python tools/check_module_size.py` | Exit 0 |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/generate_reference_table.py --check` | No errors |

Baseline recorded in Step 5: `radon cc` reports `_populate_token_maps` D (21) and `subscribe` D (28) among the touched modules; `vulture scripts/ --min-confidence 80` lists only unrelated findings outside `scripts/eventbus/`; `bandit -r scripts/` reports no Medium or High findings.

## Risks
- **Risk**: A deployed consumer subscribes without `topic` and now receives fewer topics → **Mitigation**: narrowing is limited to topics the consumer was already granted; verify the deployed `config/eventbus.toml` at deploy time (UNK-02).
- **Risk**: Six test files construct `Principal` with the removed fields → **Mitigation**: change them in the same phase as the model and run `uv run pytest tests/eventbus` before any further step.
- **Risk**: The ACK/NACK topic lookup adds a read and could reveal event existence → **Mitigation**: lookup runs only to authorize; a missing event keeps the existing not-found path and a non-granted topic returns 403 before any delivery write.
- **Risk**: A `consumer_authorization` entry with an empty topic list now rejects that consumer_id → **Mitigation**: document it as intended deny-all behavior and cover it with a test.
- **Risk**: ADR edits drift from the Decisions → **Mitigation**: edit Implementation Notes only and run `tools/check_adr_preservation.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Grant model and shared decision in `auth.py`, with principal tests | Completed | — | 20261028-130524 |  |
| 2 | Subscribe route narrowing and tests | Completed | — | 20261028-130524 |  |
| 3 | ACK/NACK pair authorization, `event_repo.py` helper, wiring and tests | Completed | — | 20261028-130524 |  |
| 4 | ADR-013 and EventBus docs | Completed | — | 20261028-130524 |  |
| 5 | Deployment and verification hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-114911_01_scripts_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-114911_02_scripts_eventbus_subscribe_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-114911_03_scripts_eventbus_ack_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-114911_04_scripts_eventbus_app.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-114911_05_scripts_eventbus_event_repo.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-114911_06_tests_eventbus_test_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-114911_07_tests_eventbus_test_eventbus_consumer_authorization.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-114911_08_tests_eventbus_test_eventbus_subscribe.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-114911_09_tests_eventbus_test_eventbus_ack_nack.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-114911_10_tests_eventbus_test_eventbus_ack_endpoint.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-114911_11_tests_eventbus_test_admin_topics_authorization.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-114911_12_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261028-114911_13_docs_24_eventbus_eventbus_02_api-reference-index.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261028-114911_14_docs_24_eventbus_eventbus_12_ack_nack_endpoints.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261028-114911_15_docs_24_eventbus_eventbus_08_reference_api.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-092616
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/event_repo.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_eventbus_subscribe.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `auth.py` set accumulation | `scripts/eventbus/auth.py` | Step 1 | AC-1 | `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 | `tests/eventbus/test_eventbus_auth.py` | Step 1 | AC-1 | `uv run pytest tests/eventbus` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 | `tests/eventbus/test_eventbus_consumer_authorization.py` | Step 1 | AC-1 | `uv run pytest tests/eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `subscribe_route.py` comment; `broker.subscribe` docstring | `scripts/eventbus/subscribe_route.py` | Step 2 | AC-2 | `tests/eventbus/test_eventbus_subscribe.py` | Needs confirmation |
| REQ-002 | Required Changes 2 | `tests/eventbus/test_eventbus_subscribe.py` | Step 2 | AC-2 | `uv run pytest tests/eventbus/test_eventbus_subscribe.py` | Needs confirmation |
| REQ-003 | Required Changes 3 | `scripts/eventbus/auth.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3 | `scripts/eventbus/subscribe_route.py` | Step 2 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_subscribe.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3 | `scripts/eventbus/app.py` | Step 3 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3 | `scripts/eventbus/ack_route.py` | Step 3 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 4; OpenAPI request body on ACK/NACK; ACK/NACK check only `consumer_id` | `scripts/eventbus/ack_route.py` | Step 3 | AC-4 | `tests/eventbus/test_eventbus_ack_nack.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4 | `scripts/eventbus/app.py` | Step 3 | AC-4 | `tests/eventbus/test_eventbus_ack_endpoint.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4 | `scripts/eventbus/event_repo.py` | Step 3 | AC-4 | `tests/eventbus/test_eventbus_ack_nack.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 4 | `tests/eventbus/test_eventbus_ack_nack.py` | Step 3 | AC-4 | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4 | `tests/eventbus/test_eventbus_ack_endpoint.py` | Step 3 | AC-4 | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 5; `_CONTROL_PLANE_ROLES`, ADR-013 INV-07 | `scripts/eventbus/auth.py` | Step 1 | AC-3 | `tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 6; `admin_route.update_topics_authorization` calls `_populate_token_maps` | `scripts/eventbus/auth.py` | Step 1 | AC-5 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 6 | `tests/eventbus/test_admin_topics_authorization.py` | Step 1 | AC-5 | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-007 | Constraints | `scripts/eventbus/auth.py` | Step 1 | AC-1 | `tests/eventbus/test_eventbus_consumer_authorization.py` | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 4 | AC-6 | `tools/check_adr_preservation.py` | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/24_eventbus/eventbus_02_api-reference-index.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/24_eventbus/eventbus_08_reference_api.md` | Step 4 | AC-6 | `tools/generate_reference_table.py --check` | Explicit in issue |