## Goal

Add `ROUND_INFLIGHT` (new) to `ToolCallStopReason` (Plan D2 Option A, the recommended route) so
a round stopped by cancellation can answer an in-flight call with a self-describing
outcome-unknown reason instead of reusing `ROUND_NOT_COMPLETED` (REQ-002; AC-001).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_enums.py` row (seq 01) of
`plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`. This is
the first document of the plan: it declares `ROUND_INFLIGHT` (new) that the seq 02
(`_STOP_TEXT` mapping) and seq 03 (partition in `complete_round`) documents consume.
Intra-plan execution order: 01 → 02 → 03 → 04, then the plan-wide validation.
The row has no companion test file of its own: its enum-contract tests are owned by the
seq 02 document (companion of the `scripts/agent/tool_result_pairing.py` row).

## Assumptions
- Verified against current source (20261103): `ToolCallStopReason` (tool_enums.py:50-54)
  is a `StrEnum` with exactly `GUARD_STOP = "guard_stop"` and
  `ROUND_NOT_COMPLETED = "round_not_completed"`. Construction sites: `tool_runner.py` 523
  (`ROUND_NOT_COMPLETED`, inside the `except BaseException` handler of
  `execute_all_tool_calls`) and 527 (`GUARD_STOP`); the plan row cites 518/522 — line
  drift only, symbols unchanged. Match site: only `tool_result_pairing.py::_STOP_TEXT`
  (19-26). No `isinstance`/exhaustive-match elsewhere (rg over `scripts/` confirmed).
  Re-verified 20261104 after blockio001 landed: construction sites are now `tool_runner.py`
  526 (`ROUND_NOT_COMPLETED`) and 530 (`GUARD_STOP`); symbols unchanged.
- `tool_enums.py` is 1112 B (gate 20480 B) — ample (re-measured 20261104: 1112 B).
- The only test that enumerates the members is `TestStopReasonIsClosed` in
  `tests/agent/test_tool_result_pairing.py` (43-61), which asserts
  `len(set(texts.values())) == len(ToolCallStopReason) == 2` and
  `all("not executed" in t ...)`; seq 02 updates it in the same commit (its companion
  section). Landing seq 01 without seq 02 would break that test — 01 and 02 commit together.
- Red-first note: with no companion section here, the red tests live in the seq 02/03/04
  documents; this document's change is confirmed by seq 02's `_STOP_TEXT[reason]` lookups
  raising `KeyError` pre-change only in combination — write seq 02's red tests first,
  then land 01+02 together (recorded in seq 02's Procedure).

## Design decisions
- Member name and value: `ROUND_INFLIGHT` (new), value "round_inflight" (next to the existing two,
  same style). It is a reason a *call* was answered with, matching the existing semantics
  of the enum ("Why a declared tool call was not executed in a round" — docstring gets one
  clarifying clause that an in-flight call's execution outcome is unknown).
- No other module changes: construction and matching arrive in seq 03/04; the enum module
  itself only gains the member.

## Alternatives considered
- Plan D2 Option B (no new member, per-id text selection inside `pair_round_results`):
  rejected for the implementation per the Plan's recommendation of Option A
  ("first-class, self-describing reasons"); Option B stays the owner's fallback if the
  enum-contract expansion is later deemed undesirable (Plan Risks mitigation).

## Implementation
### Target file
`scripts/agent/tool_enums.py`

### Procedure
1. Add `ROUND_INFLIGHT` (new), value "round_inflight" (new) to `ToolCallStopReason` after
   `ROUND_NOT_COMPLETED`.
2. Extend the class docstring by one clause: an in-flight call was dispatched but its
   server-side outcome is unknown.

### Method
One enum member plus a docstring clause; no logic in this module.

### Details
- The member must stay mapped in `_STOP_TEXT` (seq 02) in the same commit so the dict
  stays total — `pair_round_results` indexes `_STOP_TEXT[stop_reason]` directly (a missing
  entry is a `KeyError` at round completion).
- `tool_enums.py` is imported by the agent layer today (`tool_result_pairing.py`,
  `tool_runner.py`, `tool_round_completion.py` via TYPE_CHECKING-free import); no
  `lint-imports` contract change.

### Companion test files
- None. The enum-contract tests (member count, text uniqueness) belong to
  tests/agent/test_tool_result_pairing.py, covered as companion of the seq 02 document.

## Compatibility considerations
- Adding a `StrEnum` member is additive: persisted data stores row *text*, not the enum
  value, so no schema or stored-data impact (REQ-004 "no schema change").
- `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` names the two
  reasons today (its round-completion paragraph); seq 05 updates it. Until seq 05 lands,
  the doc under-describes the reasons — same-commit grouping 01+02+03 with 05 before the
  plan-wide validation keeps docs and code consistent.

## Security considerations
N/A: no new input or trust boundary.

## Rollback considerations
- One-line additive change; reverting the commit (together with seq 02/03/04) restores the
  two-member enum.

## Validation plan
1. Covered by seq 02's companion run: `uv run pytest tests/agent/test_tool_result_pairing.py -q`
   (this document has no tests of its own).
2. Static: `uv run ruff check scripts/agent/tool_enums.py`, `uv run ruff format --check`
   on it, `uv run mypy scripts/agent/tool_enums.py`.
3. Gates: `uv run python tools/check_module_size.py` (1112 B, ample), `uv run lint-imports`.
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after
   all four code documents of this plan are executed.

## Completion criteria
- `ToolCallStopReason` has exactly three members including `ROUND_INFLIGHT` (new)
  (value `"round_inflight"`); `seq 02`'s updated `TestStopReasonIsClosed` passes.

## Out of Scope
- `_STOP_TEXT` mapping and its tests (seq 02), the partition in `complete_round` (seq 03),
  the dispatch marking (seq 04), the docs paragraph (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the member and docstring clause (Procedure 1-2), committed together with seq 02 | Completed | 20261104-091538 | 20261104-091712 | blockio001 landed (f9573d415); anchors re-verified 20261104 (finish calls now 526/530) |
| 2 | Run this document's static checks (Validation plan 2-3) | Completed | — | 20261104-091712 |  |

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
- **Requirement ID**: REQ-002 (in-flight vs never-dispatched texts, via the recommended
  new enum member), REQ-004 (no schema change)
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-121149
- **Related target files**: `scripts/agent/tool_enums.py`