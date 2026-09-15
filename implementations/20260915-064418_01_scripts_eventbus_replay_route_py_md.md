# Implementation Procedure: Remove Unused `_role` Parameter from `replay_route.py`

## Goal

Remove the unused `_role` parameter from `replay()` function in `scripts/eventbus/replay_route.py`, aligning handler signatures with the actual authorization enforcement location (endpoint-level via FastAPI dependencies).

## Scope

- Modify `scripts/eventbus/replay_route.py`: remove `_role` parameter from `replay()`
- No test modifications required (existing tests should still pass)

## Assumptions

- Authorization is enforced at the endpoint level via FastAPI dependencies (`Depends(require_role(...))`), not within handler functions — confirmed by `auth.py:128-172` and `app.py` middleware wiring
- `_role` parameter exists in function signature but is never used in the function body — confirmed by `replay_route.py:33`
- eventbus02/03 have landed before this issue is implemented (required by issue constraints)

## Design decisions

### Decision A: Remove `_role` parameter entirely

**Reason:** The parameter is prefixed with underscore (convention for intentionally unused parameters), but its presence creates a misleading contract for future readers/maintainers. Since authorization is enforced at the endpoint level via FastAPI dependencies, removing it clarifies the responsibility boundary.

### Alternative A: Keep `_role` parameter with explicit comment

**Reason for rejection:** The underscore prefix convention is insufficient to prevent misinterpretation. Future developers may assume the parameter will be used once authorization logic is added, creating technical debt.

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

#### Step 1: Verify current state of `replay()` signature

```python
# Current (before change):
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
) -> Any:
```

Verify `_role` is not referenced anywhere in the function body.

#### Step 2: Remove `_role` parameter from `replay()`

```python
# After change:
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
```

#### Step 3: Update `app.py` to remove `_role` argument passing

Check `app.py` for any code that passes `_role` to this route handler. If found, remove the argument passing.

Example of what to look for in `app.py`:
```python
# Before:
app.get("/replay")(lambda req, since_seq, fmt, limit, offset, _role=None: replay(req, since_seq, fmt, limit, offset, _role=_role))

# After:
app.get("/replay")(lambda req, since_seq, fmt, limit, offset: replay(req, since_seq, fmt, limit, offset))
```

#### Step 4: Run static analysis

```bash
uv run ruff check scripts/eventbus/replay_route.py
uv run mypy scripts/eventbus/replay_route.py
```

Expected: No new errors introduced.

#### Step 5: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_subscribe.py -v
```

Expected: All existing tests pass.

### Method

Parameter removal via surgical edit — only the `_role` parameter line and its associated comment are removed from the function signature.

### Details

#### Verification checklist

- [ ] `_role` is not referenced in `replay()` function body
- [ ] `_role` is not passed from `app.py` route registration
- [ ] Static analysis passes without new errors
- [ ] Existing tests pass

## Compatibility considerations

- **Breaking change risk**: Low — `_role` was always an internal parameter (underscore-prefixed, never part of public API contract)
- **Downstream consumers**: None expected — `_role` was never part of the HTTP API surface
- **Migration path**: None required — parameter removal is backward-compatible since callers never passed `_role` explicitly

## Security considerations

- No security impact — `_role` was unused and did not affect authorization behavior
- Authorization continues to be enforced at the endpoint level via FastAPI dependencies

## Rollback considerations

- Revert to original signature: add `_role: Role | None = None` back to the function signature
- Restore `_role` argument passing in `app.py` if modified

## Validation plan

1. **Static analysis**: Confirm no new lint/type errors introduced
2. **Test execution**: Confirm all existing tests in `tests/eventbus/test_eventbus_subscribe.py` pass
3. **Acceptance criteria verification**:
   - [ ] AC-1: No internal handler accepts unused security context parameters (confirmed by inspecting `replay()` signature)
   - [ ] AC-3: Static analysis reports no unused authorization parameters (confirmed by running `ruff` and `mypy`)

## Completion criteria

- [ ] `_role` parameter removed from `replay()` signature
- [ ] `_role` argument passing removed from `app.py` (if present)
- [ ] Static analysis passes without new errors
- [ ] All existing tests pass

## Out of scope

- Modifying other route handlers (separate procedure per row)
- Adding new authorization logic (out of scope per issue)
- Creating or modifying documentation (separate procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify _role not used in replay() | Pending | — | — | |
| 2 | Remove _role from replay() signature | Pending | — | — | |
| 3 | Update app.py route registration | Pending | — | — | |
| 4 | Run static analysis | Pending | — | — | |
| 5 | Run existing tests | Pending | — | — | |

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
- **Generated at**: 20260915-064418
- **Related target files**: scripts/eventbus/replay_route.py
