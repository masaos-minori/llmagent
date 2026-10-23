## Goal

Cover the pure pairing function's contract directly (`REQ-004`, `REQ-009`,
`REQ-010`, `REQ-013`): missing ids are synthesized, already-answered ids are not,
a duplicated declared id yields one row, an empty declaration yields none, output
order equals declared order, and each stop-reason member yields its own distinct
payload. This is the cheapest place to detect a contract change in
`scripts/agent/tool_result_pairing.py`.

## Scope

New test file `tests/agent/test_tool_result_pairing.py`. Pure-function coverage
only: no fixtures, no monkeypatching, no session. Reference reads:
`scripts/agent/tool_result_pairing.py::pair_round_results`,
`scripts/agent/tool_enums.py::ToolCallStopReason`,
`scripts/agent/tool_result_formatter.py::format_error_payload` (the payload this
test asserts is *not* imitated).

## Assumptions

- `pair_round_results(declared, answered, collected, stop_reason)` is importable
  with no construction side effects, so tests build arguments directly.
- `collected` is inspected by keys only; tests may pass a plain dict.

## Design decisions

- One `pytest` class per invariant from the plan's Tests section:
  `TestPairingIsByDeclaredId`, `TestStopReasonIsClosed`,
  `TestOrderIsDeclaredOrder`, `TestSynthesizedRowValidates`. Each asserts against
  the returned pairs directly.

## Alternatives considered

- Driving pairing through `execute_all_tool_calls` with a real session — heavier,
  needs a session fixture; the pure test is the intended cheap contract gate
  (`DR-003`).

## Implementation

### Target file

`tests/agent/test_tool_result_pairing.py` (new)

### Procedure

Create the file with four test classes:

1. `TestPairingIsByDeclaredId`:
   - Declared ids absent from `collected` (and not in `answered`) are synthesized;
     assert the returned ids equal the missing ones.
   - Ids present in `collected`, in `answered` (preparation failures), or in
     denials are not synthesized.
   - A duplicated declared id yields exactly one row.
   - An empty declaration yields no rows.
2. `TestStopReasonIsClosed`:
   - Each member of `ToolCallStopReason` yields its own distinct text.
   - Neither text equals `format_error_payload()` output nor the
     `"Tool execution denied by user."` literal (`REQ-004`).
   - An unknown reason cannot be constructed (the enum has two members).
3. `TestOrderIsDeclaredOrder`:
   - Fill `collected` in a different order than `declared`; assert output order
     equals declared order (`REQ-009`, the DAG/order behavior preserved at
     `tool_runner.py:330-332`, `:383-385`).
4. `TestSynthesizedRowValidates`:
   - Each synthesized message passes `validate_message()` with `role='tool'` and
     `tool_call_id` set; each row tuple is shaped like
     `("tool", content, None, tool_call_id)`.

### Method

- Plain `pytest` functions/methods; import `pair_round_results` and
  `ToolCallStopReason` directly. No `conftest` fixtures.

### Details

- `answered` models prep-failure ∪ denial ids; pass it as a set to exercise the
  "already answered" branch.

## Compatibility considerations

### Corrections found while implementing

- Written as `tests/agent/test_tool_result_pairing.py` against the 4-argument signature; added `TestBuildDeniedMessages` because that helper moved into the pure module. No fixtures or patching.


- New file; does not touch any existing test.

## Security considerations

- N/A: test-only, pure logic.

## Rollback considerations

- Delete the new file; nothing else references it.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_pairing.py -q --timeout=120` — all
  four classes pass.
- `uv run ruff check tests/`, `uv run ruff format --check tests/`.
- Negative control (AC-7): temporarily make `pair_round_results` return `[]` and
  confirm the missing-id assertions fail; revert.

## Completion criteria

All four invariant classes pass; missing ids synthesize, already-answered ids do
not, duplicates collapse to one row, empty declaration yields none, order matches
declared order, and both payloads are distinct and non-error-shaped.

## Out of Scope

- The round-level pairing behavior — `tests/agent/test_tool_runner.py` (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add pure-function coverage of REQ-004, REQ-009, REQ-010, REQ-013 | Completed | 20261023-170140 | 20261023-170140 | Phase 1 implemented; full suite passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-170140 | 20261023-170140 |  |

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
- **Requirement ID**: REQ-004, REQ-009, REQ-010, REQ-013
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `tests/agent/test_tool_result_pairing.py`