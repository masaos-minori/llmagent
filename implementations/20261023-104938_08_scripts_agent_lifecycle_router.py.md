## Goal

Verify that both `shutdown_all` definitions in the lifecycle router (`:76` and `:254`)
propagate termination to every managed subsystem, so the outcome-based behavior from the
terminator (row 2) and coordinator (row 3) reaches all servers. This is a propagation
check; no body changes unless a routing gap is found.

## Scope

`scripts/agent/lifecycle_router.py` only. Reference reads: the coordinator (row 3), the
manager (row 4). No code change unless verification finds a gap.

## Assumptions

- There are two `shutdown_all` methods (`:76`, `:254`); each must forward to the same
  underlying shutdown path rather than short-circuiting some subsystems.

## Design decisions

- **Verify, do not modify.** Read both `shutdown_all` methods (`:76`, `:254`) and confirm
  each routes to the lifecycle manager's `shutdown_all` (row 4) and does not drop any
  server or subsystem.
- **If a gap exists** (e.g., one route omits a subsystem), fix only that route.

## Alternatives considered

- Consolidating the two routes into one — rejected: verify-only; introduce only if a
  route provably fails to propagate.

## Implementation

### Target file

`scripts/agent/lifecycle_router.py`

### Procedure

1. Read `scripts/agent/lifecycle_router.py` around `:76` and `:254`.
2. Confirm both routes forward to the manager's `shutdown_all` (row 4).
3. Confirm no route omits a managed subsystem or server.
4. Record the confirmation; edit only if a gap is found.

### Method

Read-and-confirm against both routes. Edit only if verification finds a concrete gap.

### Details

- Propagation correctness is what makes row 3's per-server branching observable across
  the whole router; a silently-dropped route would defeat REQ-007.

## Compatibility considerations

- N/A unless a gap is found; this row is verification-first.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/lifecycle_router.py` restores
  HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/agent` — proves both routes satisfy the
  protocol (row 7).
- `uv run ruff check scripts/agent/lifecycle_router.py`.

## Completion criteria

Both `shutdown_all` methods (`:76`, `:254`) propagate to the manager's shutdown path
(row 4) without dropping subsystems; if unmodified, the confirmation is recorded and
mypy passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the manager (row 4), the protocol (row 7), the tests (row 14), and the
  docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify both `shutdown_all` routes propagate (`:76`, `:254`) | Pending | — | — | Verify-only |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: `scripts/agent/lifecycle_router.py`
