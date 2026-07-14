# Implementation: `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` — Remove `retry`-Stage and `exponential` Mentions

## Goal

Correct this doc's stage-list, retry-policy, and validation-rules sections to match confirmed runtime behavior: no `retry` stage exists, `plan` performs no LLM call, `execute` is where memory injection/mode classification/LLM/tool loop actually run, and `backoff` supports only `"fixed"`.

## Scope

**In scope:**
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`:
  - Lines ~58-62 (stage list): remove `retry` bullet; correct `plan` and `execute` bullets.
  - Lines ~77-80 (default retry policy) and ~117-120 (retry mechanism section): remove `"exponential"` mentions.
  - Lines ~128, 131 (loader validation rules list): update required-stages line and backoff validation rule.

**Out of scope:**
- Lines ~95, ~97 (`/approve [reason]`/`/reject [reason]` syntax) — already scoped into the sibling plan `plans/20260711-172158_plan.md` / its own implementation doc (`implementations/20260711-172657_docs_approve_reject_syntax_and_db_fallback_fix.md`); not duplicated here.
- Any other section of this doc unrelated to the stage list, retry policy, or loader validation rules.
- Other doc files referencing memory injection (confirmed accurate in the plan's Out-of-Scope list) — not touched.

## Assumptions

- Confirmed by direct read (per plan Assumption 3): the doc's stage-list section (line 59) currently states `` `plan` — LLMが初期計画を生成; 必須 â€”this is wrong; no LLM call happens in the plan stage at all.
- Confirmed by direct read (per plan Assumptions 1-2): `retry` is not a real engine-invoked stage, and `exponential` backoff is accepted by the loader but has zero runtime effect.
- The doc is otherwise assumed to follow the same stage-list / retry-policy / validation-rules structure implied by the plan's line-number references (~58-62, ~77-80, ~117-120, ~128/131); exact line numbers should be re-confirmed by direct read immediately before editing, since prior edits in this same session (e.g. the `/approve`/`/reject` fix) may have already shifted some line numbers.

## Implementation

### Target file

`docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

### Procedure

1. Re-read the file in full immediately before editing to re-confirm current line numbers (other implementation docs in this batch may touch nearby lines, e.g. the `/approve`/`/reject` syntax fix at lines ~95/97).
2. In the stage-list section (~58-62): delete the `retry` bullet entirely. Rewrite the `plan` bullet to state it is a bookkeeping/idempotency stage with no LLM call. Rewrite the `execute` bullet to state it performs memory injection, mode classification, the LLM call, and the tool execution loop.
3. In the default retry policy section (~77-80): remove any mention of `"exponential"` as an accepted/example `backoff` value; state `backoff` accepts `"fixed"` only.
4. In the retry mechanism section (~117-120): remove any remaining `exponential` mention; ensure prose describing the retry loop matches `_run_execute_with_retry()`'s actual fixed-delay behavior.
5. In the loader validation rules list (~128, 131): update the required-stages line to note `retry` is not a defined stage in `default.json` (already not required — just make this section consistent with the corrected stage-list section). Update the backoff validation rule to state `"fixed"` is the only accepted value.
6. After editing, grep the file for residual `exponential` or `retry`-as-stage wording to confirm nothing was missed.

### Method

Prose/bullet-list edits only — no code blocks, no restructuring of headings or table layout beyond the specific bullets/sentences named above.

### Details

- Match the file's existing language (English or Japanese, whichever is currently used in the surrounding prose) — do not introduce a language switch mid-document.
- Keep bullet/list formatting consistent with the rest of the stage-list section.
- Do not touch the `/approve`/`/reject` lines (~95, ~97) — reserved for the sibling implementation doc.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this doc:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep | `grep -n "exponential" docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` | No matches remain |
| Manual grep | `grep -n "retry" docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` | Only parenthetical/loop-mechanism mentions remain; no `retry`-as-stage bullet |
| Manual review | Diff review of stage-list section | `plan`/`execute` bullets match confirmed orchestrator.py behavior (plan Assumption 3) |
