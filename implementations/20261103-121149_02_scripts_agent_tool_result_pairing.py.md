## Goal

Give `pair_round_results` the outcome-unknown text for in-flight calls by mapping the seq
01 enum member in `_STOP_TEXT` (dict stays total), and pin the closed-set text contract
with the companion unit tests (REQ-002, REQ-003, REQ-004; AC-003, AC-004).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_result_pairing.py` row (seq 02) and its companion test row
`tests/agent/test_tool_result_pairing.py` (seq 07 of the plan table, companion-eligible, no
document of its own) of
`plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`. Runs after
`implementations/20261103-121149_01_scripts_agent_tool_enums.py.md` (it consumes
`ROUND_INFLIGHT` (new) declared there) and before seq 03/04. Intra-plan execution order:
01 → 02 → 03 → 04, then the plan-wide validation.

## Assumptions
- Verified against current source (20261103): `_STOP_TEXT` (tool_result_pairing.py:19-26)
  maps the two existing members; `pair_round_results` (29-51) takes one `stop_reason`,
  reads `text = _STOP_TEXT[stop_reason]` once, and synthesizes one row per missing id
  with a `seen` set; rows are `("tool", text, None, call_id)`. radon: `pair_round_results`
  A(5). Module is 2503 B (gate 20480 B) — ample.
- `ROUND_INFLIGHT` (new) is declared by the earlier sibling document (seq 01).
- The companion file's `TestStopReasonIsClosed` (43-61) today asserts
  `len(set(texts.values())) == len(ToolCallStopReason) == 2` and
  `all("not executed" in t for t in texts.values())`. It is a whole-enum closure test: it
  must be updated in the same commit as seq 01's member or it fails red for the wrong
  reason (count 3 != 2). The `all("not executed")` half is intentionally relaxed for
  `ROUND_INFLIGHT (new) — the whole point is that the text no longer claims non-execution
  (Plan Goal).
- Red-first: the new companion tests fail pre-change (`KeyError`/wrong text), satisfying
  AC-005.

## Design decisions
- Outcome-unknown text (module-level, alongside `_STOP_TEXT`):
  `"Tool call was dispatched before the round stopped: outcome unknown, the call may have
  run on the server; verify before repeating."` — contains no tool name, arguments or
  output (REQ-004); deliberately distinct from `session_restore.py`'s
  `INTERRUPTED_TOOL_CALL_MARKER` ("[interrupted] tool call did not complete before session
  termination", verified 20261103) so the two synthesis paths never look alike.
- `pair_round_results` itself keeps its single-reason design (Plan Option A): the per-id
  partition happens in `complete_round` (seq 03), which calls this function once per
  partition with the matching reason. No new parameter here; `pair_round_results` only
  gains the `_STOP_TEXT` entry.
- Keep the "not executed" wording for `GUARD_STOP` and `ROUND_NOT_COMPLETED` byte-identical
  (REQ-003, AC-004; existing tests cite them).

## Alternatives considered
- A per-call text parameter on `pair_round_results` (Plan Option B): rejected with the
  same rationale as seq 01 — Option A keeps reasons self-describing and leaves this
  function's complexity (A(5)) untouched.

## Implementation
### Target file
`scripts/agent/tool_result_pairing.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail
   (missing `KeyError` on the new reason, missing text expectations).
2. Land this document together with
   `implementations/20261103-121149_01_scripts_agent_tool_enums.py.md` (the enum member is
   required for the mapping to import cleanly and for `TestStopReasonIsClosed` to see three
   members).
3. Add `ToolCallStopReason.ROUND_INFLIGHT: (<Design decisions text>)` to `_STOP_TEXT`
   (19-26). No other change to the function.

### Method
One dict entry; the function body and signature stay untouched.

### Details
- `_STOP_TEXT` is annotated `dict[ToolCallStopReason, str]`; adding the member makes it
  total again over the three-member enum — mypy does not enforce totality, but
  `pair_round_results`'s direct `_STOP_TEXT[stop_reason]` lookup (41) does at runtime, and
  the companion closure test enforces it statically.
- radon: unchanged (A(5)).

### Companion test files
- `tests/agent/test_tool_result_pairing.py` (companion of the
  `scripts/agent/tool_result_pairing.py` row; Plan `Implementation Target Files` seq 07
  covered here per the companion rule; the row's Requirement cites the guard-stop and
  exactly-once tests, which stay untouched)
  - Procedure:
    (i) Update `TestStopReasonIsClosed` (43-61) in place: drop the hard-coded `== 2`
    (keep `len(set(texts.values())) == len(ToolCallStopReason)` so the test stays closed
    against future members); assert `GUARD_STOP` and `ROUND_NOT_COMPLETED` texts contain
    "not executed" (byte-identical strings from today) and the `ROUND_INFLIGHT (new) text
    contains "outcome unknown" and "verify before repeating" and does NOT contain
    "not executed" (REQ-002, AC-001).
    (ii) Add `TestInFlightText` (new) to the module: `pair_round_results(["a"], set(),
    {}, ToolCallStopReason.ROUND_INFLIGHT)` yields exactly one row whose text is the
    outcome-unknown text and one history message with `tool_call_id == "a"`; assert the
    text contains none of the tool-name/argument placeholders used by the test fixtures
    (REQ-004: no args/output); assert the text differs from `build_denied_messages`
    denial text and from `session_restore.py`'s interrupted marker (import the marker
    constant and compare — Reference File read-only, import for assertion only).
    (iii) Regression: `TestPairingIsByDeclaredId`, `TestOrderIsDeclaredOrder`,
    `TestSynthesizedRowValidates`, `TestBuildDeniedMessages` stay byte-identical and green
    (REQ-003, AC-003, AC-004).
  - Validation: `uv run pytest tests/agent/test_tool_result_pairing.py -q` — red before
    Procedure 3 (and seq 01), green after.

## Compatibility considerations
- `pair_round_results` is called once today (`tool_round_completion.py:77-79`); seq 03 will
  call it up to twice per round with different reasons — no signature change here makes
  that call-compatible (AC-003 exactly-once is enforced by the partitions' disjointness in
  seq 03 plus the unchanged `seen` set).
- Existing callers/tests that pass `GUARD_STOP` or `ROUND_NOT_COMPLETED` see identical
  texts (unchanged dict entries).
- No `docs/` change here (seq 05 owns it). New symbols are private (a dict entry), so
  `tools/generate_reference_table.py --check` should report no drift.

## Security considerations
- The synthesized text carries no tool arguments, output, or user data (REQ-004); it adds
  no new masking obligation.

## Rollback considerations
- One dict entry plus the companion test edits; revert the commit (with seq 01) restores
  the two-member mapping.

## Validation plan
1. `uv run pytest tests/agent/test_tool_result_pairing.py -q` — red before Procedure 3,
   green after (Validation plan row 3 of the Plan).
2. Static: `uv run ruff check scripts/agent/tool_result_pairing.py
   tests/agent/test_tool_result_pairing.py`, `uv run ruff format --check` on both, `uv run
   mypy scripts/agent/tool_result_pairing.py`.
3. Gates: `uv run radon cc scripts/agent/tool_result_pairing.py -s` (unchanged ranks), `uv
   run python tools/check_module_size.py` (2503 B, ample), `uv run lint-imports`.
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   four code documents of this plan are executed.

## Completion criteria
- AC-003: one synthesized row per missing id under every reason (closure test green).
- AC-004: guard-stop and not-executed texts byte-identical; denial path unchanged.
- AC-005: the new/updated tests are red pre-change and green post-change.

## Out of Scope
- The enum member itself (seq 01), the partition and dispatch field (seq 03), the marking
  and cancellation test (seq 04), the docs paragraph (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, confirm they fail (Procedure 1; Companion test files) | Pending | — | — | Commit together with seq 01 |
| 2 | Add the `_STOP_TEXT` entry (Procedure 3) | Pending | — | — | |
| 3 | Run this document's checks (Validation plan 1-3) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (outcome-unknown text supplied via `_STOP_TEXT`), REQ-003
  (guard-stop text unchanged), REQ-004 (no args/output, exactly once)
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-121149
- **Related target files**: `scripts/agent/tool_result_pairing.py`, `tests/agent/test_tool_result_pairing.py`
