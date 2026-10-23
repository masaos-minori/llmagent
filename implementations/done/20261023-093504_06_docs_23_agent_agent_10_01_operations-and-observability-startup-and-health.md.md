## Goal

State the corrected exit-sequence contract in the Resource Cleanup section of
`agent_10_01_operations-and-observability-startup-and-health.md` (:74-83): the
session-persist step is the first member of the single `finally` bracket, runs on
every exit path, and writes nothing on a startup failure/interrupt by design
(REQ-001, REQ-008, REQ-009, AC-8).

## Scope

Docs change to `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
only. Reference reads: `docs/01_overview/overview_01_03-arch-features.md` (row 7,
the sibling description), `scripts/agent/repl.py` (row 1, the code the doc now
describes).

## Assumptions

- This document's own update trigger is "change `scripts/agent/repl.py` or its
  shutdown path" (`docs/00_index.md:145` maps Agent startup / verification /
  troubleshooting here), so the Resource Cleanup section is the correct home.
- `shutdown001` (`20261022-043330`) owns the Known-Limitations bullet at
  `:142-146` (in particular `:144`, the WAL-timeout item). This Plan edits only
  the Resource Cleanup section (`:74-83`) and leaves `:142-146` untouched.

## Design decisions

- **Insert the persist step as the first ordered member.** The section currently
  lists four steps (`:78-81`) after "The cleanup runs in a `finally` block in the
  following order:". Add the persist step ahead of them and restate the ordering
  sentence to reflect that persistence precedes resource close.
- **State the by-design skip.** Add a sentence that on a startup failure or
  interrupt the persist step runs and writes nothing, because no session exists
  (the write-or-skip decision is owned by `SessionPersister`, keyed on
  `ctx.session.session_id`).
- **Keep the four existing steps and their guard sentence (`:83`) unchanged.**

## Alternatives considered

- Adding a new subsection instead of editing the existing one — rejected: the
  persist step belongs in the same ordered list the code produces, so readers hit
  the one place that states the full bracket (REQ-009).

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. **Rewrite the ordering sentence and prepend the persist step.** Replace the
   paragraph at `:76` ("Resources are closed once, when the interactive session
   ends or when startup fails or is interrupted; they are not closed during a
   successful startup. The cleanup runs in a `finally` block in the following
   order:") and the numbered list at `:78-81` with:

   > Resources are closed once, when the interactive session ends or when startup
   > fails or is interrupted; they are not closed during a successful startup. The
   > exit sequence runs in a single `finally` block in the following order:
   >
   > 0. **Persist session state** — writes a session summary and session memory,
   >    but only when a session was started. On a startup failure or interrupt no
   >    session exists, so this step runs and writes nothing, by design (the
   >    write-or-skip decision is owned by `SessionPersister`, keyed on
   >    `ctx.session.session_id`).
   > 1. WAL checkpoint (with PASSIVE → TRUNCATE fallback)
   > 2. WAL backup (with path validation)
   > 3. `lifecycle.shutdown_all()`
   > 4. `http.aclose()`

   Persist is first because it reads `ctx.services` clients that
   `close_resources()` releases; containing its failures keeps a persistence error
   from replacing the exception the process was already reporting.

2. **Leave `:83` and everything from `:84` onward unchanged**, including the
   Known-Limitations region at `:142-146` (owned by `shutdown001`).

### Method

Read-only reference reads of `scripts/agent/repl.py` (row 1) confirm the
persist-then-close order and the `SessionPersister` gate the text now states;
`docs/01_overview/overview_01_03-arch-features.md` (row 7) states the same
contract so the two documents agree.

### Details

- Do not add a new Known-Limitations bullet: per
  `docs/00_governance/governance_00_document-guide.md:47-49` known limitations are
  managed centrally, and this records a *design decision*, not a limitation.
- UNK-01 / UNK-04, if still open at the end of implementation, are registered as
  Part 2 inventory entries in `docs/00_governance/governance_03_issue-and-
  uncertainty-management.md` (`:94-122`), not here.

## Compatibility considerations

### Corrections found while implementing

- Steps renumbered 1-5 (no `0.` item); persist is step 1.


- This section cross-references `overview_01_03-arch-features.md` (row 7); keep
  the two descriptions consistent (same order, same gate).
- `agent_07_05_cli-and-commands-repl-io.md` and `agent_02_runtime-architecture.md`
  are not edited: their shutdown paragraphs describe the input loop's own bound
  and prompt behavior, which this Plan does not change (both are `repl001`/
  `repl002` rows).

## Security considerations

- N/A: documentation change only.

## Rollback considerations

- Single logical commit; `git checkout -- docs/23_agent/agent_10_01_*` restores
  HEAD. Reversible.

## Validation plan

- `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`
  (`routing.md` "Any `docs/*.md` file was added or edited", AC-8).

## Completion criteria

The Resource Cleanup section states the persist step as the first member of the
single `finally` bracket, gated on a session existing and writing nothing on a
startup failure by design, followed by the four unchanged steps; `:142-146` is
untouched; AC-8 holds.

## Out of Scope

- The production bracket — row 1. The `overview_01_03` lead sentence and items 1-2
  — row 7. `shutdown001`'s `:144` and item 3 — not this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the ordering sentence + prepend the persist step | Completed | 20261023-150352 | 20261023-150352 | REQ-001, REQ-009 implemented; full suite 9879 passed |
| 2 | State the by-design skip on startup failure/interrupt | Completed | 20261023-150352 | 20261023-150352 | REQ-003, AC-8 |
| 3 | Run documentation validation sequence (`rules/toolchain.md`) | Completed | 20261023-150352 | 20261023-150352 | AC-8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-2 | Shared section also touched by `shutdown001` (`plans/20261022-043330_plan.md`), which owns `:142-146` (item 3 / `:144`). Implement `shutdown001` first; this Plan owns only `:74-83`. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 1-2 | Ordering | Open | implementer | after `plans/20261022-043330_plan.md` implemented |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-008, REQ-009
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`