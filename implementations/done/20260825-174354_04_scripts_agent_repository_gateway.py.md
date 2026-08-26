## Goal

`REQ-003`: update `RepositoryGateway.execute()`'s `classify_operation_type()` call site
to pass the caller's `RuntimeToolRegistry`, matching the new signature introduced by
REQ-001.

## Scope

- **In-Scope**: update the single `classify_operation_type(tool_name)` call
  (`scripts/agent/repository_gateway.py:84`) to
  `classify_operation_type(tool_name, ctx.services_required.runtime_tools)`.
- **Out-of-Scope**: `_gate_write()` and the rest of `RepositoryGateway`'s policy/approval
  flow — unchanged; `classify_operation_type()`'s own implementation — covered by the
  companion `scripts/agent/tool_policy.py` implementation procedure document (REQ-001).

## Assumptions

- Confirmed via Read that `RepositoryGateway.execute()` (`scripts/agent/
  repository_gateway.py:73-87`) already receives `ctx: AgentContext` as a parameter, so
  `ctx.services_required.runtime_tools` is reachable without any new parameter threading.
- **Critical finding**: `tests/agent/test_repository_gateway.py`'s `_make_ctx()` helper
  (lines 25-32) builds `ctx` as a `types.SimpleNamespace` with `services=SimpleNamespace(
  gateway=None, tools=AsyncMock())` — it has no `services_required` attribute at all
  (unlike `AgentContext`, where `services_required` is a property that raises if
  `services` is `None`, not a plain attribute). Adding `ctx.services_required.runtime_tools`
  to the call site means every existing test using `_make_ctx()` (all of
  `TestReadBypass` and `TestWritePolicy`, confirmed via `rg "_make_ctx" tests/agent/
  test_repository_gateway.py`) will raise `AttributeError: 'SimpleNamespace' object has
  no attribute 'services_required'` when `RepositoryGateway.execute()` evaluates the new
  argument expression — even though `classify_operation_type` itself is monkeypatched in
  these tests via `patch("agent.repository_gateway.classify_operation_type", ...)`, the
  argument expression is evaluated before the (mocked) call, so the patch does not
  prevent this failure. `_make_ctx()` must be updated in the same change (see
  Implementation, step 2).

## Design decisions

- Single-argument addition at the existing call site; no other logic in `execute()` or
  `_gate_write()` changes.
- Fix `_make_ctx()` in `tests/agent/test_repository_gateway.py` by adding a
  `services_required` attribute alongside the existing `services` attribute (both as
  plain `SimpleNamespace` attributes, since `SimpleNamespace` does not support
  properties) — e.g. `services_required=SimpleNamespace(gateway=None,
  tools=AsyncMock(), runtime_tools=None)` — rather than attempting to make
  `_make_ctx()` return a real `AgentContext`, which would require constructing the
  full `AppServices`/`AgentSession` graph unnecessarily for these unit tests.

## Alternatives considered

- Passing `registry=None` unconditionally at this call site (ignoring `ctx`): rejected —
  would defeat the purpose of REQ-001/REQ-003, since read-only tools discovered only via
  live MCP discovery would never classify as READ, forcing every one of them through
  `_gate_write()`'s approval path.

## Implementation

### Target file
`scripts/agent/repository_gateway.py`

### Procedure
1. In `RepositoryGateway.execute()` (`scripts/agent/repository_gateway.py:84`), change
   `op = classify_operation_type(tool_name)` to `op =
   classify_operation_type(tool_name, ctx.services_required.runtime_tools)`.
2. In `tests/agent/test_repository_gateway.py`, update `_make_ctx()` (lines 25-32) to
   add a `services_required` attribute (see Design decisions) so the new call-site
   argument resolves without `AttributeError`.
3. Re-run the full test file to confirm the three existing test classes still pass
   unmodified in their assertions (only the fixture changes).

### Method
One-line call-site update plus a corresponding test-fixture fix; no change to
`RepositoryGateway`'s control flow.

### Details
- `op == OperationType.READ` still triggers the direct-passthrough branch (line 85-86);
  everything else still routes through `_gate_write()` — unchanged behavior once the
  correct registry is passed.

## Compatibility considerations

- No change to `RepositoryGateway`'s public `execute()` signature — only the internal
  call to `classify_operation_type()` changes.

## Security considerations

- Ensures the write/read gating decision in `RepositoryGateway` (the enforcement point
  for policy/approval) is based on the same RuntimeToolRegistry data used elsewhere in
  the approval pipeline, closing the ADR-003 Decision #8 drift for this call site.

## Rollback considerations

- Revert the call site to `classify_operation_type(tool_name)` and revert the
  `_make_ctx()` fixture change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repository_gateway.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_repository_gateway.py -v` | All existing tests pass after the `_make_ctx()` fixture fix; no `AttributeError` |

## Completion criteria

- `RepositoryGateway.execute()` passes `ctx.services_required.runtime_tools` to
  `classify_operation_type()`.
- `tests/agent/test_repository_gateway.py`'s `_make_ctx()` provides a
  `services_required` attribute so the updated call site does not raise
  `AttributeError`.
- All existing tests in the file pass.

## Out of scope

- `scripts/agent/tool_policy.py`'s `classify_operation_type()` implementation — see the
  companion implementation procedure document for REQ-001/REQ-002.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `classify_operation_type()` call site in `RepositoryGateway.execute()` | Completed | — | — | |
| 2 | Fix `_make_ctx()` in `tests/agent/test_repository_gateway.py` to add `services_required` | Completed | — | — | Prevents `AttributeError` — see Assumptions |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Completed | — | — | All 4 tests pass |
| 4 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-003` — update `RepositoryGateway`'s `classify_operation_type()` call site
- **Source issue**: `issues/20260822_rt_classify_operation_type_unknown_deviation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132516_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/agent/repository_gateway.py`
