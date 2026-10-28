# Plan: Apply fallback truncation on token-only compression overflow failure

## Goal
- When history compression is triggered by a token-only overflow and the summarizer
  returns `None`, the unit-drop fallback (`_fallback_truncate`) is applied with a
  token-aware drop condition, so the oversized history converges instead of being
  resent to the backend every turn.

## Priority
Medium — the char-limit path already has the fallback; the token-path gap turns a
one-off summarizer failure into a persistent session-level failure. Path A task
(1 production file + 1 test file + 1 doc).

## Scope
- **In-Scope**:
  - Fallback gating in `compress()` extended to the token-only overflow case
    (`scripts/agent/history.py`).
  - Token-aware drop condition in the `_fallback_truncate` / `_apply_unit_drops` path
    (`scripts/agent/history.py`).
  - Regression tests for the token-only + summarizer-failure state
    (`tests/agent/test_history_manager.py`).
  - Docs: describe both overflow triggers and fallback-on-failure behavior
    (`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`).
- **Out-of-Scope**:
  - Improving token estimation accuracy.
  - Changing summarizer retry/timeout policy.
  - Selection policy, protected-turn handling, summarizer call semantics (issue AI
    instruction).
- **Dependencies**: N/A: none

## Background
From the python-code-review pass over the REPL turn path (finding F-006). Verified
against current code:
- `scripts/agent/history.py` `compress()` L264-295: triggers on `over_char` or
  `over_token` (L276-279); when `_get_summary_text` returns `None`, fallback runs only
  if `self._is_over_char_limit(history)` (L287); token-only overflow returns the
  unchanged history with `error="compression returned None"` (L289-294). Issue claim
  confirmed.
- `_fallback_truncate` (L301-327) and `_apply_unit_drops` (L343-359) currently drop
  units only `while self._is_over_char_limit(new_history)` (L351-352): calling the
  fallback unchanged in the token-only case would be a silent no-op — the gating fix
  alone is insufficient, the drop condition must be token-aware. This resolves the
  issue's Unresolved Question: **reuse the existing unit-drop fallback with a
  token-aware limit check**, not a separate token-budgeted variant.
- Trigger-side token source: `_check_limits` (L383-390) uses `count_tokens_async`; with
  `tokenize_url = ""` (docs agent_04_02 L118-123) this is the same category-aware
  `estimate_tokens` that `count_tokens()` (L161-183) computes synchronously — so the
  fallback drop loop can use the identical estimator it was triggered with.

## Problem
Token limit exceeded + summarizer failure → history unchanged, backend context-length
error on every subsequent turn, no recovery short of `/clear`.

## Reason for Change
Issue target-file claim corrected against current code: `scripts/agent/orchestrator.py`
needs no change — it never inspects `CompressResult.error` for this case; the oversized
history simply flows on because `compress()` returned it unchanged. The fix is confined
to `scripts/agent/history.py`. Persistence is also already compatible:
`conversation_state_manager.handle_history_compression` (L155-169) persists via
`replace_messages` whenever `compressed_count > 0`, so a fallback-produced history is
persisted with no change there.

## Implementation Intent
Make the fallback decision depend on "history is over a hard limit", not on which
limit: when summarization is unavailable and `over_char or over_token`, call
`_fallback_truncate`; make its drop/stop condition
`over_char or (token_limit > 0 and count_tokens(h) > token_limit)`; keep whole-unit
drops, protected-unit integrity, and never-empty guarantees untouched.

## Requirements
- `REQ-001`: `compress()` applies the fallback when the summarizer is unavailable and
  any hard limit (`over_char` or `over_token`, using the already-computed flags) is
  exceeded; the token-only case no longer returns the unchanged history with
  `error="compression returned None"`.
- `REQ-002`: The fallback drop loop and post-drop warning use a token-aware limit
  check: drop whole units while `over_char` or (`_token_limit > 0` and
  `count_tokens(new_history) > _token_limit`). Estimator: the synchronous category-aware
  `count_tokens()` estimate — identical to the trigger estimator under default config
  (`tokenize_url = ""`), so trigger and fallback agree on the measurement.
- `REQ-003`: Invariants preserved: only whole turn units drop, units containing
  protected messages never split (no orphaned tool row), history never emptied,
  system messages and `protect_turns` tail preserved.
- `REQ-004`: Reporting parity: token-path fallback reports `CompressResult.is_fallback=True`,
  `compressed_count` = dropped messages, and increments `stat_fallback_truncate_count`,
  exactly as the char path does today.
- `REQ-005`: Convergence: repeated turns in the token-overflow + summarizer-failure
  state keep shortening the history toward the limit (approximation tolerance same as
  the char path; sub-limit size not guaranteed).
- `REQ-006`: Char-path behavior and all existing compression/fallback tests pass
  unchanged; selection policy, protected-turn handling, and summarizer call are not
  touched.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/history.py | Extend `compress()` fallback gating to `over_char or over_token`; make `_fallback_truncate`/`_apply_unit_drops` limit check token-aware (`count_tokens() > _token_limit` alongside char check) | Token-only overflow + summary `None` returns unchanged history (L287-294); drop loop stops only on char limit (L351-352) | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 | Read: `compress` L264-295, `_fallback_truncate` L301-327, `_apply_unit_drops` L343-359, `_check_limits` L383-390 | tests/agent/test_history_manager.py | Verified |
| tests/agent/test_history_manager.py | Add token-only fallback regression cases: overflow+`None` → shortened + `is_fallback=True`; tool-row integrity; repeated compress keeps history bounded; error-path cases under no overflow unchanged | Existing fallback tests cover the char path only (`..._over_limit`, `..._under_limit` cases around L921-1019) | REQ-001, REQ-003, REQ-004, REQ-005, REQ-006 | Read: 40 fallback references; token-limit cases already present in this file | — | Verified |
| docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | Update fallback section: both triggers (char, token) now fall back on summarizer failure; token-aware drop condition and reporting | Current docs state fallback only on "character limit is still exceeded" (L79) — becomes stale | REQ-001, REQ-002, REQ-004 | `docs/00_index.md` L155 maps `HistoryManager` compression to agent_04_02; file exists | N/A: documentation only | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/orchestrator.py | Confirm the post-compression turn path needs no change (issue lists it as a target; verification says no) | REQ-001 |
| scripts/agent/conversation_state_manager.py | `handle_history_compression` persists whenever `compressed_count > 0` (L155-169) — fallback-produced history is persisted without change | REQ-004 |
| scripts/shared/token_estimation.py | Category-aware estimator used by `count_tokens()`; must stay the same estimator the trigger uses | REQ-002 |
| scripts/agent/history_selection_policy.py | Unit grouping / protected-tail / importance used by the drop loop — invariants must remain untouched | REQ-003 |
| tests/agent/test_history_compression_consistency.py | Existing char-path fallback + persistence-consistency regression gate | REQ-006 |

## Acceptance Criteria
- `AC-001` (REQ-001, REQ-004): token-only overflow + summarizer `None` → history
  shortened via fallback, `CompressResult.is_fallback=True`, `compressed_count` =
  dropped messages, `stat_fallback_truncate_count` incremented.
- `AC-002` (REQ-005): repeated compress() calls in that state strictly shorten history
  until no droppable unit remains (bounded, no permanent oversized resend).
- `AC-003` (REQ-003): after token-path fallback, no tool message is separated from its
  assistant `tool_calls` row and history is non-empty.
- `AC-004` (REQ-006): all existing compression/fallback tests pass unchanged
  (`test_history_manager.py`, `test_history_compression_consistency.py`,
  `test_regression_history_compress_reload.py`).

## Tests
- `T-001` (REQ-001, REQ-004): char under limit, tokens over limit (mock `count_tokens`
  input via long messages with `token_limit` set), summarizer mocked to return `None` →
  history shortened, `is_fallback=True`, no `error="compression returned None"`.
- `T-002` (REQ-003): history containing a tool round (assistant `tool_calls` + tool
  rows) in a droppable unit → after fallback, whole units only; protected tail intact.
- `T-003` (REQ-005): two consecutive compress() calls in failure state → second call
  still progresses or history is at minimal (protected-only) size with the
  could-not-bring-under-limit warning (no silent unchanged success).
- `T-004` (REQ-006): run the three existing history test modules unchanged.

## Documentation Impact
Docs update required, driven by REQ-001/REQ-002/REQ-004: the history-compression doc
(mapped via `docs/00_index.md` L155 → `agent_04_02_state-and-persistence-history-
compression.md`) must describe both overflow triggers and the token-aware fallback
behavior when summarization is unavailable.

## Assumptions
- Overlap check (Step 8b, run at freeze): this Plan targets no file shared with the
  other Frozen Plans (turn001/turn002/memory001); `agent_04_01` overlaps belong to those
  Plans only. Re-verified at freeze via `check_plan_target_overlaps.py`.
- Trigger and fallback use the same estimator under default config (`tokenize_url = ""`),
  so a drop loop measured by `count_tokens()` cannot disagree with the `over_token`
  trigger measurement except through estimator drift within one call — acceptable per
  the issue's tolerance constraint.
- `count_tokens(history)` (sync estimate) is cheap enough per dropped unit for
  interactive use (estimate is a single pass over messages).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact config values where token limit can be exceeded while char limit is not (realistic test geometry) | `config/agent.toml` `context_token_limit` / `context_char_limit` current values not re-read this cycle | Tests construct limits explicitly on the HistoryManager constructor (`token_limit` kwarg, L74) rather than production config | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/history.py | Fallback gating + token-aware drop condition | All compression callers: `conversation_state_manager.handle_history_compression`, `cmd_rag_export.force_compress` (force path always sets over_char, so unchanged) | 1 | 1 | None (no schema/deploy change) |
| tests/agent/test_history_manager.py | New regression cases | test suite | — | — | None |
| docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | Fallback semantics section | docs | — | — | None |

## Design
- `compress()` failure branch becomes:
  `if summary_text is None: if over_char or over_token: return self._fallback_truncate(history)`
  — the already-computed `over_char`/`over_token` flags (L276-277) replace the second
  `_is_over_char_limit` call, removing a duplicated char scan.
- `_apply_unit_drops` drop condition becomes `_is_over_any_limit(new_history)`:
  `self._is_over_char_limit(h) or (self._token_limit > 0 and self.count_tokens(h) > self._token_limit)`.
  One new private helper on HistoryManager; `_fallback_truncate`'s post-drop warning
  (L315-320) checks the same helper and logs chars and tokens.
- Char-path behavior is a strict subset of the new condition (char-only overflow
  behaves exactly as today), satisfying REQ-006 without mode flags.
- `force_compress()` (L130-147) forces `char_limit=1` → `over_char=True` path unchanged.
- No changes to `CompressResult` schema, selection policy, protection logic, or
  `_get_summary_text`.

## Implementation steps
1. **Phase 1: Core logic in `scripts/agent/history.py`**
   - [ ] Add `_is_over_any_limit` helper (char or token check) and use it in
     `_apply_unit_drops` and the `_fallback_truncate` post-drop warning (REQ-002,
     REQ-003; scripts/agent/history.py)
   - [ ] Change the `compress()` summary-`None` branch to fall back on
     `over_char or over_token` (REQ-001, REQ-004; scripts/agent/history.py)
2. **Phase 2: Regression tests and docs**
   - [ ] Add T-001..T-003 to `tests/agent/test_history_manager.py` (REQ-001, REQ-003,
     REQ-004, REQ-005; tests/agent/test_history_manager.py)
   - [ ] Update the fallback/trigger section of the history-compression doc
     (docs/23_agent/agent_04_02_state-and-persistence-history-compression.md)
     (REQ-001, REQ-002, REQ-004)
   - [ ] Run the full validation plan below; `deploy.sh` impact: none (no schema or
     deployment file touched)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/history.py | Unit: T-001..T-003 | `uv run pytest tests/agent/test_history_manager.py` | Token-only fallback cases pass |
| char-path regression | Regression gate | `uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_compression_consistency.py tests/agent/test_regression_history_compress_reload.py` | Existing cases pass unchanged (AC-004) |
| consumers | Regression gate | `uv run pytest tests/agent/ -q -k "history or compress or rag_export"` | No regressions in compress callers |
| lint/type | Static checks | `uv run ruff check . && uv run mypy scripts/agent/history.py` | Clean (issue Testing Expectations) |

## Risks
- **Risk**: token-only fallback could drop down to protected-only history and still be
  over the token limit (single huge protected unit) → **Mitigation**: existing
  never-empty invariant plus post-drop warning naming chars/tokens/limits (T-003);
  behavior equals today's char-path no-progress edge, but now visible.
- **Risk**: per-unit `count_tokens()` re-estimation cost on very large histories →
  **Mitigation**: estimate is O(total chars) single pass and only runs in the failure
  fallback path; acceptable per constraint "reload/interactive fast enough" analog.
- **Risk**: existing tests that assert `error="compression returned None"` for a case
  that is actually token-overflow (not under-limit) would flip behavior → **Mitigation**:
  grep shows those cases are "under_limit" named cases (L939, L964); AC-004 gate
  catches any surprise.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: core logic in scripts/agent/history.py | Completed | 20261028-082312 | 20261028-082312 |  |
| 2 | Phase 2: regression tests and docs | Completed | 20261028-082312 | 20261028-082312 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-211550_01_scripts_agent_history.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261027-211550_02_tests_agent_test_history_manager.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-211550_03_docs_23_agent_agent_04_02_state-and-persistence-history-compression.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-224931_history001_token-overflow-compression-fallback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-10-27 07:42:12
- **Related target files**: `scripts/agent/history.py`,
  `tests/agent/test_history_manager.py`,
  `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Section | Source Content | Target File | Implementation Phase | Acceptance Criteria | Test Case | Basis |
|---|---|---|---|---|---|---|---|
| REQ-001 | Summary; Required Changes 1 | Token-only overflow must fall back | scripts/agent/history.py | Phase 1 | AC-001 | T-001 | Confirmed by repository evidence (L287-294) |
| REQ-002 | Implementation Intent; Unresolved Question | Unit-drop fallback extended token-aware | scripts/agent/history.py | Phase 1 | AC-001 | T-001 | Confirmed (L351-352 char-only stop condition) |
| REQ-003 | Constraints 1 | Whole units, no orphaned tool row | scripts/agent/history.py | Phase 1 | AC-003 | T-002 | Confirmed (L301-327 invariants) |
| REQ-004 | Required Changes 2 | CompressResult reporting parity | scripts/agent/history.py | Phase 1 | AC-001 | T-001 | Confirmed (L322-327) |
| REQ-005 | Acceptance Criteria 2 | Repeated turns keep history bounded | scripts/agent/history.py | Phase 1 | AC-002 | T-003 | Derived from confirmed evidence |
| REQ-006 | Acceptance Criteria 3; AI Instruction | Existing tests/behavior unchanged | tests/agent/test_history_manager.py | Phase 2 | AC-004 | T-004 | Confirmed (existing fallback case inventory) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-211550 -->