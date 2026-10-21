## Goal

Lock in the `dry_run=True` no-op contract as regression coverage by extending the
existing dry-run flow test: assert `execute` is called with `dry_run=True` and that a
fake executor records no downstream mutation (REQ-001, REQ-003).

## Scope

- Modify `tests/agent/test_tool_approval_preflight.py` only: extend
  `TestCheckApprovalDryRun` with a test asserting no downstream mutation under a fake
  executor.

## Assumptions

- Extending the existing dry-run flow test does not change the behavior of approved
  calls.
- The existing parametrized `test_plan_mode_blocks_every_non_read_only_tool` (L823-854)
  already exercises many of the same tools through a different path; this new test
  targets the pre-approval dry-run path specifically.

## Design decisions
- Add a focused new test method to `TestCheckApprovalDryRun` rather than rewriting
  existing tests, so the dry-run flow assertions stay colocated with the existing
  dry-run coverage.

## Alternatives considered
- Rewriting the existing dry-run tests to add the mutation assertion: rejected; extend,
  do not rewrite, to avoid destabilizing passing assertions.

## Implementation
### Target file
`tests/agent/test_tool_approval_preflight.py`

### Procedure
1. In `TestCheckApprovalDryRun`, add a test that runs `check_approval` for a write tool
   (e.g. `write_file`) with `approval_dry_run_tools` enabled and a fake executor whose
   `execute` records whether any mutation would occur, then asserts:
   - `execute` was awaited once with `dry_run=True` (mirrors the pattern already used in
     `test_dry_run_for_create_directory` at L566-568 and `test_github_tool_triggers_dry_run`
     at L600-602).
   - The recorded downstream mutation count is zero under `dry_run=True`.
2. Keep the new test consistent with the module's `_make_cfg` / `_make_ctx` fixtures and
   the `ToolCallResult` shape used by the other dry-run tests.

### Method
- Open `tests/agent/test_tool_approval_preflight.py`; locate `TestCheckApprovalDryRun`
  (L505-619) and the existing `dry_run is True` assertions (L566-568, L600-602) as the
  template for capturing `execute.await_args`.
- Build the fake executor as an `AsyncMock` whose `execute` returns a `ToolCallResult`
  with `is_error=False` and record the passed `dry_run` value via `side_effect`.

### Details
- Existing dry-run tests already assert `execute` is called with `dry_run is True`:
  `test_dry_run_for_create_directory` (L566-568) and `test_github_tool_triggers_dry_run`
  (L600-602). They do **not** assert that no downstream mutation occurs; the new test
  closes that gap by asserting the no-op contract end-to-end through `check_approval`.
- Fixture helpers: `_make_cfg(**overrides)` (L43) and `_make_ctx(cfg)` (L78) set
  `ctx.services_required.tools = AsyncMock()` by default.

## Compatibility considerations
Test-only change; no impact on production code, interfaces, or config.

## Security considerations
The new test encodes the security invariant that a pre-approval dry-run performs no
side effect. It guards against a future change making `dry_run` advisory (which would
turn the preview into an unapproved execution).

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_tool_approval_preflight.py` | Unit (dry-run flow) | `uv run pytest tests/agent/test_tool_approval_preflight.py` | New assertion passes; existing green |
| Whole module | Type check + lint | repo type-check + lint | Pass |

## Completion criteria
- The new test asserts `execute` is called with `dry_run=True` and that a fake executor
  records no downstream mutation (REQ-001, REQ-003).
- The full `tests/agent/test_tool_approval_preflight.py` suite passes; type check + lint pass.

## Out of Scope
- Adding a REQ-002 whitelist-membership test (only if a tool was removed per the
  code-row document).
- Changing the behavior of approved calls.
- Rewriting existing dry-run tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `TestCheckApprovalDryRun` with the no-downstream-mutation assertion (REQ-001, REQ-003) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: issues/20261021-161803_dryrun_preapproval_tool_execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261021-201654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-204811
- **Related target files**: tests/agent/test_tool_approval_preflight.py
