## Goal

- Reduce duplication in `docs/01_overview-arch-02-pipelines.md` by summarizing the
  tool-loop-guard bullet (line ~48, under `#### クエリパイプラインの実装補足`) into a single
  sentence and linking to the detailed specification in
  `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`.

## Scope

- In scope: the tool-loop-guard bullet at `docs/01_overview-arch-02-pipelines.md:48`.
- Out of scope: `scripts/agent/tool_loop_guard.py` (source, actual path — see Assumptions),
  and any other bullet or file under `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`.

## Assumptions

- The source plan (`plans/20260803-183859_plan.md`) refers to the source file as
  `agent/tool_loop_guard.py`; actual path confirmed by `find` is
  `scripts/agent/tool_loop_guard.py` (repo layout puts implementation modules under
  `scripts/`). No behavior change is implied either way since this phase is docs-only.
- **Discrepancy found during investigation (flag, do not silently resolve):** the current
  content of `docs/01_overview-arch-02-pipelines.md:48` already reads as a one-sentence
  summary with a markdown link to
  `[`05_agent_03_02_turn-processing-flow-llm-tool-loop.md`](05_agent_03_02_turn-processing-flow-llm-tool-loop.md)`,
  matching the plan's target state. The plan's own Assumption 1 anticipated this
  ("Initial inspection suggests it may already be summarized"). Per
  `rules/coding.md` §"Current behavior" classification, this looks like the
  "Obsolete and removable" case (the plan's premise may no longer hold) — but confirming
  that requires re-reading the file's history/diff, which is outside a docs-only
  procedure-writing phase. The procedure below therefore starts with a verification
  step that makes this a no-op if the text already matches, rather than assuming
  further edits are required.
- Link target `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` exists and
  already contains a detailed `ToolLoopGuard` specification (confirmed: `check_all()`
  circular-detection → dedup → retry ordering, `GUARD_HINT` fallback message, etc.).

## Design decisions

- Treat this as a single-bullet text edit, not a restructuring of the doc section — keep
  the existing "実装補足" bullet-list format and heading placement.
- Prefer re-verifying current content before editing (idempotent procedure) over assuming
  the plan's premise is still accurate, per `skills/python-design/workflow.md` guidance to
  distinguish current/implemented state from proposed state and avoid presenting
  unverified assumptions as fact.

## Alternatives considered

- Move the detail out to the linked doc first and add the link — rejected: the detail
  already lives in `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`; only the
  summary sentence in the overview doc is in scope.
- Do nothing since content already appears summarized — rejected: verification must be an
  explicit, recorded step in the procedure rather than an implicit skip, so a future
  executor confirms rather than assumes.

## Implementation

### Target file

- `docs/01_overview-arch-02-pipelines.md` (line ~48, section `#### クエリパイプラインの実装補足`)

### Procedure

1. Verification: read the current bullet at `docs/01_overview-arch-02-pipelines.md:48` and
   compare against the target summary form (one sentence + link to
   `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`).
2. If the bullet is already in the target form: make no edit; record verification result
   only (this procedure's goal is already satisfied).
3. If the bullet still contains inlined implementation detail beyond a one-sentence
   summary: replace it with a single sentence describing the tool-loop-guard's purpose
   (detect abnormal repeated tool-call patterns within a turn and force termination via an
   LLM stop hint), followed by a markdown link to
   `[`05_agent_03_02_turn-processing-flow-llm-tool-loop.md`](05_agent_03_02_turn-processing-flow-llm-tool-loop.md)`.
4. Preserve the existing `(根拠: ...)` evidence-source annotation style used by sibling
   bullets in the same list.

### Method

- Manual/editor text replacement (single bullet line) — no script or codemod needed.
- Confirm via `grep -n "ツールループガード" docs/01_overview-arch-02-pipelines.md` before and
  after the edit to check line content, and
  `grep -n "05_agent_03_02_turn-processing-flow-llm-tool-loop" docs/01_overview-arch-02-pipelines.md`
  to confirm the link is present exactly once.

### Details

- Sibling bullets in the same list (MDQ/RAG classifier, workflow engine) follow the pattern
  `<one-line summary> (根拠: <source file>)`; the tool-loop-guard bullet should follow the
  same shape but add a markdown link to the detail doc since the plan calls for one
  ("summarize ... and link to the detailed specification").
- Source module for the `(根拠: ...)` reference: `scripts/agent/tool_loop_guard.py`
  (class `ToolLoopGuard`, dataclass `TurnLoopState`) — confirmed present via `grep -n
  "^class "`.

## Compatibility considerations

- N/A — documentation-only text change; no code, schema, or API surface affected.

## Security considerations

- N/A — no secrets, credentials, or executable content involved.

## Rollback considerations

- Single-line/bullet edit in a Markdown file tracked by git; revert via
  `git checkout -- docs/01_overview-arch-02-pipelines.md` or a follow-up commit restoring
  the prior bullet text if the summary loses needed context.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Bullet content | `grep -n "ツールループガード" docs/01_overview-arch-02-pipelines.md` | One line, single-sentence summary |
| Link present | `grep -n "05_agent_03_02_turn-processing-flow-llm-tool-loop" docs/01_overview-arch-02-pipelines.md` | Exactly one match, valid relative link |
| Link target exists | `test -f docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` | File exists |
| Manual render check | Open both docs in a Markdown viewer | Link resolves; summary reads coherently in context |

## Out of scope

- Any change to `scripts/agent/tool_loop_guard.py`.
- Any change to `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`.
- Broader reformatting of `docs/01_overview-arch-02-pipelines.md` beyond the one bullet.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-183859_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-112239
- Related target files: 01_overview-arch-02-pipelines.md
