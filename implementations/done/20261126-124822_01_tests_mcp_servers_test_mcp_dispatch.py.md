## Goal
- Pin keyless, empty-key, and whitespace-key rejection at the programmatic dispatcher for every tool in `ALL_SIDE_EFFECTING_TOOLS`, not only `write_file` (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new test cases in `tests/mcp_servers/test_mcp_dispatch.py`.
- Out of scope: any change to `dispatch.py`, which already rejects keyless side-effecting calls (`scripts/mcp_servers/dispatch.py:418-428`).

## Assumptions
- No code row of the Plan names this file in its Related Tests, so it keeps its own document.
- Verified in Step 3a: the existing keyless test covers one tool (`write_file`) and uses the `_ctx` helper (`test_mcp_dispatch.py:25-40,168-190`); `ExecutionContext.__post_init__` strips the key, so a whitespace key becomes empty (`scripts/mcp_servers/execution_context.py:47`).
- This test is written first (the Plan's AI instruction) and is expected to pass on current code; its value is coverage of the full real set.
- High-churn file (10 commits in 30 days): add a new class rather than editing existing tests, and rebase before editing.

## Design decisions
- Iterate `sorted(ALL_SIDE_EFFECTING_TOOLS)` through `pytest.mark.parametrize`, so a tool added to the set is covered automatically.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
1. Add a new test class for the keyless sweep.
2. Parametrize over each tool in `ALL_SIDE_EFFECTING_TOOLS` and over the keys `""`, `"   "`, and an absent key (context built with the default key).
3. For each case, register a handler for that tool name that records calls, call `dispatch_tool`, and assert `is_error`, `error_type == "idempotency_key_required"`, `execution_mode == "no_op"`, `side_effect_applied is False`, an uncalled handler, and an empty duplicate cache.
4. Add a control case per tool group (or one parametrized valid-key case) showing a valid key reaches the handler, and one assertion that the set is non-empty.

### Method
- Reuse the module's `_ctx` helper and its fixtures; do not change them.

### Details
- Do not weaken or edit the existing `write_file` keyless tests.

## Compatibility considerations
- Test-only.

## Security considerations
- N/A: no secret involved; handlers are stubs.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -k keyless`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Every tool of the real set is rejected for each missing, empty, and whitespace key before its handler runs; the valid-key control passes; existing tests untouched and passing; all validation commands pass.

## Out of Scope
- Dispatcher changes, the HTTP boundary sweep (seq 16 companion), and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests described in Implementation > Procedure | Completed | 20261126-131011 | 20261126-131011 | Changed: tests/mcp_servers/test_mcp_dispatch.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-131011 | 20261126-131011 | ruff format/check, mypy (CI invocation), lint-imports, bandit, module size, gates passed; full suite (parallel, coverage): 27 failed and 88 errors in tests/agent/* from a pre-existing NameError in scripts/agent/commands/cmd_mcp.py (RuntimeToolRegistry annotation), unrelated to this change; no failing test touches a changed file; targeted tests pass |

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
- **Requirement ID**: `REQ-001` (keyless rejection over the real side-effecting set, programmatic path)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch.py`
