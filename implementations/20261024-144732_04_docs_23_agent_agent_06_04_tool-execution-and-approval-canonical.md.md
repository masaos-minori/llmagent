## Goal

Make `### Persistence of Partial Completion` in the tool-execution canonical chapter agree with the
`tasks.status` state machine: state which outcomes are recorded and by whom, that a cancelled turn is
recorded `halted`, and name `agent_03_03` as the canonical source of the state machine instead of
implying that `failed` and `halted` are the complete record (`REQ-010`; `AC-9`).

## Scope

- `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`, one passage only:
  `### Persistence of Partial Completion` (heading `:44`, body `:46-51`, blank `:52`).
- The two existing bullets at `:48-49` and the `**Design judgment**` paragraph at `:51` are reworded
  in place; no new heading is added.
- Front matter (`:1-15`), `## Purpose`, `## Design Intent`, `#### Terminology`, `#### Behavior`,
  `## Responsibility Boundary` (`:53-55`), `## Key Constraints` (`:57-62`), `## Known Limitations`
  (`:64-67`) and `## Keywords` (`:69-73`) are untouched.
- No other chapter is edited; the state machine itself is documented by
  `implementations/20261024-144732_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`.

## Assumptions

- `agent_03_03` is the canonical home for this state machine: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md:31`
  points at it for "the formal partial completion model", and it is the only other chapter in the corpus
  that documents task status at all (`grep -rln "update_task_status|tasks table|workflow task" docs/`
  returns only `agent_03_03` and this chapter). This chapter therefore points at it rather than restating
  it.
- The existing claim that the engine "records the final task status" is not wrong, only incomplete: once
  the adapter stops writing `completed` and starts recording cancellation, the two-bullet list becomes a
  misleading enumeration of possible outcomes.
- The chapter's approval content is unaffected: nothing in the tool-level approval passages depends on
  which component wrote a status.
- `halted` keeps its existing meaning here (`:61`, `:67`: partial completion is not automatically
  resumed), so extending the outcome list to cancellation does not require touching those passages.

### Procedure-local findings

- Frozen row status: **Not implemented**. No file-level overlap with active sibling procedures:
  `check_plan_target_overlaps.py` reports no active plan naming this file, and no active procedure edits it
  (`grep -rln "agent_06_04" implementations/` excluding `implementations/done/` matches only this procedure,
  plus out-of-scope mentions in `144732_01` and `144732_03`). This file is therefore safe
  to edit independently of the turn002/turn004 sequencing that gates `_01`-`_03`.
- Anchor correction: the Plan cites `:46-52`; the subsection heading is at `:44` and the body is
  `:46-51` with a blank line at `:52`. `## Responsibility Boundary` follows at `:53`.
- The Plan's own row wording ("It already documents `update_task_status()` writing `failed` and `halted`")
  matches `:46-49` exactly today.
- `## Responsibility Boundary`'s only entry is `**Canonical Source**: agent/tool_approval.py (tool-level
  approval)` (`:55`). Adding a second canonical-source line there would broaden the frozen row's scope;
  the canonical-source statement for the state machine goes in the Persistence passage body instead, and
  the untouched `Responsibility Boundary` entry is recorded as a follow-up candidate.
- Size and cleanliness baselines re-measured 2026-10-24 at HEAD `1471a75e8`: 73 lines / 3171 B against the
  24576 B docs gate; `check_docs_structure.py "docs/23_agent/agent_06_04*.md"` — "All checks passed";
  `check_docs_quality.py` and `check_docs_content_policy.py` — no finding naming this file;
  `check_docs_consistency.py --domain agent` — "No issues found."; `check_docs_japanese.py` — clean.
- Inbound links re-measured at HEAD `1471a75e8`: `agent_06_04` is named by `agent_06_01:11`, `agent_06_02:10`
  and `agent_06_03:13` front matter, by `agent_06_02:27` body text, by `agent_03_03:46` body text (the latter
  added by the upstream docs-dedup commits), and by `docs/01_overview/overview_01_02-arch-pipelines.md:82`
  body text. No link is added to or removed from either direction by this row, and no front matter change is
  made (`GV-016`).
- Plan-evidence correction (re-measured 2026-10-24 at HEAD `1471a75e8`): the Plan's `Documentation Impact`
  rationale states that `docs/23_agent/agent_04_01_state-and-persistence-state-model.md:44` "defers this
  topic to `agent_03_03`". At procedure-generation time `agent_04_01:44` was `### DiagnosticStore Separation
  Design` body text about `session_diagnostics` with no deferral sentence. The upstream docs-dedup commits
  (`0d193fd60`, `92caeb0b4`) then added one: `agent_04_01:44` now ends with a pointer to
  [agent_03 Partial-Completion Model](agent_03_03_turn-processing-flow-workflow-engine.md), under the
  `### DiagnosticStore Separation Design` heading (`:42`), plus the front-matter `related` entry at `:17`.
  The Plan's claim is now true against the current tree; the canonicality decision is retained and the
  evidence is restated in `Assumptions`. `agent_04_01` is not edited by this row.

## Design decisions

- Prose and bullets, no table: the state machine table lives in `agent_03_03`. Restating it here would
  create a second canonical statement and risks `check_docs_quality.py`'s cross-file
  `check_content_similarity` warning, which is not exempt for a `### Persistence of Partial Completion`
  vs `### Task Status Transitions` pair.
- Keep the section name and its position: other documents already reference this chapter as the partial
  completion owner, and the frozen row scopes the edit to this subsection.
- Name the writer for each outcome (workflow engine / turn adapter) rather than the module: the chapter
  already names components (`StateStore.update_task_status()`, `agent/tool_approval.py`) and component
  ownership is retain-category content, while an "implemented in `<file>.py`" sentence is the
  remove-category mapping pattern `check_docs_content_policy.py` flags.
- Cancellation is described by its effect on the durable record and by the pointer to `agent_03_03`, not
  by the mechanism in the adapter, so this chapter does not need to be re-edited when the adapter row's
  internal shape changes.

## Alternatives considered

- Add a `### Task Status Transitions` subsection here as well: rejected — the Plan scopes this row to
  `### Persistence of Partial Completion` only, and duplicating the state machine splits canonicality.
- Delete the two `failed` / `halted` bullets and replace them with a link only: rejected — the chapter is
  the entry point for partial-completion questions, and a reader must see the outcome list without
  jumping chapters.
- Also amend `## Key Constraints` and `## Known Limitations` so their "not automatically resumed" bullets
  name the resume guard: outside the frozen row's single-section scope; recorded as a follow-up
  candidate.
- Amend `## Responsibility Boundary` to list a canonical source for the state machine: outside the
  frozen row's scope; the pointer is placed in the Persistence passage instead.

## Implementation
### Target file

`docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`

- 73 lines / 3171 B at HEAD `1471a75e8`; docs size gate 24576 B. The `### Persistence of Partial
  Completion` anchors (`:44`, body `:46-51`) were re-taken 2026-10-24 and are unchanged.
- Region in scope: `:44-52` (subsection heading plus its body).

### Procedure

1. Land `implementations/20261024-144732_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`
   first (or in the same commit), so the canonical target of the new cross-reference exists.
2. Replace the body of `### Persistence of Partial Completion` (`:46-51`) with the text in `Method`.
3. Run the docs checker set in `Validation plan` and confirm no finding names this file (`AC-9`).

### Method

Replace `:46-51` with:

```markdown
If a workflow stops after some steps have run, the durable outcome is recorded in the workflow task
record through `StateStore.update_task_status()`:

- `"completed"` — every stage ran. The workflow engine is the only writer of this value.
- `"failed"` — a stage raised an exception, or the turn reported a soft error that the engine could not
  observe.
- `"halted"` — a retryable stage exhausted its attempts, a stage timed out, or the turn was cancelled
  while a stage was running. The workflow engine records the first two; the turn adapter records the
  cancellation, because the engine does not observe it.
- `"pending"` — the turn failed before any stage ran, so the record keeps the value it was created with.

**Canonical source**: the exit-path table and the writer for each outcome are documented in
[agent_03_03](agent_03_03_turn-processing-flow-workflow-engine.md). This chapter states only what a
partially completed turn leaves behind.

**Design judgment**: Completed steps are not persisted individually. Partial completion is **not**
automatically resumed — the user must resubmit the request. Adapter status writes are best-effort: a
persistence failure is logged at error level with the task id and the intended status, and is never
presented as an LLM error.
```

### Details

- The existing link syntax to a sibling chapter uses a bare basename
  (`agent_06_02_tool-execution-and-approval-approval.md` style appears in `agent_06_04:66` as
  `[agent_06_02](agent_06_02_tool-execution-and-approval-approval.md)`); the new link follows the same
  same-directory form. `check_docs_structure.py` resolves basenames through a corpus-wide index, so the
  cross-directory location of `agent_03_03` does not matter.
- Keep the fenced-free prose style of the chapter: no code block, no table, no line numbers, no `scripts/`
  path, no port number, no numeric configuration value.
- Keep the backticked `StateStore.update_task_status()` exactly as today: `check_docs_consistency.py`
  resolves backtick-quoted `name()` references against `scripts/`, and this one already resolves.
  Do not introduce a new backticked callable in this chapter.
- `"completed"` is added to the list even though the chapter is about partial completion, because the
  list's current shape reads as the complete set of durable outcomes; `AC-9` requires the same state
  machine in both chapters.

## Compatibility considerations

- `agent_03_03` and this chapter must not disagree about who writes each status (`AC-9`); the pointer in
  the new text is the mechanism that keeps them from drifting.
- `## Key Constraints` (`:59-62`) and `## Known Limitations` (`:66-67`) keep their existing "partial
  completion is not automatically resumed" claims, which stay true: the resume guard rejects `halted`
  tasks, and a cancellation now lands in that same state.
- `#### Behavior` (`:39-42`) and the audit `tool_approval` event description are untouched; approval
  persistence is independent of task status.
- `docs/23_agent/agent_04_01_state-and-persistence-state-model.md:44` and
  `docs/41_db/db_02_architecture_and_schema-schema-reference.md` §7 are not edited (the latter belongs to
  `plans/20261023-084918_plan.md`).
- No `docs/00_index.md` change (`UNK-04`).
- No code, test, config or generated-document interaction.

## Security considerations

- The reworded best-effort sentence must describe the log as carrying the task id and the intended status
  only, matching what the adapter writes, so the docs do not imply a wider payload.
- No secrets, no concrete configuration values, no port numbers.

## Rollback considerations

- Revert with `git checkout HEAD~1 -- docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`.
- If `_03` is reverted while this chapter keeps the cross-reference, the pointer targets a chapter that no
  longer states the state machine; revert both together or drop the canonical-source paragraph.
- The change is a single-section replacement with no heading or link removal, so a partial revert cannot
  orphan a reference from another document.

## Validation plan

- `uv run python tools/check_docs_structure.py "docs/23_agent/agent_06_04*.md"` — must print "All checks
  passed" (baseline: it does today).
- `uv run python tools/check_docs_quality.py` — no finding naming this file; specifically watch
  `content_similarity` against `agent_03_03#'Task Status Transitions'` (baseline: none today).
- `uv run python tools/check_docs_content_policy.py` (and with `--strict`) — no warning naming this file.
- `uv run python tools/check_docs_consistency.py --domain agent` — "No issues found."
- `uv run python tools/check_docs_japanese.py` — no Japanese text.
- `uv run python tools/check_metadata_field_policy.py` — no new Metadata or Status field (`GV-016`).
- Manual cross-read against `agent_03_03`'s `### Task Status Transitions`: same six outcomes, same writer
  per outcome, same `halted`-for-cancellation rule (`AC-9`).

## Completion criteria

- `### Persistence of Partial Completion` names all four durable outcomes and the writer for each, and no
  longer presents `failed` and `halted` as the complete record (`REQ-010`, `AC-9`).
- The section states that a cancelled turn is recorded `halted` and why the adapter, not the engine,
  records it (`AC-9`).
- The section names `agent_03_03` as the canonical source of the state machine.
- The section states that adapter status writes are best-effort and logged at error level.
- All docs checkers report no finding naming this file, and no other file was modified (`AC-9`).
- Front matter and every other section of the chapter are unchanged.

## Out of Scope

- Registering this chapter in `docs/00_index.md`'s task-scope table (`UNK-04`).
- Adding a state-machine table or a `### Task Status Transitions` subsection here.
- `## Responsibility Boundary`'s canonical-source list, `## Key Constraints` and `## Known Limitations`
  wording.
- Tool-level approval behavior, risk rules, and the `tool_approval` audit event — unchanged by this Plan.
- Anything about closing the in-flight attempt record a cancelled turn leaves behind (`DR-006`,
  `UNK-02`), and about resumability of a cancellation-halted task (`UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Not implemented; land with or after `_03` |
| 2 | Add or update tests per Validation plan | N/A: documentation row | — | — | Docs checkers are the validation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Baselines recorded 2026-10-24 in Procedure-local findings |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is a docs row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `_03` landing first so the canonical cross-reference resolves | False | — |
| 1 | Plan `UNK-04` (index registration) has no owner decision | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010`
- **Source issue**: `issues/20261021-093421_turn003_task-status-overwritten-after-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-125756_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-144732
- **Related target files**: `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`
