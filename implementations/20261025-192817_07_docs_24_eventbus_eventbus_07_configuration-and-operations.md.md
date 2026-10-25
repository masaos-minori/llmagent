## Goal

Document the shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy in `docs/24_eventbus/eventbus_07_configuration-and-operations.md` via a new "Shutdown" subsection (`REQ-002`, `REQ-003`).

## Scope

- **In-Scope** (`docs/24_eventbus/eventbus_07_configuration-and-operations.md` only):
  - Add a new "## Shutdown" subsection after "DLQ Operations" describing the shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shared helper and shutdown flag (`app.py`, seq 01; `db_conn.py`, seq 02).
  - The connection-ownership invariant recorded in ADR-006 (seq 06).

## Assumptions

- `lifespan()` (app.py:69-118) delegates its shutdown tail to the shared helper `_shutdown_lifespan` (new), which stops scheduling new sweep cycles, awaits the in-flight `_dlq_loop` (app.py:121) sweep, proves exclusive ownership of the shared connection by acquiring `get_db_lock()` (holding `_db_lock`), then closes.
- The connection-ownership rule covers every worker that may hold the lock: the DLQ sweep thread, a route-handler worker thread (via `run_with_db_lock`), and an SSE task.
- The bounded-shutdown bound is `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS` (currently 5.0 s); on lock-acquire timeout the helper raises instead of closing. The bound must stay compatible with the process-manager stop timeout (an external/ops constraint, UNK-02 — no systemd unit exists in this repo).
- This document is implemented after seq 01/02/03, so `_shutdown_lifespan` (new), `set_shutdown_flag` (new), `is_shutting_down` (new) exist.

## Design decisions

- **New top-level "Shutdown" section.** The ops doc is organized by operational area; shutdown is a distinct operator concern (controlled restart, process-manager stop), so it earns its own section rather than being folded into DLQ Operations.
- **Operator-facing, not implementation-facing.** The section describes the observable behavior (what happens on stop, the bound, the ownership rule) and points to ADR-006 for the invariant, rather than restating code.

## Alternatives considered

- **Put the shutdown policy only in ADR-006 (seq 06).** Rejected: operators consult `eventbus_07` for restart/stop procedures; the sequence and bound belong in the ops doc.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

1. Insert a new "## Shutdown" subsection after the "DLQ Operations" section and before "## Validation".
2. Document the shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy (text below).
3. Run the documentation checkers named in `routing.md`.

### Method

Insert the following after the "DLQ Operations" section (before "## Validation"):

```markdown
## Shutdown

`lifespan()` delegates the shared-connection shutdown to one helper shared with the
test suite, so production and tests run the same sequence:

1. Stop scheduling new DLQ sweep cycles once shutdown begins.
2. Await the in-flight `_dlq_loop` sweep (its `asyncio.to_thread()` worker keeps
   running after task cancellation, so the close is serialized behind it).
3. Prove exclusive ownership of the shared connection by acquiring `get_db_lock()`
   (`_db_lock`) with no worker queued on it.
4. Close the connection.

**Connection-ownership rule:** the shared SQLite connection is never closed while any
worker — the DLQ sweep thread, a route-handler worker thread, or an SSE task — may
still execute SQL against it. This is the invariant recorded in
`adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.

**Bounded shutdown:** step 3 is bounded by `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS`
(currently 5.0 s). If exclusive ownership cannot be proven within the bound, shutdown
raises instead of closing (refuse-to-close); there is no close-on-timeout fallback.
The bound must stay compatible with the process-manager stop timeout.
```

### Details

- **`REQ-002` (no new sweep / await in-flight):** step 1-2 of the sequence.
- **`REQ-001` (never close while a worker may use it):** the connection-ownership rule; enforced by `_shutdown_lifespan` (new) proving ownership before close.
- **`REQ-003` (bounded shutdown documented):** the bound value and refuse-to-close policy; the process-manager stop timeout is an external constraint (UNK-02) documented here for operator awareness.
- Blast radius is doc-only; the wording must match the implemented behavior in `app.py` (seq 01).

## Compatibility considerations

- Doc-only. The new section is additive; existing sections are unchanged.

## Security considerations

- No new credentials, secrets, or attack surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `eventbus_07` doc structure | Documentation checker | `uv run python tools/check_workitem_structure.py --file docs/24_eventbus/eventbus_07_configuration-and-operations.md` (or the checker in `routing.md`) | No findings |
| Content accuracy | Manual: wording matches implemented behavior | Review against `app.py` (seq 01) | Sequence + bound match code |

## Completion criteria

- A "## Shutdown" subsection exists after "DLQ Operations" and before "## Validation".
- The shutdown sequence, connection-ownership rule, and bounded-shutdown policy are documented.
- The bound value (5.0 s) and refuse-to-close policy are stated.
- The applicable documentation checker reports no findings.

## Out of Scope

- The shared helper and shutdown flag (`app.py`, seq 01; `db_conn.py`, seq 02).
- The connection-ownership invariant recorded in ADR-006 (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the "Shutdown" subsection: sequence, ownership rule, bounded-shutdown policy | Pending | — | — | Doc-only; run the `routing.md` documentation checker |
| 2 | Add/update tests per Validation plan | Pending | — | — | N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation checkers per `routing.md` |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
