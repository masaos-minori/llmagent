## Goal

Update the REPL input document so the interrupt and shutdown behavior it states matches the machine the Plan installs: shutdown requests arm one deadline, post-shutdown input is refused, and a second Ctrl-C interrupts the running step instead of being ignored (REQ-003: no new work after shutdown starts; REQ-011: second-signal behavior).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the input-handling bullets, the Shutdown Behavior subsection, and the Ctrl-C key constraint in this document.
- Out of scope: the input loop implementation (row 8), the signal handler (row 10), and the budget itself (row 1).

## Assumptions

- The input-handling bullets are `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:38-40`: EOF/Ctrl-D, Ctrl-C acting by input state, and the paths that begin graceful shutdown.
- The Shutdown Behavior subsection is `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:47`, which states the SIGTERM behavior and the `_GRACEFUL_TIMEOUT_S` bound on the cancelled-turn wait.
- The key constraint at `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:56` states that Ctrl-C never ends the REPL by itself, and the Plan keeps that property.
- The Ctrl-C bullet already anticipates an opt-in force exit during shutdown; the Plan supplies the configuration key that opt-in reads.

## Step 3b verification against the current source (20261125-122600)

- Anchors hold: the Ctrl-C and shutdown-starting bullets are `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:39-40`, the Shutdown Behavior bullet `:47`, and the Ctrl-C constraint `:56`.
- Procedure step 3 is corrected against the code: the refusal is one console warning line naming the phase (`ReplInputLoop._report_shutdown_refusal`, `scripts/agent/repl_input_loop.py:149-157`); what the shutdown report records is the refused-write count (`ShutdownReport.refused_write_count`), not a record per refused command or turn. The document states the line and the write count.
- Procedure step 4 names `InputOutcome.SHUTDOWN`; the document's existing outcome vocabulary at `:41` uses the enum value `shutdown` (`scripts/agent/repl_input_controller.py:42`), and `ReplInputController.shutdown()` settles the open request with it (`:249`), so the document keeps that vocabulary.
- The force-exit opt-in is `shutdown_force_exit_on_second_sigint` read once at `SignalHandler` construction (`scripts/agent/signal_handler.py:100-105`); the interrupt request on an armed budget is `:129-134`.

## Design decisions

- Keep "Ctrl-C never ends the REPL by itself" and change only what a second Ctrl-C does during shutdown: the Plan's stated defect is the unbounded sequence, not the accidental-Ctrl-C protection.
- Describe the refusal as a user-visible one-line refusal plus a recorded step outcome, because REQ-003 is about what the user sees and what the report holds.
- State the pending-approval resolution as `InputOutcome.SHUTDOWN`, which is the value the input loop already uses for a shutdown-terminated request, rather than inventing a new user-facing term.
- Keep the test names the document cites (`TestInterruptByState`, `TestSignalDuringPromptEndsLoop`) and add new ones only where a behavior has no existing test name to point at.
- Compatibility impact: documentation only.

## Alternatives considered

- Document the second Ctrl-C as "force exit" — rejected: the default is interrupting the running step, and `os._exit` is reachable only through `shutdown_force_exit_on_second_sigint` (new).

## Implementation
### Target file
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`

### Procedure
1. Update the Ctrl-C bullet at `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:39`: during shutdown a Ctrl-C requests an interrupt on the step in progress, and the process exits through the force-exit path only when `shutdown_force_exit_on_second_sigint` (new) is true.
2. Update the shutdown-starting paths at `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:40` to state that SIGTERM, Ctrl-D, and `/exit` arm one deadline that later requests cannot extend.
3. Rewrite the Shutdown Behavior bullet at `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:47`: the cancelled-turn wait is the remaining time of the armed budget, and once the phase is draining, new commands and turns are refused with one line and a recorded outcome.
4. Add that a pending approval or confirmation resolves `InputOutcome.SHUTDOWN` when shutdown begins while it is open.
5. Keep the constraint at `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:56` and state the interrupt behavior it now refers to.

### Method

- Bullet-level rewrites inside the existing subsections; no new heading.

### Details

- The refusal wording is the same one the input loop prints, so the document and the console agree (row 8).

## Compatibility considerations

- Runs after rows 1, 8 and 10: the behavior it documents is installed by those rows.
- `docs/00_index.md` maps CLI view and readline claims to this file together with `docs/23_agent/agent_07_02_cli-and-commands-cliview.md`; if the refusal line is also described there, the two statements must match.

## Security considerations

- N/A: no path, command, or configuration value is quoted.

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | No finding |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claims |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Documented interrupt behavior matches `scripts/` |

## Completion criteria

- The document states one deadline, the post-shutdown refusal, the `InputOutcome.SHUTDOWN` approval resolution, and the configured force-exit opt-in, and still states that Ctrl-C alone never ends the REPL.

## Out of Scope

- The input loop and signal handler implementations, and the shutdown step sequence (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the interrupt and shutdown-behavior wording | Completed | 20261125-130118 | 20261125-130118 | Phase 7 Ctrl-C, shutdown-starting, and constraint bullets rewritten; Step 3b note added |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-130118 | 20261125-130118 | quality/structure/policy clean; consistency shows only the pre-existing /db warning |

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
- **Requirement ID**: REQ-003 (no new work after shutdown starts), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`