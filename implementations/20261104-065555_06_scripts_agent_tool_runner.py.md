# Implementation Procedure: scripts/agent/tool_runner.py (pathkeys001 seq 06)

## Goal
Pass the `RuntimeToolRegistry` reachable from `ctx` into the gateway-less `check_preflight` call at
`scripts/agent/tool_runner.py` line 223, so the runner's fallback preflight applies the declared
`resource_scope_keys` union and list handling added by sibling `20261104-065555_01` (`REQ-003`:
registry threading at every preflight call site).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Amendment-recorded row (owner-approved, class `scope`, 2026-11-04): this file was appended to the
  Plan's frozen table because the Scope bullet "the declared keys are reachable at every preflight
  call site" is not satisfied without this call-site update.
- `ctx.services_required.runtime_tools` is already dereferenced unconditionally eight lines above
  the target line (line 215, `classify_operation_type` call), so it is non-`None` wherever line 223
  runs and needs no extra guard.
- Sibling `20261104-065555_01` must land first: `check_preflight` only accepts the extra `registry`
  parameter after that procedure is implemented.
- `tools/check_plan_target_overlaps.py` re-run after the amendment: no finding names this Plan.

## Design decisions
- Pass `ctx.services_required.runtime_tools` directly in the call, mirroring line 215's expression,
  so the tier classification and the fallback preflight resolve keys from the same registry
  instance.

## Alternatives considered
- Removing the gateway-less preflight and forcing all calls through the gateway: rejected — the
  gateway-bypass justification comment at lines 200-210 documents this fallback as a required
  safety layer; weakening it is out of the Plan's scope.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
Single-line edit at the fallback preflight call:

```python
# Before (line 223):
            check_preflight(ctx.cfg, name, args)
# After:
            check_preflight(ctx.cfg, name, args, ctx.services_required.runtime_tools)
```

### Method
One-line call-site update; nothing else in the file changes. The gateway delegation branch
(`gateway.execute`) and the `OperationType.READ` bypass are untouched.

### Details
- This is the last of the three `check_preflight` call sites (verified by grep across
  `scripts/`): middleware (`_04`), gateway (`_05`), runner fallback (this). The gateway branch
  returns earlier, so this line only runs when `ctx.services_required.gateway` is `None`.
- The gateway-bypass justification docstring (lines 200-210) remains accurate; it does not cite
  key-resolution details and needs no wording change.

### Companion test files
- `tests/agent/test_tool_runner.py` (itself)
  - Procedure: add a failing-baseline test (Plan Phase 1) executing a non-READ tool call with no
    gateway in context and a list-valued path argument with one element outside `allowed_root`: the
    result is denied (`Policy blocked:` / `denied_root_jail`) instead of executed (fails on current
    code, which skips list values). Add a sibling all-insside case that executes.
  - Validation: `uv run pytest tests/agent/test_tool_runner.py` — new tests fail before the sibling
    `20261104-065555_01` + this edit land, then all tests pass.

## Compatibility considerations
- The added argument is a positional into a trailing optional parameter; behavior is identical to
  today until sibling `_01` implements the registry-aware resolution.

## Security considerations
- Closes the fail-open gap at the last preflight call site: without this line the runner fallback
  would keep using configured keys only even after `_01` lands.

## Rollback considerations
- N/A: revert the single commit line; no schema, config, or deploy change.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_policy.py` — failing baseline
  first, then green.
- `uv run ruff check scripts/agent/tool_runner.py tests/agent/test_tool_runner.py` and
  `uv run ruff format --check` on both.
- `uv run mypy --no-namespace-packages scripts/ tests/agent/test_tool_runner.py` — clean on the
  changed call.
- Diff-scoped coverage per `rules/toolchain.md` section 7 (`diff-cover --fail-under=90`).

## Completion criteria
- The runner fallback preflight denies a list-valued path argument with an out-of-root element
  (AC-1/AC-2 runner half).
- All existing tests in `tests/agent/test_tool_runner.py` pass unchanged (AC-4).

## Out of Scope
- The gateway delegation branch and READ bypass logic in this file.
- The other two preflight call sites (siblings `20261104-065555_04/_05`).

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
- **Requirement ID**: REQ-003 (registry threaded at the runner fallback preflight call site)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-155552_pathkeys001_path-checks-skip-lists.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-065555
- **Related target files**: `scripts/agent/tool_runner.py`, `tests/agent/test_tool_runner.py`
