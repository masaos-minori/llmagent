## Goal

Partition the unanswered declared ids of a `ROUND_NOT_COMPLETED` round into in-flight
(present in `RoundState.dispatched_ids`) and never-dispatched, answer each partition with
its own reason (`ROUND_INFLIGHT` (new) vs `ROUND_NOT_COMPLETED`), and keep one synthesized row
per declared id in declared order (REQ-002, REQ-004; AC-001, AC-002, AC-003).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_round_completion.py` row (seq 03) and its companion test row
`tests/agent/test_tool_round_completion.py` (seq 06 of the plan table, companion-eligible,
no document of its own) of
`plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`. Runs after
`implementations/20261103-121149_01_scripts_agent_tool_enums.py.md` (consumes
`ROUND_INFLIGHT` (new)) and `implementations/20261103-121149_02_scripts_agent_tool_result_pairing.py.md`
(consumes the `_STOP_TEXT` mapping). Declares `dispatched_ids` (new) on `RoundState` for
the seq 04 tool_runner document to consume. Intra-plan execution order: 01 → 02 → 03 → 04,
then the plan-wide validation.

## Assumptions
- Verified against current source (20261103): `RoundState` (tool_round_completion.py:21-28)
  is a `@dataclass` with `declared_ids: list[str]`, `collected: dict[str, tuple]`,
  `prep_failures: list[Any]`, `denied_ids: list[str]` and no dispatch field.
  `complete_round` (55-95) computes `answered = {*(r[0] for r in state.prep_failures),
  *state.denied_ids}` at 76 and calls `pair_round_results(state.declared_ids, answered,
  state.collected, reason)` once at 77-79; `pair_history`/`pair_msgs` feed
  `ctx.conv.extend_messages` (80) and `tool_msgs.extend` (81). radon: `complete_round`
  A(3). Module is 3527 B (gate 20480 B) — ample.
- `ROUND_INFLIGHT` (new) is declared by the seq 01 sibling and mapped in `_STOP_TEXT` by
  the seq 02 sibling; this document adds `dispatched_ids` (new).
- `tool_runner.py:495` constructs `RoundState([...])` positionally; a defaulted field keeps
  that call unchanged (seq 04 only reads `state.dispatched_ids`).
- `TestCompleteRoundPersistence` (companion file, 83-160) is the fixture pattern to mirror:
  a MagicMock `ctx`, real `RoundState`, a stub `collect` coroutine, assertions on
  `ctx.conv.extend_messages` calls. `TestCompleteRoundRoundAtomicity` (207+) covers the
  persistence-boundary path and must stay green.
- Red-first: the new partition tests fail pre-change (every unanswered id gets the
  not-executed text today), satisfying AC-005.

## Design decisions
- Field: `dispatched_ids: set[str] = field(default_factory=set)` on `RoundState` — the
  plan's per-round tracking location (D1); written by `_recorded_call` via the seq 04
  threading, read here. Default-empty keeps every existing construction site working.
- Partition (D3, Option A): only for `reason == ToolCallStopReason.ROUND_NOT_COMPLETED`,
  compute `unanswered` (declared order, deduplicated, minus `answered`, minus
  `collected`), split it by membership in `state.dispatched_ids`, call
  `pair_round_results` once per partition with its reason, then re-merge the two outputs
  into `unanswered` order so the module's documented "Rows keep the original batch order"
  behavior survives the split (a plain concatenation would block-group the partitions).
  The two partitions are disjoint and the unchanged `seen` set plus the dedup keep the
  exactly-once guarantee (REQ-004).
- `GUARD_STOP` (and any future reason) keeps the single `pair_round_results` call —
  guard-skipped calls are never dispatched, so their text must not change (REQ-003,
  AC-004). A dispatched id under `GUARD_STOP` (reachable only if a future flow dispatches
  and then guard-stops) still gets the guard-stop text: this Plan changes only the
  `ROUND_NOT_COMPLETED` path.

## Alternatives considered
- Two raw `pair_round_results` calls concatenated in inflight-then-never order: rejected —
  breaks declared order, which `complete_round`'s docstring and the existing merge design
  commit to.
- Per-id text selection inside `pair_round_results` (Plan Option B): rejected with the same
  rationale as seq 01/02.

## Implementation
### Target file
`scripts/agent/tool_round_completion.py`

### Procedure
1. Confirm the red companion tests (see Companion test files) exist and fail against the
   current `complete_round`.
2. Add `dispatched_ids: set[str] = field(default_factory=set)` (new) to `RoundState` after
   `denied_ids`, with a one-line docstring comment naming its writer (`_recorded_call`,
   tool_runner) and reader (this module's partition).
3. In `complete_round`, replace the single `pair_round_results` call (77-79) with the
   partition described in Design decisions: if the reason is `ROUND_NOT_COMPLETED`,
   compute `unanswered` (dedup via `dict.fromkeys`, declared order), split by
   `state.dispatched_ids`, call `pair_round_results` twice (inflight ids with
   `ToolCallStopReason.ROUND_INFLIGHT`, never-dispatched ids with `reason`, both with empty
   `answered`/`collected` since filtering already happened), then rebuild
   `pair_history`/`pair_msgs` in `unanswered` order from the returned rows' id (row index
   3); otherwise keep today's single call.
4. Keep every other statement of `complete_round` (merge, collect, denied, extend, atomic
   persistence block) untouched.

### Method
One defaulted dataclass field plus a guarded branch in `complete_round`; the persistence
and stats behavior is unchanged.

### Details
- radon: `complete_round` A(3) → estimated A(6) (one `if`, two comprehensions, one merge
  comprehension); rank A ceiling is 10 — recheck `uv run radon cc
  scripts/agent/tool_round_completion.py -s` after the edit.
- `unanswered` dedup: `list(dict.fromkeys(...))` preserves today's `seen`-set behavior for
  duplicate declared ids (characterization test (iv) below pins it).
- The partition runs after `answered` is computed (line 76) and must reuse it verbatim —
  preparation-failure and denied ids stay excluded from synthesis (existing contract).
- `ToolCallStopReason` is already imported in this module (used in the signature at 61).

### Companion test files
- `tests/agent/test_tool_round_completion.py` (companion of the
  `scripts/agent/tool_round_completion.py` row; Plan `Implementation Target Files` seq 06
  covered here per the companion rule)
  - Procedure: add to the module, mirroring the `TestCompleteRoundPersistence` fixture
    style (MagicMock ctx, real `RoundState`, stub `collect`):
    (i) `TestCompleteRoundDispatchPartition` (new) `test_inflight_and_never_dispatched_get_their_own_texts` (new):
    declared ids `["a", "b", "c"]`, `collected` holds a real result row for `a`,
    `dispatched_ids` (new) == {"b"}; run `complete_round` with `ROUND_NOT_COMPLETED`; assert
    exactly one tool row per declared id, `b`'s row text contains "outcome unknown" and
    "verify before repeating", `c`'s row text is the not-executed round text, `a` keeps its
    real result row, and the synthesized rows appear in declared order (REQ-002; AC-001,
    AC-002, AC-003).
    (ii) `test_guard_stop_path_unchanged` (new): same state with `GUARD_STOP` reason → every
    unanswered id gets the guard-stop text even when present in `dispatched_ids` (new) (REQ-003;
    AC-004).
    (iii) `test_prep_failure_and_denied_ids_are_not_resynthesized` (new): `b` in
    `prep_failures` and `c` in `denied_ids`, both also in `dispatched_ids` (new) → no extra
    synthesized rows, each id answered once (REQ-004).
    (iv) characterization `test_duplicate_declared_id_synthesizes_one_row` (new): declared
    `["x", "x"]`, nothing collected → exactly one synthesized row (today's `seen`-set
    behavior preserved).
    (v) Regression: `TestMergeInDeclaredOrder`, `TestCompleteRoundPersistence`,
    `TestCompleteRoundRoundAtomicity` stay byte-identical and green.
  - Validation: `uv run pytest tests/agent/test_tool_round_completion.py -q` — red before
    Procedure 2-3, green after.

## Compatibility considerations
- `complete_round` has a single caller (the `finish` closure in
  `scripts/agent/tool_runner.py:498-505`, verified 20261103); its signature is unchanged,
  so seq 04's threading lands independently of this module.
- Row/history shapes (`LLMMessage` tool entries, `("tool", text, None, call_id)` rows)
  unchanged — no persistence or schema impact (REQ-004).
- blockio001's Pending procedures do not touch this module (cross-plan overlap is
  tool_runner/test_tool_runner only; Plan Assumptions 20261103 note).
- No `docs/` change here (seq 05 owns it). `dispatched_ids` (new) is a dataclass field — not a
  reference-table symbol; `tools/generate_reference_table.py --check` at plan validation.

## Security considerations
N/A: the partition reads internal ids only; the emitted texts come from the seq 02 dict
(no user data).

## Rollback considerations
- One field plus one guarded branch plus the new companion class; revert the commit
  restores today's single-call pairing.

## Validation plan
1. `uv run pytest tests/agent/test_tool_round_completion.py -q` — red before Procedure 2-3,
   green after (Plan Validation plan row 2).
2. Static: `uv run ruff check scripts/agent/tool_round_completion.py
   tests/agent/test_tool_round_completion.py`, `uv run ruff format --check` on both, `uv
   run mypy scripts/agent/tool_round_completion.py`.
3. Gates: `uv run radon cc scripts/agent/tool_round_completion.py -s` (`complete_round`
   stays rank A), `uv run python tools/check_module_size.py` (3527 B, ample), `uv run
   lint-imports`.
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   four code documents of this plan are executed.

## Completion criteria
- AC-001/AC-002: the two texts are selected per id as specified; AC-003: exactly one row
  per declared id; AC-004: guard-stop and completed paths unchanged.
- AC-005: new tests red pre-change, green post-change.

## Out of Scope
- Writing/clearing `dispatched_ids` (new) (seq 04), the enum member (seq 01), the text dict
  entry (seq 02), the cancellation test (seq 04's companion), the docs paragraph (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm red companion partition tests fail (Procedure 1; Companion test files) | Pending | — | — | Commit with seq 01+02 (the mapping and member are required) |
| 2 | Add the field and the partition branch (Procedure 2-3) | Pending | — | — | |
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
- **Requirement ID**: REQ-002 (per-id partition and texts), REQ-004 (one row per declared
  id, declared order preserved)
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-121149
- **Related target files**: `scripts/agent/tool_round_completion.py`, `tests/agent/test_tool_round_completion.py`
