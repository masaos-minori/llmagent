# Implementation Procedure: test_llm_turn_runner.py bounded-loop and measurement tests

## Goal

Prove end-to-end that a persistently unavailable tool is bounded by the guard and that
LLM tool definitions never change, and run the REQ-006 prompt-cache/context impact
measurement in `tests/agent/test_llm_turn_runner.py` (REQ-002, REQ-003, REQ-006; plan
AC-2, AC-5).

## Scope

**In scope:**
- `tests/agent/test_llm_turn_runner.py`: new integration tests for the runner bound and
  the token-estimation comparison harness.

**Out of scope:**
- Guard unit behavior (row 10); invoker hint unit behavior (row 09).

## Assumptions
- Verified at HEAD `124e340b4`: file exists with 30 runner tests using mocked
  transports/LLM; `TurnResult` shape (`turn_result.py:22-25`); runner guard chain
  location (`llm_turn_runner.py:116-133`). Test-first: new tests fail until rows 04/05
  land. Measurement tooling: `estimate_tokens(history)` and
  `estimate_tokens_for_text` exist (`shared/token_estimation.py:48`, `:19`).

## Design decisions
- Integration test: patch `tool_empty_result_max_repeats=2`, make the mocked transport
  return a result with `availability_hint(reason=server_unavailable, ...)` every call;
  assert the turn ends with `action="fail"`, `reason="unavailable_repeat"` before
  `max_tool_turns` exhaustion, and that the LLM request captured per turn contains an
  identical tool-definitions block across turns (REQ-002/AC-1 at the request boundary).
- Disabled default test: with `tool_empty_result_max_repeats=0` the same scenario
  proceeds exactly as today (characterization of default-off).
- REQ-006 measurement (plan Design "Measurement"): build two representative tool-result
  message histories — hinted vs unhinted (same base text, hint adds only the structured
  error-channel content) — compare `estimate_tokens()` totals and per-category deltas;
  assert the system prompt + tool-definition region token count is **identical** between
  variants (volatile content never enters prompt-cached regions, AC-5) and print/record
  the tool-result-region delta (tokens) — the number must be copied into the plan's
  Execution Status Notes (plan step 2 row already reserves the note).

## Alternatives considered
- Live-LLM measurement: rejected — the plan specifies `token_estimation` on representative
  payloads; deterministic and CI-safe.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
1. Keep all 30 existing tests byte-identical.
2. Append the bounded-loop integration tests.
3. Append the token-estimation comparison test with the recorded-delta convention.

### Method
- Reuse existing runner fixtures (mocked LLM history, mocked tool executor) and inject
  hinted `ToolCallResult`s through the executor mock.

### Details
- The measurement test is deterministic (fixed fixture strings); its printed number is
  for the Execution Status note, its assertions are structural (identical
  cached-region counts).

## Compatibility considerations
- `toolexec001` overlap (plan Risks): this file is shared; land whichever plan lands
  first and rebase appended classes on top of current HEAD (no edits to the other
  plan's tests).

## Security considerations
- Assert the turn answer equals the guard's fixed summary (no server free-text widened
  into answers).

## Rollback considerations
- Delete appended classes to revert; measurement numbers recorded in the plan note stay
  as historical evidence.

## Validation plan
- `uv run pytest tests/agent/test_llm_turn_runner.py -v` — new tests fail before rows
  04/05, green after; REQ-006 delta recorded in the plan Execution Status note
  (AC-5 gate: widening hint placement is blocked until recorded).

## Completion criteria
- Bounded termination observable end-to-end; definitions immutable at request boundary;
  measurement delta recorded in the plan note; 30 existing tests untouched.

## Out of Scope
- Rows 04/05 implementation, guard unit tests (row 10), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append bounded-loop integration tests (fail before rows 04/05 land) | Pending | — | — | |
| 2 | Append token-estimation comparison test; record REQ-006 delta in plan Execution Status notes | Pending | — | — | |
| 3 | Confirm 30 existing tests byte-identical and green | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-006`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `tests/agent/test_llm_turn_runner.py`
