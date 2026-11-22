## Goal

Remove the delayed-input hand-off specification and document the input outcomes and Ctrl-C semantics (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` only; documentation text is written in English (`skills/DESIGN.md` Output language).

## Assumptions

- Verified: the document specifies the hand-off at line 41, Ctrl-C ending the REPL at lines 39 and 54, and cites `TestReadMultilineTimeout` and `TestCancelledRequestDelivery`, which the test rows replace.

## Design decisions

- Describe the behavior the code procedures implement; do not document anything the Plan did not decide.

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`

### Procedure
1. Replace the Hand-off After Timeout bullet with: late lines of timed-out or cancelled requests are discarded; outcomes are completed, timed_out, cancelled, eof, shutdown; partial multiline input is never auto-submitted.
2. Replace the Ctrl-C bullets: prompt discards the input, turn cancels the turn, job requests job cancellation (wired by the maintenance-job work), Ctrl-D and `/exit` shut down, SIGTERM and console close shut down gracefully; double Ctrl-C force exit is opt-in.
3. Replace the test names cited with the new ones from the test rows.
4. Document the one-line caveat that the line submitted after Ctrl-C or a multiline timeout is consumed by the abandoned read.

### Method
Edit the named sections in place; keep the front matter and keyword lists consistent.

### Details
- Keep the Shutdown Behavior section consistent with `TestAbandonedReadDoesNotDelayProcessExit`.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- The documentation checkers named in `rules/tool-gates.md` "When to run which tool" for a changed `docs/` file (run `uv run python tools/run_validation_gates.py`).

## Completion criteria

- The hand-off specification is gone; every cited test name exists; checkers pass.

## Out of Scope

Code changes and the CLI docs consolidation Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: docs/23_agent/agent_07_05_cli-and-commands-repl-io.md |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-009` (input outcomes, Ctrl-C semantics, hand-off removal)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`
