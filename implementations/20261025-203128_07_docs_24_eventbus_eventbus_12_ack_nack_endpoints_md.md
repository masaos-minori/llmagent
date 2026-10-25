## Goal

Document the NACK idempotency key contract in `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`: the client-generated stable delivery-attempt key, its latest-key-only scope and retention, and reconcile the duplicate-NACK no-op row (`eventbus_12:59`) with the fixed route behavior (`REQ-001`, `REQ-004`, `REQ-005`).

## Scope

- **In-Scope** (`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` only):
  - Add an "Idempotency Key" subsection under "Negatively Acknowledge Event" describing the client-generated stable key, how to send it on retries, and the dedup semantics.
  - Add a keyless-NACK row (400) to the NACK condition table (`eventbus_12:42-48`), per UNK-01.
  - Reconcile the duplicate-NACK no-op row (`eventbus_12:59`) to state that the no-op applies only when the SAME delivery-attempt key is repeated.
  - Document the key scope / retention window (latest-key-only).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01) — introduces the query parameter documented here.
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - Tests (seq 05/06), ADR close (seq 08).

## Assumptions

- UNK-02 = client-generated stable key: the client owns/derives the key from `(consumer_id, event_id)` and echoes it on every NACK retry. This doc describes that contract for external subscribers (no client exists in this repository).
- UNK-03 recommended = latest-key-only: the single remembered key (`consumer_last_nack_attempt`) is compared; a non-latest key counts as a new attempt.
- UNK-01 recommended = reject keyless with 400: the route enforces key presence (seq 01); this doc records the resulting 400.
- `deploy.sh` rsyncs `docs/` wholesale to `/opt/llm/`; this doc is deployed with the rsync.

## Design decisions

- **Contract-first documentation.** The NACK endpoint now carries a caller-supplied idempotency key; this section is the canonical ops contract for subscribers — how to derive the key, when to reuse it, and what the server does on a repeat.
- **Reconcile the no-op row.** The `eventbus_12:59` row stated the no-op without stating the precondition (same key). The route previously minted a per-request UUID, so the no-op never fired. This doc restates the no-op as conditioned on repeating the same delivery-attempt key, matching the fixed route (seq 01) and the repository guard (seq 02).

## Alternatives considered

- **Server-issued key contract:** if UNK-02 selected the server-issued model, this section would document an SSE-provided `attempt_id` the client echoes. Rejected as default (client-key model); recorded in seq 03.
- **Leave the no-op row unqualified:** rejected — an unconditional no-op claim is misleading once the route passes a stable key; the precondition must be explicit.

## Implementation

### Target file

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

1. Under "Negatively Acknowledge Event" (eventbus_12:38), after the success description (eventbus_12:40), add an **Idempotency Key** subsection: the client generates/holds a stable key per delivery attempt; send it as the NACK query parameter on every retry of that attempt; advance to a new key for a genuinely new attempt; the server deduplicates a repeat.
2. Add a row to the NACK condition table (eventbus_12:42-48): `idempotency key missing | 400`.
3. Edit the duplicate-NACK no-op row (eventbus_12:59) to add the precondition: the no-op applies when the NACK repeats the same delivery-attempt key (i.e. the same `consumer_last_nack_attempt`).
4. Add a **Key scope and retention** note stating latest-key-only: only the most recent key per `(consumer_id, event_id)` is remembered; a non-latest key counts as a new attempt.
5. Run the documentation checkers.

### Method

The "Negatively Acknowledge Event" section (eventbus_12:38-48) documents the `/nack` success payload (`event_id`, `consumer_delivery_failure_count`, optional `dlq_promoted`) and the condition table. The "ACK/NACK State Transition Table" (eventbus_12:52-64) includes the duplicate-NACK no-op row at eventbus_12:59. The edits below are additive (new subsection + table row + retention note) and a targeted edit of the no-op row's wording.

```markdown
<!-- eventbus_12 — add under "Negatively Acknowledge Event", after the success paragraph (eventbus_12:40) -->

### Idempotency Key

`POST /nack` accepts an `idempotency_key` (new) query parameter identifying the
delivery attempt. The client generates and holds this key (for example derived
from `(consumer_id, event_id, attempt_number)`, or a client-stored UUID) and sends
it on **every** NACK for that attempt:

- A retry of the **same** failed attempt reuses the **same** key → the NACK is a
  **no-op** (counters unchanged), so network/proxy retries do not double-count.
- Advancing to a **new** attempt uses a **new** key → counted once.

The server treats the key opaquely and passes it unchanged through to the
repository. A NACK without a key is rejected with HTTP 400.

| Condition | HTTP status |
|---|---|
| ... | ... |
| `idempotency_key` parameter missing | 400 |
```

```markdown
<!-- eventbus_12 — reconcile the duplicate-NACK no-op row (eventbus_12:59) -->
| Duplicate NACK (same delivery attempt) | 200 | No-op: a NACK that repeats the **same delivery-attempt key** (the stored `consumer_last_nack_attempt`) leaves counters unchanged. A distinct key counts as a new attempt. |
```

```markdown
<!-- eventbus_12 — add a Key scope and retention note after the transition table (eventbus_12:64) -->
**NACK idempotency key scope and retention.** Deduplication is latest-key-only:
only the most recent `consumer_last_nack_attempt` per `(consumer_id, event_id)` is
remembered. A NACK whose key is not the most recent one counts as a new attempt.
(A bounded set of recent keys would require a schema change and is not adopted.)
```

### Details

- **`REQ-001` (key contract caller→route→repo):** this section is the subscriber-facing statement of the one-key-per-attempt contract that seq 01 wires through the route and seq 02 enforces in the repository.
- **`REQ-004` / UNK-03 (scope/retention):** the latest-key-only note pins the documented retention window and defines the out-of-order boundary ("a non-latest key counts as a new attempt"), reconciling the previously unconditional no-op claim at eventbus_12:59.
- **`REQ-005` (client obtainable identity):** under the client-key model the client derives the key from data it already holds (`event_id`); no SSE field is required (seq 03).
- **UNK-01 (keyless 400):** the added condition table row records the reject-400 contract enforced by seq 01.

## Compatibility considerations

- N/A: documentation-only edit to an existing contract section; the `/nack` response shape is unchanged.

## Security considerations

- N/A: no credentials, secrets, or authorization changes; the key is an opaque client identifier.

## Rollback considerations

- N/A: revert the doc edit (`git checkout docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Contract doc integrity | Current-source verification | `uv run python tools/stale_detector.py {this doc}` | All referenced constructs found; no-op row reconciled |
| Structure check | Structure | `uv run python tools/check_workitem_structure.py {this doc}` | No findings |

## Completion criteria

- The "Negatively Acknowledge Event" section documents the idempotency key contract (derive/reuse/advance) and a keyless-400 row is added to the NACK condition table.
- The duplicate-NACK no-op row states the same-key precondition and latest-key-only scope.
- `stale_detector.py` and `check_workitem_structure.py` pass.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- Tests (seq 05/06).
- ADR invariant + EVENTBUS-023 close (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, seq 08).
- UNK-03 bounded-set retention — recorded as not adopted.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document the NACK idempotency key contract + key scope/retention; reconcile the duplicate-NACK no-op row; add keyless-400 row | Pending | — | — | Docs-only; latest-key-only recorded |
| 2 | Run the documentation checkers (`stale_detector.py`, `check_workitem_structure.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
