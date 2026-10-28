# Procedure: replace the independent consumer-id and topic sets with pairwise grants and a shared authorization decision

## Goal

Make `Principal` carry explicit (consumer_id, topic) grants and give subscribe, ACK and NACK one shared authorization function (Plan REQ-001, REQ-003).

## Scope

- Modify only `scripts/eventbus/auth.py`.
- In scope: the `Principal` dataclass, `_populate_token_maps`, `resolve_principal`'s copy of the principal, `require_consumer_identity`, and two new helpers.
- Out of scope: route files, `app.py`, tests, docs, token roles and the credential config format.

## Assumptions

- `consumer_authorization` maps consumer_id to topics and `topic_authorization` maps topic to consumer_ids (`EventBusConfig` types in `scripts/eventbus/config.py`); the grant set is the union of the pairs of both.
- `None` ("unrestricted") is never produced for a consumer principal today, so removing it changes no live behavior.
- Owner confirmation of the omitted-topic default (narrow to granted topics, UNK-01) may still arrive; switching to rejection changes only `effective_topics` (new).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Field `consumer_grants: frozenset[tuple[str, str]]` replaces `allowed_consumer_ids` and `allowed_topics`; non-consumer principals get `frozenset()`.
- `authorize_consumer_access` (new) is the single decision: it raises HTTP 403 with the existing audit records and returns nothing; `require_consumer_identity` delegates to it.

## Alternatives considered

- Keep the independent sets and add a second check — rejected: it keeps two sources of truth for the same grant (Plan Design Decision 1).

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

- In `Principal`, replace the two set fields with `consumer_grants` (new) and add the methods `topics_for(consumer_id)` (new) returning the granted topics of one consumer and `is_granted(consumer_id, topic)` (new).
- In `_populate_token_maps`, replace the `ids`/`topics` accumulation with a pair set: for every `consumer_authorization` item add `(consumer_id, topic)`; for every `topic_authorization` item add `(consumer_id, topic)`. Keep the `consumer_token`-without-`consumer_authorization` `ValueError` and the empty-mapping deny-all (`frozenset()`). Give the shared `auth_token`, `admin_token` and every non-CONSUMER per-role token `consumer_grants=frozenset()`.
- In `resolve_principal`, copy `consumer_grants` (new) instead of the two removed fields.
- Add `authorize_consumer_access(request, principal, consumer_id, topics)` (new): reject with 403 (`consumer_identity_rejected`) when the CONSUMER role is absent or the principal has no grants; when `consumer_id` is non-empty and `topics_for(consumer_id)` is empty reject with 403; for each requested topic reject with 403 (`topic_authorization_rejected`) when `is_granted(consumer_id, topic)` is false. Reuse the current log and audit calls and the current detail strings.
- Add `effective_topics(principal, consumer_id, requested)` (new): return `list(requested)` when non-empty, otherwise `sorted(principal.topics_for(consumer_id))`; the caller has already passed `authorize_consumer_access` (new), so an empty result cannot occur for a granted consumer.
- Rewrite `require_consumer_identity` as a thin dependency that calls `authorize_consumer_access` (new) and returns the principal.

### Method

Edit the dataclass and the three functions in place; add the two helpers next to `require_consumer_identity`; no new imports.

### Details

- Current behavior to change: `_populate_token_maps` collapses both mappings into `ids` and `topics` sets, so a token holding `consumer-a -> topic-a` and `consumer-b -> topic-b` accepts `consumer-a` with `topic-b`.
- An empty `topic` query yields an empty `requested` list; the membership loop does nothing, which is the bypass REQ-002 closes through `effective_topics` (new).
- `consumer_id` empty (ACK/NACK always pass a non-empty one, subscribe may omit it): keep today's "Missing consumer_id" HTTP 400 in `subscribe_route.py` (the route owns it, and `tests/eventbus/test_eventbus_subscribe.py` expects 400/422). Correction after adversarial verification: `authorize_consumer_access` (new) therefore must not reject an empty `consumer_id` itself; for an empty `consumer_id` it only requires each requested topic to be granted to some consumer of the principal (today's membership behavior), so the dependency does not preempt the route's 400.
- Keep `Principal` frozen and hashable-safe: grants are a `frozenset` of tuples.

## Compatibility considerations

- `Principal`'s two removed fields are read by six test files and by `subscribe_route.py` (rows 2 and 6-11 update them); `tools/check_compat_shims.py` fails on leftover aliases, so no alias is kept.
- HTTP statuses and audit `error_type` values are unchanged.

## Security considerations

- Strictly fail-closed: an unlisted pair, an empty grant set, or a control-plane credential is rejected with 403.
- No token or secret value is logged; keep `log_auth_failure` calls as they are.

## Rollback considerations

Revert the commit; no data or configuration migration is involved (grants are rebuilt from `config/eventbus.toml` on startup).

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_consumer_authorization.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/auth.py`; `uv run ruff check scripts/eventbus/auth.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/auth.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `Principal` has `consumer_grants` (new) and no `allowed_consumer_ids` / `allowed_topics`; control-plane tokens hold no grants.
- `authorize_consumer_access` (new) and `effective_topics` (new) exist and `require_consumer_identity` delegates to the former.
- Static checks pass and `scripts/eventbus/auth.py` stays under the module size gate (15359 B before the change).

## Out of Scope

- Route changes (rows 2-4), the event topic lookup (row 5), tests and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-130500 | 20261028-130500 | Step 3b: empty consumer_id is left to the route 400 |
| 2 | Add or update tests per Validation plan | Completed | 20261028-130500 | 20261028-130500 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-130500 | 20261028-130500 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-130500 | 20261028-130500 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007 (pairwise grants, narrowed omitted-topic, one decision, no implicit control-plane grants)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: scripts/eventbus/auth.py