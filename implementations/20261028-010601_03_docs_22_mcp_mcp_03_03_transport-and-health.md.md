## Goal

Update the "Retries" bullet in `docs/22_mcp/mcp_03_03_transport-and-health.md` so the documented
retry-exhaustion message contents include the new request-error cause part (REQ-005; AC-5).

## Scope

- The "Retries" bullet (current L28), specifically its final sentence enumerating the
  `TransportError` message contents ("includes the tool name, the last retryable HTTP status (if
  any), and the attempt count"), gains the request-error cause part.
- No other bullet or section of the file changes; retry set, backoff description, and
  health-registry description stay as written.

## Assumptions

- Planned target-file overlap recorded by `check_plan_target_overlaps.py`: this file is also a
  target row of the pending plan `plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md`
  (and its duplicate candidate `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`;
  the duplicate pair is disambiguated before either is processed). Disjoint regions expected —
  mcpcompat001 touches compat-path sections, not the Retries bullet; rebase whichever lands
  second.
- The bullet's surrounding claims (retryable statuses, exponential delay, no sleep after the last
  attempt, health-registry recording) are behavior-neutral under this plan and need no edit.

## Design decisions

- Edit only the message-contents clause; keep the sentence structure and the "raw response bodies
  are not included" rule, which the new cause text honors (class name + httpx connection message,
  not a body).

## Alternatives considered

- Adding a separate bullet for the cause part: rejected — the existing bullet already enumerates
  the message contents in one sentence; a second bullet would duplicate the contract description
  in two places.

## Implementation

### Target file

`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure

1. In the "Retries" bullet (current L28), replace the sentence:
   > The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name, the last
   > retryable HTTP status (if any), and the attempt count; raw response bodies are not included.

   with:
   > The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name, the last
   > retryable HTTP status (if any), the last request-error cause (`last_error=<class>: <message>`,
   > when a non-timeout `httpx.RequestError` was retried), and the attempt count, in that order;
   > raw response bodies are not included.

### Method

Single-sentence replacement in one bullet; no structural doc edits.

### Details

- The parts order (`tool=`, `status=`, `last_error=`, `after N attempts`) is the contract fixed by
  `20261028-010601_01` step 2; the doc must state the order so operators can parse the message.
- The `last_error=` part is absent for status-only exhaustion sequences — the "(when ... retried)"
  qualifier documents that optionality.

## Compatibility considerations

- Implement in the same change set as `20261028-010601_01` (the code change); editing this doc
  before the code lands makes the doc describe a shape the code does not yet produce.
- The security-doc template line in `docs/91_security/security_01_architecture-and-trust-boundaries.md`
  documents the same contract and is updated by `20261028-010601_04` in the same change set
  (REQ-005 pairs both docs).
- Sequencing note for mcpinv001 (`20261028-004925`): mcpinv001's doc row targets
  `mcp_03_01_dispatch-and-routing.md`, not this file; no conflict.

## Security considerations

- The doc explicitly states raw response bodies are not included — unchanged claim, still true of
  the cause text.

## Rollback considerations

- Revert this bullet with the code revert (`20261028-010601_01` Rollback); a reverted code +
  updated doc pair is the stale-doc failure mode the plan Problem section warns about.

## Validation plan

- `rules/toolchain.md` documentation consistency check (22_mcp domain) — message description
  matches the implemented shape (plan Validation plan).
- Cross-check against the cause-in-message test assertion in `20261028-010601_02` step 1.

## Completion criteria

- The Retries bullet enumerates `tool=`, optional `status=`, optional `last_error=` cause, and the
  attempt count in the implemented order (AC-5).
- Documentation consistency check passes for the 22_mcp domain.

## Out of Scope

- The "Non-retryable errors" bullet (L29) and health-registry sections — behavior unchanged.
- The security-doc template line — covered by `20261028-010601_04`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Same change set as 20261028-010601_01 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | N/A: documentation file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | Docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | This document is the docs procedure |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-010601
- **Related target files**: docs/22_mcp/mcp_03_03_transport-and-health.md
