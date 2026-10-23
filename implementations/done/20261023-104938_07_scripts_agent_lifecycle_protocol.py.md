## Goal

Verify the `LifecycleProtocol` contract that the coordinator (row 3), manager (row 4),
and router (row 8) all implement. Specifically confirm `shutdown_all` (`:35`) declares a
stable signature so the outcome-based behavior added in rows 2-3 is reachable through the
protocol. This is a contract check; no method body changes.

## Scope

`scripts/agent/lifecycle_protocol.py` only. Reference reads: the coordinator (row 3),
the manager (row 4), the router (row 8). No code change unless verification finds a
signature mismatch.

## Assumptions

- `shutdown_all` (`:35`) is a protocol method that other classes implement; the Plan's
  behavioral changes live in the implementations, not the protocol.

## Design decisions

- **Verify, do not modify.** Confirm the protocol's `shutdown_all` (`:35`) signature is
  compatible with every implementer (coordinator, manager, router) and that adding the
  `TerminationOutcome` return semantics (rows 2-3) does not require a protocol change.
- **If a gap exists** (e.g., a required method is missing or mis-typed), add/fix only
  that protocol member.

## Alternatives considered

- Widening the protocol to return `TerminationOutcome` — rejected: the return type is an
  implementation detail; the protocol expresses the "can be shut down" capability.

## Implementation

### Target file

`scripts/agent/lifecycle_protocol.py`

### Procedure

1. Read `scripts/agent/lifecycle_protocol.py` around `:35`.
2. Enumerate every implementer of the protocol and confirm each defines `shutdown_all`.
3. Confirm the `shutdown_all` signature is uniform across implementers (rows 3, 4, 8).
4. Record the confirmation; edit only if a mismatch is found.

### Method

Read-and-confirm against each implementer. Edit only if verification finds a concrete gap.

### Details

- The protocol is the structural glue that makes rows 2-3's changes reachable; verifying
  it holds keeps the type graph sound under mypy.

## Compatibility considerations

### Corrections found while implementing

Authoritative contract is the source plan's REQ-001..REQ-011 (plans/done/20261022-082349_plan.md); this procedure's earlier Design/Procedure text diverged from it (wrong REQ numbering, nonexistent `HttpShutdownError`, a `for server_key in self._servers` loop, raising on a failed outcome) and was not followed. Contrary to 'verify only': `shutdown_all` now returns `list[tuple[str, TerminationOutcome]]` with a docstring stating that an empty list means every started server was confirmed gone.


- N/A unless a gap is found; this row is verification-first.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/lifecycle_protocol.py` restores
  HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/agent` — proves every implementer satisfies
  the protocol.
- `uv run ruff check scripts/agent/lifecycle_protocol.py`.

## Completion criteria

The protocol's `shutdown_all` (`:35`) is satisfied by every implementer with a uniform
signature; if unmodified, the confirmation is recorded and mypy passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the manager (row 4), the router (row 8), the tests (row 14), and the
  docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `shutdown_all` protocol contract (`:35`) | Completed | 20261023-152943 | 20261023-152943 | Verify-only implemented; full suite passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-152943 | 20261023-152943 | AC-9 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-152943 | 20261023-152943 |  |

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
- **Requirement ID**: REQ-007 (indirect)
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/lifecycle_protocol.py`