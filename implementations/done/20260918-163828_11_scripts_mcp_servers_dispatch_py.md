# Implementation Procedure Output Template (Canonical)

## Goal

Verify that `dispatch.py`'s `dispatch_tool()` function already has the correct `idempotency_key: str | None = None` parameter signature per REQ-003, requiring no modification.

## Scope

- Confirm that `dispatch_tool()` in `scripts/mcp_servers/dispatch.py` already accepts `idempotency_key: str | None = None` as a keyword argument.
- Document that no changes are needed for this file.

## Assumptions

- The source evidence in the plan confirms `dispatch_tool(..., idempotency_key: str | None = None)` exists at line 94 of `dispatch.py`.
- No other function in `dispatch.py` needs modification for REQ-003.

## Design decisions

- No design decision needed — this is a verification-only row.

## Alternatives considered

- N/A: no modifications required.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
No procedure — this is a verify-only row. Review the existing code to confirm the signature matches the requirement.

### Method
Code review / verification only.

### Details
The existing `dispatch_tool()` signature at line 90-94 of `dispatch.py`:

```python
async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
    idempotency_key: str | None = None,
) -> DispatchResult:
```

This already includes `idempotency_key: str | None = None` as an optional parameter. No modification is needed.

## Compatibility considerations

- Not applicable — no changes are made.

## Security considerations

- Not applicable — no changes are made.

## Rollback considerations

- Not applicable — no changes are made.

## Validation plan

- Code review: confirm `dispatch_tool()` signature includes `idempotency_key: str | None = None`.
- No test changes needed since no code changes are made.

## Completion criteria

- [ ] Confirmed `dispatch_tool()` has `idempotency_key: str | None = None` parameter.
- [ ] No modifications were necessary.

## Out of scope

- Modifying `dispatch.py`'s duplicate-detection logic itself.
- Adding the `x-idempotency-key` header to outgoing HTTP requests.
- Idempotency support for non-side-effecting tool calls beyond what `dispatch.py` already handles via `_is_side_effecting()`.
- Changing audit logging semantics or FastAPI route registration/response model contracts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify dispatch_tool() signature has idempotency_key parameter | Pending | — | — | |

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
- **Requirement ID**: REQ-003; AC-3
- **Source issue**: N/A: not found at expected path
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260918-075225_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-163828
- **Related target files**: scripts/mcp_servers/dispatch.py
