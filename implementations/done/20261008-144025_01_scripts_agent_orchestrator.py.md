## Goal
Remove the workflow fallback mode, the duplicated turn-processing code, and the compatibility wrappers from the Orchestrator, make a workflow load failure a fatal construction error, and correct the docstrings (REQ-001, REQ-002, REQ-003 of the Plan).

## Scope
- Change only the Orchestrator module: the sentinel definition, the constructor's load handling, the turn entry point's fallback branch, the wrapper block at the end of the class, the duplicated turn-processing and tool-override code, the docstrings, and imports that become unused.

## Assumptions
- The adapter already contains identical turn-processing and tool-override code, so the orchestrator copies are dead in production (verified by search).
- No production code calls the wrappers; tests are rewritten by procedures 02 and 03, which run before this one.
- The user confirmed that no environment relies on the fallback and that the production definition file is sound.

## Design decisions
- The constructor still loads the definition in every case (mandatory); a load or missing-file error becomes a runtime error carrying the definition file path and the original cause, chained.
- The turn entry point keeps its approval-pending, pause, and execute steps and loses only the fallback branch.
- Delete the orchestrator's duplicate turn-processing and tool-override methods together with the wrappers; their imports go too.

## Alternatives considered
- Keeping the duplicate turn-processing method: rejected; it is dead code identical to the adapter's.
- Keeping a thin fallback gated by configuration: rejected by ADR-001 Decision 4.

## Implementation
### Target file
scripts/agent/orchestrator.py

### Procedure
1. Confirm procedures 02 and 03 have landed and the new construction-failure tests fail.
2. Remove the sentinel definition and the fallback flag; replace the constructor's try/except with one that raises a runtime error (path and cause, chained).
3. Remove the fallback branch from the turn entry point.
4. Remove the wrapper block, the duplicate turn-processing method, the tool-override context manager, and the property/setter for the pause state.
5. Rewrite the module and class docstrings; remove imports reported unused by the linter.
6. Run format, lint, type, security checks and the agent tests.

### Method
Edit in place; keep the constructor's component wiring, the approval and pause checks, the workflow status method, and the discard callback used by the components.

### Details
Error message shape: the definition could not be loaded, followed by the definition file location and the underlying error text; raised with the original exception chained. Docstrings: describe the facade as composing the concern classes that exist (background task monitor, audit emitter, conversation state manager, LLM turn executor, workflow engine adapter), listed once, with no mention of a coordinator module or backward compatibility.

## Compatibility considerations
- Public behavior changes only for a failing definition (the construction fails); everything else is unchanged.
- Anything that imported the removed private names must already have been updated (search shows only two test modules).

## Security considerations
- Closes a path where the Agent ran with stage settings and retry policy silently replaced by defaults.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format scripts/agent/orchestrator.py`, `uv run ruff check scripts/agent/orchestrator.py`, `uv run mypy --no-namespace-packages scripts/` (tracer-module errors are pre-existing), `uv run bandit scripts/agent/orchestrator.py`, `PYTHONPATH=scripts uv run lint-imports` (one pre-existing violation), `rg -n '_fallback_mode|_FALLBACK_WORKFLOW_DEF|turnd_coordinator' scripts tests docs`.
- `uv run pytest tests/agent tests/integration -q --timeout=60`, then the full suite once.

## Completion criteria
- No fallback names, wrappers, or stale docstring names remain; construction fails with the specified error; all tests pass (REQ-001, REQ-002, REQ-003).

## Out of scope
- Other Orchestrator logic, the workflow engine, startup preflight, deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make the load failure fatal and remove the fallback | Completed | 20261008-145219 | 20261008-145219 |  |
| 2 | Remove wrappers and duplicated turn-processing code | Completed | 20261008-145219 | 20261008-145219 |  |
| 3 | Fix docstrings and imports | Completed | 20261008-145219 | 20261008-145219 |  |
| 4 | Run format, lint, type, security checks and tests | Completed | 20261008-145219 | 20261008-145219 |  |

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
- **Requirement ID**: REQ-001 (fatal load failure), REQ-002 (docstrings), REQ-003 (remove wrappers)
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: scripts/agent/orchestrator.py