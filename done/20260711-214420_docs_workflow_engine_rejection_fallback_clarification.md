# Implementation Procedure: docs — clarify rejection-halt fallback in workflow-engine doc

Source plan: `plans/20260711-173259_plan.md` — Design §2 / Implementation step 5

## Goal

Add one clarifying sentence to the "承認ゲート" (approval gate) section of `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`, explaining that `/reject` performs the halt immediately and the engine's own rejected-status check is a defensive fallback, not the primary path.

## Scope

**In:**
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`: one sentence added to the existing "承認ゲート" section (around line 101, after the existing rejected-branch bullet).

**Out:**
- No other section of this doc is touched by this item — a sibling, already-processed plan separately fixes this same doc's stage-list/retry-policy/backoff sections (`implementations/20260711-173209_docs_workflow_engine_stage_list_retry_exponential_fix.md`) and another sibling fixes the `/approve`/`/reject` syntax mentions (`implementations/20260711-172657_docs_approve_reject_syntax_and_db_fallback_fix.md`) — do not duplicate or re-touch those sections here.

## Assumptions

1. Confirmed by the plan's Design §2: the doc's existing "### 承認ゲート" section (lines 88-104) already describes the rejected-branch behavior but does not mention that `/reject` independently performs the same halt immediately, nor that the engine's own check is a fallback.
2. This item depends conceptually on the code-level clarifications in the companion docs (`workflow_engine.py` comment, `cmd_workflow.py` docstring) — the doc sentence should describe the same relationship in operator-facing prose, consistent wording, not introduce a third, divergent explanation.
3. Two sibling plans already touch other sections of this exact same doc file (stage-list/retry-policy fixes; `/approve`/`/reject` syntax fixes) — confirm at implementation time that line numbers around ~101 have not shifted due to those edits before inserting this sentence.

## Implementation

### Target file

`docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

### Procedure

1. Locate the "### 承認ゲート" section (originally lines 88-104) and find the existing bullet describing the rejected-status branch (originally around line 101).
2. Immediately after that bullet, add one sentence (in Japanese, matching the surrounding doc's language) stating: `/reject` コマンドは拒否操作の直後にタスクを即座に halted 状態にする。`WorkflowEngine._gate_approval()` 側の rejected 状態チェックは、その halt が別経路で適用される前にエンジンが再評価した場合に備えた防御的フォールバックであり、主経路ではない。
3. Do not restructure the surrounding bullets or renumber any list — only insert the one clarifying sentence in the appropriate place.

### Method

Single-sentence documentation insertion into an existing Markdown section. No structural changes to the rest of the document.

### Details

- Re-read the current state of this section immediately before editing, since two sibling plans independently modify other parts of the same file — confirm the "承認ゲート" section's exact current line numbers and wording have not been affected by those edits.
- Keep terminology consistent with the companion code-comment/docstring wording ("defensive fallback") translated naturally into the surrounding Japanese prose style already used in this doc.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual review | Read the full "承認ゲート" section after edit | New sentence reads naturally, does not contradict or duplicate existing bullets, and does not conflict with sibling plans' edits to other sections of the same file |
