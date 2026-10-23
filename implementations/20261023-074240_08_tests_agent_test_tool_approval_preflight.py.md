## Goal

Re-point the `patch("asyncio.to_thread", …)` sites in `tests/agent/test_tool_approval_preflight.py` to the new private read seam in `scripts/agent/tool_approval.py`, and re-point `:805`'s "did not prompt" assertion to the same seam — without changing any assertion, parameterization, or case name (`plans/20261022-040200_plan.md`, REQ-009; AC-6, AC-8).

## Scope

Modify only `tests/agent/test_tool_approval_preflight.py`: change the patch origin string from `"asyncio.to_thread"` to the module's new private read seam, and move the `:805` assertion to the same seam. No assertion value, parameterization, or case name changes.

## Assumptions

- Once `tool_approval.py` no longer calls `asyncio.to_thread`, those patches stop intercepting the read, so the cases would read captured stdin instead — the patch origin must move with the call site.
- The private seam is a single, stable, patchable symbol (see row 4), so all sites can be re-pointed to it.

## Design decisions

- A mechanical, find-and-replace of the patch-target string across the file, plus a targeted edit of the single `:805` assertion. Expectations and parameterizations are left byte-identical.

## Alternatives considered

N/A: the Plan fixes the approach (mechanical re-point); this row executes it.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. Replace every `patch("asyncio.to_thread", …)` with `patch("<module>.<private_seam>", …)` pointing at the new seam added in row 4.
2. Replace `:805`'s `mock_thread.assert_not_called()` (the "did not prompt" assertion) with an assertion against the same seam.
3. Do not change any expected value, parameterization, or case name.

### Method

- Use a scoped search for `asyncio.to_thread` to enumerate the exact sites, then apply the substitution uniformly.
- Verify the re-point is complete: `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_preflight.py` returns `0` (`AC-6`).

### Details

- **Discrepancy note**: the Plan states 25 `asyncio.to_thread` sites; against current HEAD `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_preflight.py` returns 26. The implementer MUST re-point every existing site regardless of the exact count — the count is a check, not a target. Flag before proceeding if the extra site does not map to an approval-prompt read.

## Compatibility considerations

N/A: test-only change; the suite's expectations are unchanged.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_approval.py` | Regression over the whole approval suite with re-pointed patch targets, plus an `EOFError` propagation case. | `uv run pytest tests/agent/test_tool_approval_preflight.py -q` ; `grep -n "to_thread\|import asyncio" scripts/agent/tool_approval.py` ; `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_preflight.py` | Approval semantics cases pass with unchanged expectations; grep returns nothing in the module; count in the test file is 0 (AC-6). |

## Completion criteria

- All approval-semantics cases pass with unchanged expectations.
- `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_preflight.py` returns 0.

## Out of Scope

Changing any assertion value, parameterization, or case name. Modifying `tool_approval.py` beyond the private seam (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-point the `asyncio.to_thread` patch targets and `:805`'s assertion to the private seam | In Progress | 20261023-074240 | — | REQ-009; AC-6, AC-8 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Plan states 25 `asyncio.to_thread` sites; current HEAD reports 26. Non-blocking: re-point every existing site; verify the extra site maps to an approval-prompt read before proceeding. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
