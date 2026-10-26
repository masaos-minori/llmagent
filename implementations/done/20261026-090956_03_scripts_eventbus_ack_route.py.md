## Goal

Remove the `%r` debug logging of `_principal`/`_identity` from `ack_route.py` and unify the
handler-level `allowed_consumer_ids` check with the `require_consumer_identity()`
dependency check, so there is a single authorization boundary and no principal is logged
with `%r`.

## Scope

- Modify only `scripts/eventbus/ack_route.py`: the debug log at line 39 and the
  handler-level membership checks in `_do_ack()` (lines 50-62) and `nack()` (lines 140-149).

## Assumptions

- `Principal` carries a token fingerprint (`_derive_token_fingerprint`, SHA-256 prefix), not
  the token, so the `%r` exposure is low; removal is hygiene (plan Background).
- `require_consumer_identity()` (auth.py:279) enforces the same unauthorized-consumer-id →
  403 contract the handler checks enforce.
- UNK-03 (the concrete list of duplicated checks) is an engineering decision recorded before
  execution; this procedure removes the handler duplicates and relies on the dependency.

## Design decisions

- **Single boundary.** Route ACK/NACK consumer identity through the
  `require_consumer_identity()` FastAPI dependency and delete the handler-level
  `allowed_consumer_ids` membership re-checks, which duplicate the dependency.
- **Keep exactly-403-before-409.** Whatever the UNK-03 outcome, an unauthorized consumer ID
  must still return exactly 403 before any delivery-state check (REQ-005; Acceptance 3).

## Alternatives considered

- Retaining the handler check and documenting why (UNK-03): acceptable only if the
  dependency does not cover every case; otherwise it is a duplicate boundary.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Delete the debug log line 39:
   `logger.debug("DEBUG _do_ack: _principal=%r, _identity=%r", _principal, _identity)`.
2. In `_do_ack()` (lines 50-62) and `nack()` (lines 140-149), remove the handler-level
   `allowed_consumer_ids` membership guard that duplicates `require_consumer_identity()`.
3. Confirm the consumer identity is enforced by the `require_consumer_identity()`
   dependency at the route layer (set by app.py wrapper / FastAPI). If the dependency
   covers the consumer-id check, no further code is needed; if it does not cover a case
   the handler guard did, retain ONLY that specific guard and document why (UNK-03).
4. Keep `_principal`/`_identity` parameters (set by app.py wrapper) for any downstream use
   other than the removed membership check.

### Method

Edit the two handlers and remove the log line; no new symbols.

### Details

- Do not change the ACK/NACK delivery logic; only the authorization-boundary dedup and the
  log removal.
- Record the concrete duplicated-check list (UNK-03) in the plan's design before executing.

## Compatibility considerations

- Consumers already receive 403 for unauthorized consumer IDs via the dependency; behavior
  is unchanged except the redundant handler check is gone.

## Security considerations

- Removing `%r` logging prevents any principal representation reaching debug logs (REQ-007).
- The single dependency boundary preserves fail-closed 403 (INV-01/02).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` — unauthorized consumer ID
  returns exactly 403 (this row removes the handler duplicate; seq 09 tightens the
  assertion from `(403, 409)` to `403`).
- `uv run pytest tests/eventbus/` — full suite passes.
- `uv run radon cc scripts/eventbus/ack_route.py`; keep `nack` at or below B (8).
  `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.
- `uv run mypy`, `uv run ruff`.

## Completion criteria

- No `%r` principal log remains; the unauthorized-consumer-id path returns exactly 403 via a
  single authorization boundary.

## Out of Scope

- Changing the ACK/NACK delivery or transaction logic.
- The UNK-03 duplicated-check enumeration — resolve before executing this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `%r` log; unify handler auth check with dependency | Pending | — | — | UNK-03 enumerated before execution |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-03: concrete duplicated-check list is an engineering decision | Classified non-blocking; enumerate before execution | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `scripts/eventbus/ack_route.py`
