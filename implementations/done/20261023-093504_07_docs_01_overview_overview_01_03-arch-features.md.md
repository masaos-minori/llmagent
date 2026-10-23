## Goal

Correct the "Diagnostic Storage upon Session Termination" description in
`overview_01_03-arch-features.md` so it states the actual exit-sequence contract
(REQ-009, AC-8): persistence runs on every exit path, before resource shutdown,
and is gated on a session existing — not "after the REPL input loop ends".

## Scope

Docs change to `docs/01_overview/overview_01_03-arch-features.md` only. Reference
reads: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
(row 6, the sibling description), `scripts/agent/repl.py` (row 1, the code the doc
now describes).

## Assumptions

- Item 3 of the same list (`:69`, the WAL paragraph) is `shutdown001`'s region and
  is left to that Plan. This Plan edits only the lead sentence (`:65`) and items
  1-2 (`:67-68`).
- `_persist_after_loop` has been renamed to `_persist_session_state` by row 1; the
  doc must cite the new name.

## Design decisions

- **Rewrite the lead sentence.** Replace "After the REPL input loop ends" with the
  real reachability ("on every REPL exit path"), rename
  `_persist_after_loop` → `_persist_session_state`, and state that persistence runs
  before the resource shutdown sequence and is gated on a session existing.
- **Name the gate in items 1-2.** Each of the two persistence bullets states that
  it performs no write when no session was started.
- **Leave item 3 (`:69`) unchanged.**

## Alternatives considered

- Editing only the lead sentence and leaving items 1-2 — rejected: the gate is the
  defining behavior of both persistence actions, so both bullets must state it
  (REQ-009).

## Implementation

### Target file

`docs/01_overview/overview_01_03-arch-features.md`

### Procedure

1. **Rewrite the lead sentence** at `:65`. Replace:

   > After the REPL input loop ends, session diagnostics and memory are persisted
   > (`AgentREPL._persist_after_loop`) and then the resource shutdown sequence runs
   > (`ResourceShutdownCoordinator.close_resources`). The following actions are
   > performed:

   with:

   > On every REPL exit path — normal exit, startup failure, startup interrupt, and
   > input-loop error — session diagnostics and memory are persisted
   > (`AgentREPL._persist_session_state`) and then the resource shutdown sequence
   > runs (`ResourceShutdownCoordinator.close_resources`), persist first because it
   > reads clients that shutdown releases. Persistence is gated on a session
   > existing: when no session was started (for example on a startup failure) the
   > persist step runs and writes nothing, by design. The following actions are
   > performed:

2. **Name the gate in items 1-2** (`:67-68`). Append a clause to each:
   - Item 1: after "…to `DiagnosticStore`." add " — no row is written when no
     session was started."
   - Item 2: after "…rule-based logic." add " — no memory is extracted or
     persisted when no session was started."
3. **Leave item 3 (`:69`) and everything after unchanged.**

### Method

Read-only reference reads of `scripts/agent/repl.py` (row 1) and
`scripts/agent/session_persister.py` (row 3) confirm the persist-then-close order
and the `ctx.session.session_id` gate the text now states;
`docs/23_agent/agent_10_01_*` (row 6) states the same contract so the two
documents agree.

### Details

- Keep the "(Explicit in code — …)" attribution style the section already uses.
- Do not touch item 3 (`:69`); it is `shutdown001`'s WAL region.

## Compatibility considerations

### Corrections found while implementing

- Lead sentence and items 1-2 edited as written; item 3 untouched.


- Cross-references `agent_10_01_*` (row 6); keep the two descriptions consistent
  (same order, same gate).
- `agent_07_05_cli-and-commands-repl-io.md` and `agent_02_runtime-architecture.md`
  are not edited: their shutdown paragraphs describe the input loop's own bound
  and prompt behavior, which this Plan does not change.

## Security considerations

- N/A: documentation change only.

## Rollback considerations

- Single logical commit; `git checkout -- docs/01_overview/overview_01_03-arch-features.md`
  restores HEAD. Reversible.

## Validation plan

- `uv run python tools/check_docs_structure.py docs/01_overview/overview_01_03-arch-features.md`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`
  (`routing.md` "Any `docs/*.md` file was added or edited", AC-8).

## Completion criteria

The lead sentence states persistence on every exit path, before resource shutdown,
gated on a session existing; items 1-2 name the gate; item 3 is untouched; AC-8
holds.

## Out of Scope

- The production bracket — row 1. The `agent_10_01` Resource Cleanup section — row
  6. `shutdown001`'s item 3 (`:69`) — not this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the lead sentence (:65) | Completed | 20261023-150353 | 20261023-150353 | REQ-009 implemented; full suite 9879 passed |
| 2 | Name the gate in items 1-2 (:67-68) | Completed | 20261023-150353 | 20261023-150353 | REQ-009 |
| 3 | Run documentation validation sequence (`rules/toolchain.md`) | Completed | 20261023-150353 | 20261023-150353 | AC-8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-2 | Shared list also touched by `shutdown001` (`plans/20261022-043330_plan.md`), which owns item 3 (`:69`). Implement `shutdown001` first; this Plan owns only the lead sentence and items 1-2. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 1-2 | Ordering | Open | implementer | after `plans/20261022-043330_plan.md` implemented |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `docs/01_overview/overview_01_03-arch-features.md`