# Implementation Procedure: scripts/agent/repository_gateway.py (pathkeys001 seq 05)

## Goal
Pass the `RuntimeToolRegistry` reachable from `_gate_write`'s `ctx` into the `check_preflight` call
at `scripts/agent/repository_gateway.py` line 102, so the gateway write gate applies the declared
`resource_scope_keys` union and list handling added by sibling `20261104-065555_01` (`REQ-003`:
registry threading at every preflight call site).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Amendment-recorded row (owner-approved, class `scope`, 2026-11-04): this file was appended to the
  Plan's frozen table because the Scope bullet "the declared keys are reachable at every preflight
  call site" is not satisfied without this call-site update.
- `ctx.services_required.runtime_tools` is typed `RuntimeToolRegistry | None` and is already
  dereferenced in the same class (line 96, where `execute` resolves the tier for the
  `classify_operation_type` call), and `_gate_write` receives the same
  `ctx`, so no guard is needed; the trailing optional `registry` parameter accepts the `None` case
  for mypy anyway.
- Sibling `20261104-065555_01` must land first: `check_preflight` only accepts the extra `registry`
  parameter after that procedure is implemented.
- `tools/check_plan_target_overlaps.py` re-run after the amendment: no finding names this Plan.

## Design decisions
- Pass `ctx.services_required.runtime_tools` directly in the call rather than reading a gateway
  member: the gateway's own `self._cfg` is used for config today, but the registry lives on the
  per-call `ctx`, mirroring how `execute` already resolves the operation tier.

## Alternatives considered
- Storing the registry on the gateway instance at construction: rejected — the gateway is built per
  agent wiring while the registry flows per call; member state would add lifecycle coupling for no
  behavior gain.

## Implementation
### Target file
`scripts/agent/repository_gateway.py`

### Procedure
Single-line edit at the preflight call inside `_gate_write`:

```python
# Before (line 102):
            check_preflight(self._cfg, tool_name, args)
# After:
            check_preflight(self._cfg, tool_name, args, ctx.services_required.runtime_tools)
```

### Method
One-line call-site update; nothing else in the file changes. The `PolicyViolationError` handling,
executor call, and `gateway.write` audit logging are untouched.

### Details
- This is the gateway-bypass target: with the gateway absent, `tool_runner` reaches its own
  preflight (sibling `_06`); with the gateway present, every non-READ write passes this line.
- Non-write tier calls never reach `_gate_write` today (execute routes them without a policy
  preflight) and stay unchanged (Plan Scope covers the write gate only).

### Companion test files
- `tests/agent/test_repository_gateway.py` (itself)
  - Procedure: add a failing-baseline test (Plan Phase 1) driving `RepositoryGateway.execute` for a
    write tool whose list-valued path argument has one element outside `allowed_root`: the result is
    the existing denied result (`Policy blocked:` / `denied_root_jail`) instead of execution (fails
    on current code, which skips list values). Add a sibling all-inside case that executes.
  - Validation: `uv run pytest tests/agent/test_repository_gateway.py` — new tests fail before the
    sibling `20261104-065555_01` + this edit land, then all tests pass.

## Compatibility considerations
- The added argument is a positional into a trailing optional parameter; behavior is identical to
  today until sibling `_01` implements the registry-aware resolution.

## Security considerations
- Closes the fail-open gap at the gateway write gate: without this line the gateway would keep
  using configured keys only even after `_01` lands.

## Rollback considerations
- N/A: revert the single commit line; no schema, config, or deploy change.

## Validation plan
- `uv run pytest tests/agent/test_repository_gateway.py tests/agent/test_tool_policy.py` — failing
  baseline first, then green.
- `uv run ruff check scripts/agent/repository_gateway.py tests/agent/test_repository_gateway.py` and
  `uv run ruff format --check` on both.
- `uv run mypy --no-namespace-packages scripts/ tests/agent/test_repository_gateway.py` — clean on
  the changed call.
- Diff-scoped coverage per `rules/toolchain.md` section 7 (`diff-cover --fail-under=90`).

## Completion criteria
- The gateway write gate denies a list-valued path argument with an out-of-root element (AC-1/AC-2
  gateway half).
- All existing tests in `tests/agent/test_repository_gateway.py` pass unchanged (AC-4).

## Out of Scope
- The gateway executor wiring, read gate, and audit logging in this file.
- The other two preflight call sites (siblings `20261104-065555_04/_06`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the failing-baseline tests to the companion test file first (Plan Phase 1); confirm they fail on current code | Completed | 20261104-153548 | 20261104-153705 | Baseline: 1 failing (executed despite out-of-root list element), 1 pin green |
| 2 | Apply the one-line call-site edit per Implementation > Procedure | Completed | — | 20261104-153705 | Land after sibling _01 |
| 3 | Re-run the companion suite (all green) and the validation sequence (`rules/toolchain.md`) | Completed | 20261104-153705 | 20261104-154641 | 9 companion tests green; full suite 11466 passed; diff-cover 100% |

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
- **Requirement ID**: REQ-003 (registry threaded at the gateway preflight call site)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261101-155552_pathkeys001_path-checks-skip-lists.md` (archived by
  commit `60d796777`; path corrected during Step 3a verification)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-065555
- **Related target files**: `scripts/agent/repository_gateway.py`, `tests/agent/test_repository_gateway.py`