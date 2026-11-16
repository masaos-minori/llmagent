## Goal

Add an explicit `lease_duration_sec` to the single `begin_stage_if_new()` call in `tests/agent/workflow/test_state_store.py` so it satisfies the now-required argument (`REQ-003`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` (seq 01) makes `lease_duration_sec` a required positive `int`; line 407 currently omits it and will raise `TypeError` once that lands.
- Verified via `rg -n "begin_stage_if_new\("` over `tests/agent/workflow/test_state_store.py`: exactly one direct call at line 407 (`begin_stage_if_new(store.get_connection(), ...)`).
- The two raw `INSERT INTO attempts` in this file (lines 90 and 464) already include `owner_id`/`lease_expires_at` on continuation lines — no change needed.

## Design decisions
- Use a single positive value (e.g., `300`); the site does not assert lease timing.

## Alternatives considered
N/A: mechanical call-site fix.

## Implementation
### Target file
`tests/agent/workflow/test_state_store.py`
### Procedure
Add `lease_duration_sec=300` to the `begin_stage_if_new()` call at line 407.
### Method
Single-argument insert.
### Details
- Line 407-408: add `lease_duration_sec=300` inside the existing
  ```python
          rec = begin_stage_if_new(
              store.get_connection(), "task-att-1:s1:1", "task-att-1", "s1"
          )
  ```
  call.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_state_store.py` — no `TypeError` from the missing required argument.

## Completion criteria
- The line 407 `begin_stage_if_new()` call supplies `lease_duration_sec`; the suite passes.

## Out of Scope
Other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (every call site supplies an explicit lease)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/agent/workflow/test_state_store.py`
