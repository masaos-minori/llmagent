# Implementation Procedure: scripts/agent/tool_approval.py (pathkeys001 seq 04)

## Goal
Pass the `RuntimeToolRegistry` available in `check_approval` into the `check_preflight` call at
`scripts/agent/tool_approval.py` line 168, so the middleware preflight resolves the declared
`resource_scope_keys` union and list handling added by sibling `20261104-065555_01` (`REQ-003`:
registry threading at every preflight call site).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Amendment-recorded row (owner-approved, class `scope`, 2026-11-04): this file was appended to the
  Plan's frozen table because the Scope bullet "the declared keys are reachable at every preflight
  call site" is not satisfied without this call-site update.
- `ctx.services_required.runtime_tools` is already dereferenced unconditionally three lines below
  the target line (line 176, `classify_risk` call), so it is non-`None` wherever line 168 runs and
  needs no extra guard.
- Sibling `20261104-065555_01` must land first: `check_preflight` only accepts the extra `registry`
  parameter after that procedure is implemented.
- `tools/check_plan_target_overlaps.py` re-run after the amendment: no finding names this Plan.

## Design decisions
- Pass the registry directly from `ctx.services_required.runtime_tools` rather than hoisting a
  local variable: one changed line, and the sibling call on line 176 already uses that exact
  expression, keeping the two calls symmetrical.

## Alternatives considered
- Hoisting `runtime = ctx.services_required.runtime_tools` above line 168 and using it at both
  calls: rejected as unnecessary churn for a one-line change; the existing line 176 expression is
  left as-is.

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
Single-line edit at the preflight call inside `check_approval`:

```python
# Before (line 168):
        check_preflight(ctx.cfg, tool_name, args)
# After:
        check_preflight(ctx.cfg, tool_name, args, ctx.services_required.runtime_tools)
```

### Method
One-line call-site update; nothing else in the file changes. `denied_allowed_tools` /
`denied_repo_allowlist` handling, the `classify_risk` call, and the `gitops_push_blocked` gate are
untouched.

### Details
- This is the middleware call site reached from the agent tool loop; with sibling `_01` in place it
  makes `read_multiple_files` / git tool denials see the union keys and list elements.
- `ApprovalMiddleware._record_audit` and the `denied_allowed_tools` audit helper paths in this file
  are unaffected.

### Companion test files
- `tests/agent/test_tool_approval_preflight.py`
  - Procedure: add a failing-baseline test (Plan Phase 1) driving `check_approval` with a
    `read_multiple_files` call whose `paths` list contains one element outside `allowed_root`: the
    call is denied with `denied_root_jail` (fails on current code, which skips list values). Add a
    sibling case where all elements are inside and the call proceeds to the approval decision
    unchanged.
  - Validation: `uv run pytest tests/agent/test_tool_approval_preflight.py` — new tests fail before the
    sibling `20261104-065555_01` + this edit land, then all tests pass.

## Compatibility considerations
- The added argument is a positional into a trailing optional parameter; behavior is identical to
  today until sibling `_01` implements the registry-aware resolution.

## Security considerations
- Closes the fail-open gap at the middleware preflight: without this line the middleware would
  keep using configured keys only even after `_01` lands.

## Rollback considerations
- N/A: revert the single commit line; no schema, config, or deploy change.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_policy.py` — failing
  baseline first, then green.
- `uv run ruff check scripts/agent/tool_approval.py tests/agent/test_tool_approval_preflight.py` and
  `uv run ruff format --check` on both.
- `uv run mypy --no-namespace-packages scripts/ tests/agent/test_tool_approval_preflight.py` — clean on the
  changed call.
- Diff-scoped coverage per `rules/toolchain.md` section 7 (`diff-cover --fail-under=90`).

## Completion criteria
- The middleware preflight denial path denies a list-valued path argument with an out-of-root
  element (AC-1/AC-2 middleware half).
- All existing tests in `tests/agent/test_tool_approval_preflight.py` pass unchanged (AC-4).

## Out of Scope
- The approval decision flow, prompts, and audit helpers in this file.
- The other two preflight call sites (siblings `20261104-065555_05/_06`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the failing-baseline tests to the companion test file first (Plan Phase 1); confirm they fail on current code | Pending | — | — | |
| 2 | Apply the one-line call-site edit per Implementation > Procedure | Pending | — | — | Land after sibling _01 |
| 3 | Re-run the companion suite (all green) and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (registry threaded at the middleware preflight call site)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-155552_pathkeys001_path-checks-skip-lists.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-065555
- **Related target files**: `scripts/agent/tool_approval.py`, `tests/agent/test_tool_approval_preflight.py`
