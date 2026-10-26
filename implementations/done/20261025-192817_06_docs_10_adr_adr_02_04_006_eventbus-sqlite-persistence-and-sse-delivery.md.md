## Goal

Record the connection-ownership invariant and the bounded-shutdown policy in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, and update the related known-issue note (`REQ-001`, `REQ-003`).

## Scope

- **In-Scope** (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` only):
  - Add the connection-ownership invariant to the Invariants list.
  - Record the bounded-shutdown policy under Failure Policy.
  - Update the known-issue note for the shutdown-closes-connection issue to reflect resolution.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shutdown sequence and shared helper (`app.py`, seq 01; `db_conn.py`, seq 02).
  - The shutdown-sequence ops documentation (`eventbus_07`, seq 07).

## Assumptions

- The invariant list currently runs `INV-01`–`INV-16`; the plan refers to the connection-ownership rule as "INV-01", which collides with the existing INV-01 ("SQLite is the canonical store of Events"). Assign the next free number and place it near the operational-invariant cluster — or rename per owner preference; this is a doc-naming decision.
- The bounded-shutdown bound is `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS` (currently 5.0 s); on lock-acquire timeout the helper raises instead of closing (refuse-to-close).
- The known-issue note for the shutdown defect is the EVENTBUS-022 entry ("shutdown closes the shared connection when the lock was not acquired"); the plan's prose mentions EVENTBUS-021, but the shutdown issue tracked here is EVENTBUS-022.
- This document is implemented after seq 01/02/03, so `_shutdown_lifespan` (new), `set_shutdown_flag` (new), `is_shutting_down` (new) exist.

## Design decisions

- **Invariant where invariants live.** The connection-ownership rule is an invariant about the persistence layer's shutdown contract, so it joins the Invariants list rather than the ops doc.
- **Policy under Failure Policy.** The bounded-shutdown behavior is a fail-fast condition (raise on lock-timeout), so it belongs under Failure Policy, not the DLQ/SSE delivery sections.

## Alternatives considered

- **Put both the invariant and the policy only in `eventbus_07` (seq 07).** Rejected: the ADR is the canonical record of persistence invariants and failure policy; the ops doc is secondary.

## Implementation

### Target file

`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Add a new invariant to the Invariants list describing the connection-ownership rule (assign the next free `INV` number; the plan's "INV-01" label collides with the existing INV-01).
2. Under Failure Policy → Fail-Fast Conditions, record that a lock-acquire timeout during shutdown is a fail-fast that raises instead of closing.
3. Update the known-issue note for the shutdown defect to reflect that the defect is resolved by the invariant.
4. Run the documentation checkers named in `routing.md`.

### Method

Add to the Invariants list (after the last existing entry):

- **Connection ownership:** the shared SQLite connection is never closed while any worker — the DLQ sweep thread, a route-handler worker thread, or an SSE task — may still execute SQL against it. Shutdown proves exclusive ownership before `db.close()`.

Add under Failure Policy → Fail-Fast Conditions:

- **Shutdown lock-acquire timeout:** if exclusive ownership of the shared connection cannot be proven within `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS` (currently 5.0 s), shutdown raises instead of closing the connection. There is no close-on-timeout fallback; the bound stays compatible with the process-manager stop timeout.

Update the known-issue note (the shutdown-defect entry) to:

- **Known Issue: EVENTBUS-022** — RESOLVED by eventbus004: the connection-ownership invariant above forbids closing the shared connection while a worker may own it; the close-on-timeout fallback was removed. Tracked in governance_03 Part 1.

### Details

- **`REQ-001` (never close while a worker may use it):** the new invariant codifies the shutdown contract that `_shutdown_lifespan` (new) enforces.
- **`REQ-003` (bounded shutdown documented):** the fail-fast entry records the bound value and the refuse-to-close policy.
- Blast radius is doc-only; the ADR is a system-of-record citation, so the wording must match the implemented behavior in `app.py` (seq 01).

## Compatibility considerations

- Doc-only. The new invariant and policy entries are additive; existing invariant numbering is preserved (a new number is appended, none renamed).

## Security considerations

- No new credentials, secrets, or attack surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `adr_02_04_006` doc structure | Documentation checker | `uv run python tools/check_workitem_structure.py --file docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (or the checker in `routing.md`) | No findings |
| Content accuracy | Manual: wording matches implemented behavior | Review against `app.py` (seq 01) | Invariant + policy match code |

## Completion criteria

- The connection-ownership invariant is present in the Invariants list with a free `INV` number.
- The bounded-shutdown / refuse-to-close policy is recorded under Failure Policy.
- The known-issue note for the shutdown defect reflects resolution.
- The applicable documentation checker reports no findings.

## Out of Scope

- The shutdown sequence and shared helper (`app.py`, seq 01; `db_conn.py`, seq 02).
- The shutdown-sequence ops documentation (`eventbus_07`, seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add connection-ownership invariant; record bounded-shutdown policy; update the shutdown known-issue note | Completed | 20261026 | 20261026 | Doc-only; run the `routing.md` documentation checker INV-17 added after INV-16; fail-fast bullet under Failure Policy -> Fail-Fast Conditions; EVENTBUS-022 known-issue note marked RESOLVED; wording compressed to stay under the recorded 24726 B size ceiling in tools/check_docs_structure.py (meaning preserved) |
| 2 | Add/update tests per Validation plan | Completed | — | 20261026 | N/A: doc-only N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261026 | Documentation checkers per `routing.md` check_docs_structure/quality/content-policy/consistency --domain eventbus pass; only pre-existing eventbus_06 to_thread() warning remains |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`