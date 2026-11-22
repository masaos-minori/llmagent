## Goal

Create the approval tests that prove no answer crossover, HIGH fail-closed, masked previews with redaction before truncation, and audit provenance (REQ-005, REQ-006, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new test file. Write these first in Phase 4; they fail until the approval, output, audit, and model procedures land.

## Assumptions

- Verified: no `test_tool_approval.py` exists; five `test_tool_approval_*.py` siblings exist and are not extended here (Plan Step 3).

## Design decisions

- Use a fake input controller returning scripted `InputResult` values and a captured output port, as the sibling tests do for `check_approval`.
- Cover consecutive approval requests with no answer crossover and a stale `y` after a timeout.

## Alternatives considered

Rejected: extending `test_tool_approval_paths.py` (the mcpdl003 procedure also edits it).

## Implementation
### Target file
`tests/agent/test_tool_approval_request_binding.py` (new)

### Procedure
1. Test stale answer: a timed-out request followed by another approval must not be approved by the late line.
2. Test HIGH: dry-run error result and dry-run execution failure both deny; MEDIUM follows the config field both ways.
3. Test redaction: secrets in args, dry-run output, and error text never appear in the printed prompt, and redaction precedes truncation (a secret straddling the cut).
4. Test audit: request id, preview source, and fallback reason are present; the answer text is absent.

### Method
Pytest functions with `asyncio` marks as used by sibling approval tests.

### Details
- Use fixtures from `tests/agent/_config_test_defaults.py` for config defaults.

## Compatibility considerations

N/A: test-only.

## Security considerations

These tests are the guard for AC-1 and AC-4.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_request_binding.py -q`
- `uv run ruff check tests/agent/test_tool_approval_request_binding.py && uv run mypy tests/agent/test_tool_approval_request_binding.py`

## Completion criteria

- Each listed behavior has a passing test; the file passes ruff and mypy.

## Out of Scope

Existing approval test files, signal and Memory tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-005`, `REQ-006`, `REQ-007` (approval binding, previews, audit) and `AC-1`, `AC-4`
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `tests/agent/test_tool_approval_request_binding.py`
