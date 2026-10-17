# Surface startup rollback failures beyond a log line

## Priority
Medium

## Summary
On startup failure, `StartupOrchestrator.run()` rolls back spawned subprocess
via `lifecycle.shutdown_all()`. If that rollback itself fails, the failure is
recorded only by `logger.error(...)` and then the original startup error is
re-raised, so the rollback failure is not surfaced to the operator/console. Make
rollback failures observable at a level that reaches the operator.

## Background
`scripts/agent/startup.py` `StartupOrchestrator.run()` wraps the startup sequence
in a try/except:

```python
except Exception as setup_err:
    try:
        await self._ctx.services_required.lifecycle.shutdown_all()
    except Exception as shutdown_err:
        logger.error(
            "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
            shutdown_err,
        )
    raise setup_err
```

`docs/23_agent/agent_10_01_...startup-and-health.md` Known Limitations states:
"A failure of the rollback `shutdown_all()` during startup failure is only logged;
the original startup exception is re-raised and nothing is shown on the console
for the rollback failure."

## Problem
When rollback fails, the only signal is a `logger.error` line. Depending on the
logging configuration that line may not reach the operator's console/stderr, and
it is immediately followed by the re-raised `setup_err`, which can obscure the
rollback failure. Orphaned subprocesses are a real operational hazard (leaked
children, open ports, dangling handles), and the operator has no guaranteed
console-visible indication that rollback failed.

## Reason for Change
Rollback failure during startup is a critical operational condition (possible
orphaned subprocesses). Relying solely on a logger line that may not reach the
console risks silently leaving orphaned processes. The failure should be surfaced
in a way that reliably reaches the operator.

## Implementation Intent
When the rollback fails, emit an operator-visible message in addition to (not
instead of) the existing `logger.error`. Use the process-level stderr output that
the REPL/view already uses for critical startup messages, so it reaches the
console regardless of logger level config. Preserve the re-raise of `setup_err`
so the original failure is not masked. Name the boundary: only the rollback-failure
branch changes; normal startup success and normal error paths are untouched.

## Target Files or Areas
- `scripts/agent/startup.py` (`StartupOrchestrator.run`, lines ~76-85)
- The view/stderr output mechanism used for other critical startup messages (confirm the existing entry point before coding)

## Required Changes
- On rollback (`shutdown_all()`) failure, emit a console-visible warning/error
  (stderr via the existing view/output path) in addition to the logger line.
- Keep the final `raise setup_err` unchanged.
- Do not change behavior when rollback succeeds.

## Constraints
- Do not swallow or alter the original `setup_err`; it must still be re-raised.
- Do not duplicate the message in a way that confuses log aggregation.
- Reuse the existing operator-output channel rather than adding a new one.

## Acceptance Criteria
- A failing `shutdown_all()` during startup produces a console-visible signal in
  addition to the logger line.
- The original startup error is still re-raised unchanged.
- Rollback-success path is unaffected.

## Testing Expectations
- Test that a rollback failure surfaces an operator-visible message (assert stderr
  or view output contains the rollback-failure indicator).
- Regression test that the original error is still raised.
- Regression test that successful rollback is unchanged.

## Documentation Impact
Update the Known Limitations bullet in
`docs/23_agent/agent_10_01_...startup-and-health.md` to reflect the new
surfacing, or move the item to a resolved note.

## Out of Scope
- Changing what `shutdown_all()` does or which resources it shuts down.
- Other shutdown paths (`ResourceShutdownCoordinator.close_resources`).
- Changing normal (non-failure) startup logging.

## Dependencies
- N/A: none

## Unresolved Questions
- Which existing output channel reliably reaches the console in all deployment
  modes (REPL TUI vs. embedded/HTTP); confirm before implementing.
- Whether the message should also be recorded in the audit/failure report.

## AI Implementation Instruction
Only edit the rollback-failure branch in `scripts/agent/startup.py`. Add an
operator-visible emit (reuse the existing view/stderr channel used for other
critical startup messages) alongside the existing `logger.error`; do NOT remove or
alter the `raise setup_err`. Do not touch the success path or other shutdown
coordinators. First identify the existing console-output entry point to reuse.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123338
- **Related target files**: `scripts/agent/startup.py`
