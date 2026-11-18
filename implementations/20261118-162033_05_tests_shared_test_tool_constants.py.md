## Goal

Add a cross-source consistency test class to `tests/shared/test_tool_constants.py`
that compares `RETRYABLE_TOOLS` against the repository `config/mcp_dedup.toml`
`[retry_class]` map — the test that makes the mirror relationship enforced.
(`REQ-001` toml validated against the owner constant)

## Scope
**Release unit**: N/A: not part of a release unit (lands in Phase 3, after the
`retry-class-load-gate` unit; it is only runnable once the Phase 1 rename exists)

## Assumptions

- The test reads the repository config file directly (not the production overlay);
  the overlay mirrors it (`deploy.sh` `cp`), per plan Assumptions.
- It runs after procedures 01-03 in `seq` order, so `search_web` is already the live
  key when the test executes.

## Design decisions

- Assert three conditions against `load_dedup_config`-parsed or `tomllib`-parsed
  repository config: retryable keys == `RETRYABLE_TOOLS` (two-way set equality);
  every key in `get_all_mcp_tool_names()`; every `non_retryable` key not in
  `RETRYABLE_TOOLS`.
- This is where full set equality lives (loader enforces per-key only) — plan
  Assumptions.

## Alternatives considered

- **Put equality in the loader.** Rejected at plan time (fixtures with partial maps
  would all break); the test is the enforcement point.

## Implementation
### Target file
`tests/shared/test_tool_constants.py`

### Procedure
1. Add a new test class `TestRetryClassConfigConsistency (new)` that loads
   `config/mcp_dedup.toml` (repo root resolved from the test file's location, as
   other tests in `tests/shared/` already do for config paths) with `tomllib`.
2. Assert `{k for k, v in retry_class.items() if v == "retryable"} == RETRYABLE_TOOLS`.
3. Assert every key is in `get_all_mcp_tool_names()` and every `non_retryable` key is
   not in `RETRYABLE_TOOLS`.

### Method
Parse with `tomllib` directly instead of `load_dedup_config` so the test compares the
two source artifacts independently of the loader gate added in procedure 03.

### Details

- Keep existing tests in the file unchanged; new class only.

## Compatibility considerations

- Tests only; no production import graph impact.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_tool_constants.py -q` — new class passes against
  the repository config (AC-2).
- Mutation spot-check (plan Validation plan): locally add/remove one
  `RETRYABLE_TOOLS` member, confirm this test fails, revert.

## Completion criteria

- The test fails on any extra, missing, or contradictory entry and passes on the
  shipped config (AC-2, AC-3).

## Out of Scope

- Changes to `tests/agent/test_tool_runner.py` (its membership assertions must keep
  passing unchanged — regression check, not an edit).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the consistency test class | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (cross-source consistency enforcement)
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-153543_adrchk018_mcp-retry-classes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162033
- **Related target files**: `tests/shared/test_tool_constants.py`
