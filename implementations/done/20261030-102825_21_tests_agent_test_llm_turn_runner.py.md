# Implementation Procedure: tests/agent/test_llm_turn_runner.py

## Goal

Lock the control-message propagation contract at the executor→LLM hand-off (row 09):
`run(..., control_message=...)` injects a single system-role control turn into the
per-request history copy without mutating persistent history (REQ-008), test-first
for row 09.

## Scope

**In scope:**
- `tests/agent/test_llm_turn_runner.py`: appended control-message propagation cases.

**Out of scope:**
- Engine-side detection and message construction (row 08, tested in row 20); guard
  wiring for unavailable tool results (toolhint001 row 11's own tests).

## Assumptions

- Sequencing (verified plan Context): `tests/agent/test_llm_turn_runner.py` is also
  targeted by toolhint001 row 11
  (`implementations/done/20261030-083821_11_tests_agent_test_llm_turn_runner.py.md`).
  toolhint001 precedes this plan in batch order and has landed — verified 2026-10-31: all 14
  toolhint001 procedures are archived in `implementations/done/`. Rebase verification
  2026-10-31 against the landed file (1094 lines): `TestRun:390`,
  `TestHistoryConstructionRoutedThroughAppendMessage:580`, `TestRunRoundAtomicity:794`;
  `TestControlMessageInjection` does not exist yet. `TestNormalizeForLLM`, named in earlier
  drafts, does not exist at HEAD and is not a target of this procedure.
- Red state: new cases fail until row 09 lands.

## Design decisions

- New class `TestControlMessageInjection` (new):
  - `control_message` (new) provided → exactly one extra system-role message in the
    request payload, positioned after the loop-state setup point (row 09 injection
    point `:79-80` region — rebase after toolhint001).
  - Persistent history invariant: `ctx.conv.history` identical before/after `run`
    (row 09 "per-turn, not durable" decision pinned as a test).
  - `control_message=None` (default) → payload byte-identical to today's shape
    (source-compatibility REQ-010 guard).
- Reuse the file's existing stub-LLM capture fixture to read the outgoing request
  payload; no new HTTP plumbing.

## Alternatives considered

- Asserting on the runner's internal state instead of the outgoing payload —
  rejected: the contract is what the LLM receives.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
1. After toolhint001 row 11 lands, re-locate anchor classes; append
   `TestControlMessageInjection` (new) at end of file.
2. Three cases per Design decisions.

### Method
Test-first: red until row 09 lands.

### Details
- Existing tests (including toolhint001's additions) untouched — characterization.

## Compatibility considerations

- If toolhint001 changes the history-composition path, the payload-shape case adjusts
  its expected baseline, not its assertion style (rebase point recorded in
  Assumptions).

## Security considerations

- Control message fixtures are synthetic strings; assert they are not logged into
  persistent stores by the runner (no session/DB writes during `run` with a control
  message).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_llm_turn_runner.py` (new class red before row 09,
  green after; all pre-existing green throughout);
  `uv run mypy --no-namespace-packages tests/agent`; `uv run lint-imports`.

## Completion criteria

- Injection position, single-message cardinality, history non-mutation, and default
  passthrough proven with row 09 landed on top of toolhint001's file state.

## Out of Scope

- Pending detection and retry_class policy (rows 07-08/20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rebase anchors after toolhint001 row 11 lands | Completed | 2026-10-31 | 2026-10-31 | toolhint001 archived; class appended at `:1097` after the rebased anchor classes; existing tests untouched (characterization). |
| 2 | Add TestControlMessageInjection (3 cases) | Completed | 2026-10-31 (row 09 cycle) | 2026-10-31 | Landed as 5 cases instead of 3: kwarg exists KEYWORD_ONLY/None default (default-passthrough guard), `_build_control_entry` carries `{role:"system", content}` only (single-message cardinality + schema-strict key set), None input -> no entry, `_stream_llm` appends the entry to the per-request history copy sent to the mocked `llm.stream` (outgoing-payload assertion, position = last entry) while `ctx.conv.history` stays identical (non-mutation criterion), and no-entry stream history identical. Deviation noted: the schema-validation failure branch (invalid entry -> log + no injection) is exercised via the strict key-set assertion, not a dedicated invalid-input case. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-31 | 2026-10-31 | `pytest tests/agent/test_llm_turn_runner.py` 40 passed (whole file incl. toolhint001 additions). `mypy --no-namespace-packages` on this file alone reports 61 errors vs 57 on the HEAD version: the 4 new ones (`llm.stream =` method-assign, `await_args` index) follow the file's pre-existing mock pattern; `tests/agent` is outside the mypy CI scope (`scripts/` + `tests/eventbus`), which passes clean in the batch gate run. `lint-imports` 6 kept in the batch gate run. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on toolhint001 row 11 implementation landing first | Yes | 2026-10-31 (toolhint001 plan fully Completed, all procedures archived) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (replay control message into turn context)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/agent/test_llm_turn_runner.py
