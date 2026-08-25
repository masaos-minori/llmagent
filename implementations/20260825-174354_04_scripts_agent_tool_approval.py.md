## Goal

`REQ-003`: update `check_approval()`'s `classify_risk()` call site to pass the caller's
`RuntimeToolRegistry`, matching the new signature introduced by REQ-002.

## Scope

- **In-Scope**: update `classify_risk(ctx.cfg, tool_name, args)`
  (`scripts/agent/tool_approval.py:156`) to `classify_risk(ctx.cfg, tool_name, args,
  ctx.services_required.runtime_tools)`.
- **Out-of-Scope**: `classify_risk()`'s own implementation — covered by the companion
  `scripts/agent/tool_policy.py` implementation procedure document (REQ-001/REQ-002);
  the rest of `check_approval()`'s preflight/preview/audit flow.

## Assumptions

- Confirmed via Read that the call site is inside `check_approval(ctx, tool_name, args)`
  (`scripts/agent/tool_approval.py:123-127`), which already receives `ctx: AgentContext`,
  so `ctx.services_required.runtime_tools` is reachable without new parameter threading.
- Confirmed via Read (`tests/agent/test_tool_approval_risk.py:96-105`) that this file's
  `_make_ctx()` test helper builds `ctx = MagicMock()` and already sets
  `ctx.services_required.audit_logger` / `ctx.services_required.tools` explicitly —
  `ctx.services_required.runtime_tools` will auto-resolve to a `MagicMock()` instance on
  first access (no `AttributeError`), but this auto-generated `MagicMock` is truthy and
  its `.get(tool_name)` call returns another `MagicMock` rather than raising `KeyError`,
  so `classify_operation_type()` (called internally by `classify_risk()`) would resolve
  such tools as `READ`, not `UNKNOWN`, unless `registry` is set explicitly. Any test in
  this file asserting `"high"` for a genuinely-unregistered tool name (e.g.
  `some_unregistered_tool`, `totally_unregistered_tool_xyz` — lines 149, 153) must
  explicitly set `ctx.services_required.runtime_tools = None` (or a `MagicMock` whose
  `.get` raises `KeyError`) in its test body/fixture, or the auto-generated `MagicMock`
  will cause the test to observe `READ`-derived risk instead of the expected fail-closed
  `UNKNOWN`-derived `"high"`.

## Design decisions

- Single-argument addition at the existing call site; no other logic in
  `check_approval()` changes.
- In `tests/agent/test_tool_approval_risk.py`, explicitly set
  `ctx.services_required.runtime_tools = None` in `_make_ctx()` (rather than leaving it
  to auto-generate a `MagicMock`) so the existing fail-closed-`"high"` assertions (lines
  149, 153) keep passing without relying on `MagicMock`'s default truthy/no-raise
  behavior, which does not model the real `RuntimeToolRegistry.get()` contract.

## Alternatives considered

- Leaving `_make_ctx()` unchanged and relying on `MagicMock`'s auto-generated attribute
  behavior: rejected — silently changes the semantics of the existing
  "unregistered tool → high risk" tests from fail-closed-by-absence to
  accidentally-classified-as-READ, defeating the intent of both the existing tests and
  this Requirement.

## Implementation

### Target file
`scripts/agent/tool_approval.py`

### Procedure
1. In `check_approval()` (`scripts/agent/tool_approval.py:156`), change `risk =
   classify_risk(ctx.cfg, tool_name, args)` to `risk = classify_risk(ctx.cfg, tool_name,
   args, ctx.services_required.runtime_tools)`.
2. In `tests/agent/test_tool_approval_risk.py`'s `_make_ctx()` (lines 96-105), add
   `ctx.services_required.runtime_tools = None` explicitly.
3. Re-run the file's tests asserting `"high"` for unregistered tool names (lines
   ~149, 153) and confirm they still pass under the explicit `None`.

### Method
One-line call-site update plus a corresponding test-fixture addition; no change to
`check_approval()`'s control flow.

### Details
- Do not set `ctx.services_required.runtime_tools` to anything other than `None` in the
  base `_make_ctx()` fixture — individual tests that need a populated registry (e.g. to
  exercise the READ path) should override it per-test, keeping the fail-closed default
  as the shared baseline.

## Compatibility considerations

- No change to `check_approval()`'s public signature — only the internal call to
  `classify_risk()` changes.

## Security considerations

- Ensures the approval-gating risk level is derived from the same RuntimeToolRegistry
  data used elsewhere in the pipeline, closing the ADR-003 Decision #8 drift for this
  call site; the test-fixture fix additionally prevents a latent false-negative (a
  `MagicMock`-derived accidental READ classification) from masking a real fail-closed
  regression in this file's test suite.

## Rollback considerations

- Revert the call site to `classify_risk(ctx.cfg, tool_name, args)` and remove the
  `ctx.services_required.runtime_tools = None` line from `_make_ctx()`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_approval.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_tool_approval_risk.py -v` | All existing tests pass; unregistered-tool tests (lines ~149, 153) still resolve to `"high"` under the explicit `registry=None` |

## Completion criteria

- `check_approval()` passes `ctx.services_required.runtime_tools` to `classify_risk()`.
- `tests/agent/test_tool_approval_risk.py`'s `_make_ctx()` explicitly sets
  `runtime_tools = None` as the default.
- All existing tests in the file pass.

## Out of scope

- `scripts/agent/tool_policy.py`'s `classify_risk()`/`classify_operation_type()`
  implementation — see the companion implementation procedure document for
  REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `classify_risk()` call site in `check_approval()` (line 156) | Pending | — | — | |
| 2 | Add explicit `ctx.services_required.runtime_tools = None` to `_make_ctx()` in `tests/agent/test_tool_approval_risk.py` | Pending | — | — | See Assumptions/Design decisions |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` — update `tool_approval.py`'s `classify_risk()` call site
- **Source issue**: `issues/20260822_rt_classify_operation_type_unknown_deviation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132516_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/agent/tool_approval.py`
