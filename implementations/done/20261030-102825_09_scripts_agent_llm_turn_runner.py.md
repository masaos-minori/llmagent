# Implementation Procedure: scripts/agent/llm_turn_runner.py

## Goal

Carry the workflow engine's replay control message into the turn context sent to the LLM
(REQ-008 hand-off point between executor and LLM).

## Scope

**In scope:**
- `scripts/agent/llm_turn_runner.py`: optional control-message parameter on `run`
  (`:62-70`) and its injection into the turn input.

**Out of scope:**
- Detection and message construction (row 08).

## Assumptions

- Sequencing (Needs Confirmation resolved by plan order): `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md` row 05
  (`implementations/done/20261030-083821_05_scripts_agent_llm_turn_runner.py.md`) also targets
  this file and landed first — verified 2026-10-31: procedure archived in `implementations/done/`.
  Rebase verification 2026-10-31 against the landed file: `run` at `:62`, workflow-context guard
  at `:73-78`, `self.llm_url = llm_url` at `:78` and `state = TurnLoopState()` at `:80` — all
  procedure anchors still exact; no `control_message` exists in the file yet.
- `run`'s existing required workflow-context guard (`:73-78`) stays unchanged.

## Design decisions

- New keyword-only parameter `control_message: str | None = None` on `run` (defaulted —
  every existing caller is source-compatible, REQ-010).
- Injection point: after `self.llm_url = llm_url` / `state = TurnLoopState()`
  (`:79-80`), before the history is sent — append a single system-role control turn
  containing `control_message` (new) to the copy of `ctx.conv.history` used for this request
  (does not mutate persistent history: replay instructions are per-turn, not durable
  conversation state).

## Alternatives considered

- Storing the message on the runner constructor — rejected: it is per-`run()` state; the
  runner instance is reused across turns.
- Mutating `ctx.conv.history` in place — rejected: would persist replay text into the
  session record.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
1. Extend the `run` signature with `control_message: str | None = None`.
2. When non-None, append the control entry to the per-request history copy before the LLM
   POST.
3. Keep the tool-execution loop untouched.

### Method
Signature-optional parameter; no new imports; no config boundary.

### Details
- The message text is fully constructed by row 08; this module does not interpret it.

## Compatibility considerations

- `tests/agent/test_llm_turn_runner.py` (row 21) and any `run(...)` call sites without the
  kwarg compile and behave identically (default None).
- Coexistence with the toolhint001 row-05 edit: both add keyword-level extensions; apply
  in plan order to avoid signature conflicts (Assumptions).

## Security considerations

- Control content originates from workflow-owned state (row 08); no user-input surface
  added here.

## Rollback considerations

- Revert the commit: row 08 stops passing the kwarg (its own fallback = no call), so no
  dangling caller results from reverting this row alone if rows land in plan order.

## Validation plan

- Row 21 (`tests/agent/test_llm_turn_runner.py`, test-first): kwarg present in the request
  copy when provided; persistent history unchanged after such a run; default-None call
  byte-identical to today.
- `uv run pytest tests/agent/test_llm_turn_runner.py`; `uv run mypy --no-namespace-packages
  scripts/ tests/agent`; `lint-imports`.

## Completion criteria

- A `run` call with a control message shows the message in exactly the outbound request
  history; session history and subsequent turns are unaffected; existing tests pass
  unmodified.

## Out of Scope

- Replay decision logic and message wording (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the kwarg + injection | Completed | 20261031-173000 | 20261031-175803 | `control_message: str \| None = None` keyword-only on `run` (anchors `:62`/`:73-78` confirmed exact before edit). `_build_control_entry` validates via `agent.message_schema.validate_message`; the entry is schema-strict `{role: "system", content}` only — the intended `source`/`_ephemeral` provenance keys were rejected by the role whitelist/ephemeral-source policy (recorded deviation; provenance travels in the row-08 message header text instead). Injection is a per-request copy in `_stream_llm` (`[*ctx.conv.history, entry]`); persistent history and the `_stream_llm_final_answer` request are untouched. Validation failure logs and proceeds with no injection |
| 2 | Land row 21 tests (test-first) | Completed | 20261031-173000 | 20261031-175803 | 5 cases in `tests/agent/test_llm_turn_runner.py` (`TestControlMessageInjection`): kwarg present keyword-only with None default, entry carries the message text, None for no message, `_stream_llm` appends to the sent copy while persistent history stays identical, no-entry sent history byte-identical |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-173000 | 20261031-182400 | Batched with rows 07/08: gates fast all Pass, lint-imports 6 kept, ruff clean, mypy green, bandit at the 3-medium master baseline. Batch full suite (post orchestrator-test fix): 10744 passed / 8 skipped / 0 failed in 7m17s; `diff-cover --compare-branch=master --fail-under=90`: 92% (429 changed lines, 33 missing, all in `scripts/shared/mcp_dedup.py` defensive branches) |

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
- **Requirement ID**: `REQ-008` (control message reaches the LLM)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/agent/llm_turn_runner.py
