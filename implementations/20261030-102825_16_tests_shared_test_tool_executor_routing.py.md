# Implementation Procedure: tests/shared/test_tool_executor_routing.py

## Goal

Keep the `X-Idempotency-Key` propagation suite green under deterministic keys and pin the
new key shape (REQ-001 header behavior; test-first companion of row 01).

## Scope

**In scope:**
- `tests/shared/test_tool_executor_routing.py`: adapt key-shape assertions; add
  same-call-identity assertions.

**Out of scope:**
- Transport implementation (row 01).

## Assumptions

- Verified anchors: header-presence assertions at `:236` and `:256`
  (`assert "X-Idempotency-Key" in call_kwargs["headers"]`) and the reuse-across-retries
  test at `:349` / key-collection at `:373` stay valid as-is (presence + single-value
  semantics are shape-agnostic); only assertions that pin UUID4 format (if any surface in
  helper comparison) need the deterministic-shape update — audit these four sites first.

## Design decisions

- Add one assertion per logical call: keys captured at `:373`-style collection must be
  `len(set(keys)) == 1` (already true) **and** equal to the locally re-derived
  `derive_idempotency_key` (new) value — pins determinism end-to-end through the executor path.
- Keep dry-run/non-side-effect skips byte-identical (REQ-010 preserved routing behavior).

## Alternatives considered

- Replacing the whole suite with new tests — rejected: existing assertions are
  characterization locks for preserved behavior.

## Implementation
### Target file
`tests/shared/test_tool_executor_routing.py`

### Procedure
1. Audit `:236`, `:256`, `:349`, `:373` sites; keep shape-agnostic ones untouched.
2. Add derivation-equality assertions per Design decisions at the retry-reuse test.

### Method
Test-first: derivation-equality cases fail until row 01 lands.

### Details
- No fixture churn; same stub-capture style.

## Compatibility considerations

- N/A: additive + minimal assertion tightening only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_tool_executor_routing.py` (partial red until row 01,
  green after); `uv run mypy --no-namespace-packages tests/shared`.

## Completion criteria

- Executor-routed calls carry the derived key verbatim; all pre-existing cases pass
  unmodified.

## Out of Scope

- Store/dispatcher behavior (rows 02/04/19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Audit the four key sites; add derivation-equality assertions | Pending | — | — | Red until row 01 lands |
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
- **Requirement ID**: `REQ-001` (header propagation under deterministic keys)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/shared/test_tool_executor_routing.py
