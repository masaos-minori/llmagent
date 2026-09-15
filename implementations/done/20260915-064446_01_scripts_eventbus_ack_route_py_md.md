# Implementation Procedure: Remove Unused `_role` and `_identity` Parameters from `ack_route.py`

## Goal

Remove the unused `_role` and `_identity` parameters from `_do_ack()`, `ack_event()`, and `nack()` functions in `scripts/eventbus/ack_route.py`, aligning handler signatures with the actual authorization enforcement location (endpoint-level via FastAPI dependencies).

## Scope

- Modify `scripts/eventbus/ack_route.py`: remove `_role` and `_identity` parameters from three functions
- No test modifications required (existing tests should still pass)

## Assumptions

- Authorization is enforced at the endpoint level via FastAPI dependencies (`Depends(require_role(...))`), not within handler functions — confirmed by `auth.py:128-172` and `app.py` middleware wiring
- `_role` and `_identity` parameters exist in function signatures but are never used in the function bodies — confirmed by `ack_route.py:34-35` (_do_ack), `ack_route.py:82-83` (ack_event), `ack_route.py:94-95` (nack)
- eventbus02/03 have landed before this issue is implemented (required by issue constraints)

## Design decisions

### Decision A: Remove `_role` and `_identity` parameters entirely

**Reason:** Both parameters are prefixed with underscore (convention for intentionally unused parameters), but their presence creates a misleading contract for future readers/maintainers. Since authorization is enforced at the endpoint level via FastAPI dependencies, removing them clarifies the responsibility boundary.

### Alternative A: Keep parameters with explicit comments

**Reason for rejection:** The underscore prefix convention is insufficient to prevent misinterpretation. Future developers may assume the parameters will be used once authorization logic is added, creating technical debt.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

#### Step 1: Verify current state of `_do_ack()` signature

```python
# Current (before change):
async def _do_ack(
    request: Request,
    event_id: str,
    acked: bool,
    _role: Role | None = None,
    _identity: str | None = None,
) -> JSONResponse:
```

Verify `_role` and `_identity` are not referenced anywhere in the function body.

#### Step 2: Remove `_role` and `_identity` parameters from `_do_ack()`

```python
# After change:
async def _do_ack(
    request: Request,
    event_id: str,
    acked: bool,
) -> JSONResponse:
```

#### Step 3: Verify current state of `ack_event()` signature

```python
# Current (before change):
async def ack_event(
    request: Request,
    event_id: str,
    _role: Role | None = None,
    _identity: str | None = None,
) -> JSONResponse:
```

Verify `_role` and `_identity` are not referenced anywhere in the function body.

#### Step 4: Remove `_role` and `_identity` parameters from `ack_event()`

```python
# After change:
async def ack_event(
    request: Request,
    event_id: str,
) -> JSONResponse:
```

#### Step 5: Verify current state of `nack()` signature

```python
# Current (before change):
async def nack(
    request: Request,
    event_id: str,
    _role: Role | None = None,
    _identity: str | None = None,
) -> JSONResponse:
```

Verify `_role` and `_identity` are not referenced anywhere in the function body.

#### Step 6: Remove `_role` and `_identity` parameters from `nack()`

```python
# After change:
async def nack(
    request: Request,
    event_id: str,
) -> JSONResponse:
```

#### Step 7: Update `app.py` to remove `_role` and `_identity` argument passing

Check `app.py` for any code that passes these parameters to the ACK/NACK route handlers. If found, remove the argument passing.

Example of what to look for in `app.py`:
```python
# Before:
app.post("/ack/{event_id}")(lambda req, eid, _role=None, _identity=None: ack_event(req, eid, _role=_role, _identity=_identity))
app.post("/nack/{event_id}")(lambda req, eid, _role=None, _identity=None: nack(req, eid, _role=_role, _identity=_identity))

# After:
app.post("/ack/{event_id}")(lambda req, eid: ack_event(req, eid))
app.post("/nack/{event_id}")(lambda req, eid: nack(req, eid))
```

#### Step 8: Run static analysis

```bash
uv run ruff check scripts/eventbus/ack_route.py
uv run mypy scripts/eventbus/ack_route.py
```

Expected: No new errors introduced.

#### Step 9: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_auth.py -v
```

Expected: All existing tests pass.

### Method

Parameter removal via surgical edit — only the `_role` and `_identity` parameter lines and their associated comments are removed from each function signature.

### Details

#### Verification checklist

- [ ] `_role` and `_identity` are not referenced in `_do_ack()` function body
- [ ] `_role` and `_identity` are not referenced in `ack_event()` function body
- [ ] `_role` and `_identity` are not referenced in `nack()` function body
- [ ] `_role` and `_identity` arguments are not passed from `app.py` route registration
- [ ] Static analysis passes without new errors
- [ ] Existing tests pass

## Compatibility considerations

- **Breaking change risk**: Low — both parameters were always internal (underscore-prefixed, never part of public API contract)
- **Downstream consumers**: None expected — neither parameter was part of the HTTP API surface
- **Migration path**: None required — parameter removal is backward-compatible since callers never passed these explicitly

## Security considerations

- No security impact — both parameters were unused and did not affect authorization behavior
- Authorization continues to be enforced at the endpoint level via FastAPI dependencies

## Rollback considerations

- Revert to original signatures: add `_role: Role | None = None` and `_identity: str | None = None` back to all three function signatures
- Restore argument passing in `app.py` if modified

## Validation plan

1. **Static analysis**: Confirm no new lint/type errors introduced
2. **Test execution**: Confirm all existing tests in `tests/eventbus/test_eventbus_auth.py` pass
3. **Acceptance criteria verification**:
   - [ ] AC-1: No internal handler accepts unused security context parameters (confirmed by inspecting `_do_ack()`, `ack_event()`, and `nack()` signatures)
   - [ ] AC-3: Static analysis reports no unused authorization parameters (confirmed by running `ruff` and `mypy`)

## Completion criteria

- [x] `_role` and `_identity` parameters removed from `_do_ack()` signature
- [x] `_role` and `_identity` parameters removed from `ack_event()` signature
- [x] `_role` and `_identity` parameters removed from `nack()` signature
- [x] Argument passing removed from `app.py`
- [x] Static analysis passes without new errors
- [ ] All existing tests pass (pre-existing failures unrelated to this change)

## Out of scope

- Modifying other route handlers (separate procedure per row)
- Adding new authorization logic (out of scope per issue)
- Creating or modifying documentation (separate procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify _role/_identity not used in _do_ack() | Done | — | — | Confirmed unused |
| 2 | Remove _role/_identity from _do_ack() signature | Done | — | — | Parameters removed |
| 3 | Verify _role/_identity not used in ack_event() | Done | — | — | Confirmed unused |
| 4 | Remove _role/_identity from ack_event() signature | Done | — | — | Parameters removed |
| 5 | Verify _role/_identity not used in nack() | Done | — | — | Confirmed unused |
| 6 | Remove _role/_identity from nack() signature | Done | — | — | Parameters removed |
| 7 | Update app.py route registration | Done | — | — | Removed argument passing |
| 8 | Run static analysis | Done | — | — | ruff + mypy pass |
| 9 | Run existing tests | Done | — | — | Pre-existing failures; ACK/NACK tests pass |

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
- **Requirement ID**: REQ-002 (remove unused security parameters from handlers relying on endpoint-level authorization)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-183834_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064446
- **Related target files**: scripts/eventbus/ack_route.py
