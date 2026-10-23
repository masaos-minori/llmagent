## Goal

Correct the inaccurate statement at `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md:78`
("The original unexecuted assistant message is not persisted.") and state the two
real cases for what happens to an unexecuted assistant message when the main loop
runs (`AC-6`).

## Scope

Documentation update to `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
only. Scope rule: only the paragraph at `:70-80`. `### Hints on Guard Triggering`
(:80-86) stays as written. Reference reads: `scripts/agent/llm_turn_runner.py`
(the assistant persist at `:107-112` and the two check sites at `:98-105`,
`:122-130`). Dependent production file: `scripts/agent/tool_runner.py` (row 1).

## Assumptions

- At `:78` the sentence is true only of the guard fallback at
  `_finalize_after_guard` (`llm_turn_runner.py:242`), and reads as the opposite of
  the main-loop persist at `:107-112`; the correction must not contradict the
  tool001 plan, which edits `:33` and `:110` of the same file.

## Design decisions

- Replace the single inaccurate sentence with the two real cases, keeping the
  surrounding paragraph structure intact.

## Alternatives considered

- Rewriting the whole guard section — rejected by the scope rule; only `:78` is
  wrong.

## Implementation

### Target file

`docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`

### Procedure

Replace the sentence at `:78` ("The original unexecuted assistant message is not
persisted.") with two cases:

1. A guard trip *before* the assistant persist writes nothing — the turn-level
   check at `llm_turn_runner.py:98-105` fires and `_finalize_after_guard` returns
   without persisting the unexecuted assistant message.
2. A round that fails *after* the persist leaves a complete round: the assistant
   message plus one `role='tool'` row per declared `tool_call_id` (the failing
   round still synthesizes the missing rows via `execute_all_tool_calls`).

### Method

- Edit the single paragraph at `:70-80`. Do not touch `### Hints on Guard
  Triggering` (:80-86): one hint per trip, never injected into history.

### Details

- The correction must not contradict `plans/20261022-092413_plan.md`, which edits
  `:33` and `:110` of this same file; the two sections are disjoint.

## Compatibility considerations

- Documentation only; no code, config, or `docs/00_index.md` change.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- Revert the single-sentence edit; `git checkout -- docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`.

## Validation plan

- `uv run python tools/check_docs_structure.py`, `uv run python
  tools/check_docs_consistency.py`, `uv run python tools/check_docs_content_policy.py`
  report no finding (`AC-6`); the sentence at `:78` no longer appears.

## Completion criteria

`:78` states the two real cases (pre-persist guard trip writes nothing; a
post-persist round failure leaves a complete round); `### Hints on Guard
Triggering` is unchanged; all three docs validators pass.

## Out of Scope

- Extending `### Result Reflection in History` in `agent_06_01` — row 8.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `:78` with the two real cases (AC-6) | Pending | — | — | Phase 3 |
| 2 | Run docs validators (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: N/A: documentation section (AC-6)
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
