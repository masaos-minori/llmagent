# Obtain owner confirmation of no external callers for agent package re-exports

## Priority
Medium

## Summary
Obtain from the owner confirmation that nothing outside the repository imports the twelve names that `scripts/agent/__init__.py` re-exports, plus any removal-notice policy, so that `compat003` can remove those re-exports. This issue tracks the owner input; it is not code work. Once the confirmation is recorded here, close this issue and proceed with `compat003`.

## Background
- `compat003` removes the component classes and the `AgentREPL` facade that `scripts/agent/__init__.py` re-exports "for backward compatibility", after the owner confirms that nothing outside the repository imports them from the package, and adds a test that locks the removal.
- An investigation dated 2026-10-20 re-checked the re-exports against the current source: `__all__` lists exactly twelve names — `ReplInputLoop`, `SessionPersister`, `WalCheckpointManager`, `ResourceShutdownCoordinator`, `StartupBanner`, `SignalHandler`, `AgentREPL`, `BgTaskMonitor`, `AuditEventEmitter`, `ConversationStateManager`, `LlmTurnExecutor`, `WorkflowEngineAdapter`. Every import in `scripts/`, `tests/`, and `tools/` uses the canonical submodules (for example `from agent.repl_input_loop import ReplInputLoop`), never the top-level package re-export; `import agent.context` in a clean interpreter loads the whole REPL stack through the package `__init__`. (Confirmed by repository evidence)
- The package is part of the distributed code: `pyproject.toml` includes `agent*` in package discovery and `init.d/llama-agent` starts the Agent with `python -m agent`. Whether a script, plugin, or tool outside the repository imports the re-exports is not visible from the repository. (Needs confirmation)
- The Glossary in `docs/00_governance/governance_02_documentation-metadata.md` uses the module docstring as its example of Backward Compatibility; `compat009` stops citing it.

## Problem
The re-export layer has no in-repository user but leaves an undocumented support promise to unknown external callers, with no owner and no end date. Removing the re-exports without confirming there is no external user risks breaking an operator script, plugin, or tool that imports `agent.AgentREPL` etc.

## Reason for Change
Dead public surface: twelve re-exports with zero in-repository users that still run import side effects on every `import agent`. Removing them narrows the package's public API to the canonical module paths. The risk is external consumers, which is exactly why the removal is gated on owner confirmation rather than on the in-repository reachability check alone.

## Implementation Intent
This is an inquiry-and-record task, not a code change. Ask the owner whether any external importer exists and whether a removal-notice policy applies, record the answers verbatim in the Owner Input Record section of this issue, and hand the recorded answers to `compat003`. Do not infer external usage from the repository.

## Target Files or Areas
- `issues/20261021-092513_owner003_...` (this issue; the answer record lives here)
- `issues/20261020-122918_compat003_...` (the parent issue this unblocks)
- `owner-question-packet.md` (working questionnaire; being retired once these issues exist)

## Required Changes
- Obtain from the owner confirmation that no script, plugin, or operations tool outside the repository imports any of the twelve names from `agent`.
- Obtain whether there is a release or support policy requiring a notice before a public import path is removed.
- Record both answers in the Owner Input Record section below with the answerer and date.

## Constraints
- Do not infer external usage from the repository. Record only owner-supplied answers.
- Do not start the removal until the confirmation is recorded. If an external user is found, stop and record the user, the support period, and the removal version instead of removing that name.
- Answers may be supplied in English or Japanese; record them verbatim.

## Acceptance Criteria
- **AC-1**: The Owner Input Record section records the owner's confirmation that no external importer exists (or names the external user, support period, and removal version if one exists).
- **AC-2**: The Owner Input Record section records whether a removal-notice policy applies.
- **AC-3**: Every answer carries an answerer and a date.

## Testing Expectations
Not required: this issue produces recorded owner input, not code. Verify AC-1..AC-3 by inspection.

## Documentation Impact
None beyond this issue's own Owner Input Record. The recorded answers feed `compat003`, which removes the re-exports.

## Out of Scope
- Removing the re-exports or editing `scripts/agent/__init__.py`. That is `compat003`.
- Adding a replacement public API, alias, or deprecation period.
- The sibling backward-compatibility items `requeue_event()`, `read_json_file()`, and the export `md` alias.

## Dependencies
- **Unblocks**: `compat003` (`issues/20261020-122918_compat003_...`); `compat003` cannot start the removal without this confirmation.
- **Depends on**: `compat009` so the Glossary no longer cites the removed docstring before the re-exports are removed.
- Sibling-issue check: no other open issue under `issues/` tracks external usage of the agent package re-exports.

## Unresolved Questions
- Does any script, plugin, or operations tool outside the repository import any of the twelve names from `agent`?
- Is there a release or support policy requiring a notice before a public import path is removed?

## AI Implementation Instruction
- This issue is an inquiry-and-record task. Do not touch `scripts/agent/__init__.py` or add any alias or deprecation scaffolding.
- Ask the owner the questions above and record the answers verbatim in the Owner Input Record section with an answerer and date.
- Do not infer or guess external usage from the repository. If an external user is found, record the user, the support period, and the removal version, and do not remove that name.
- When the confirmation is recorded and AC-1..AC-3 hold, close this issue and hand the recorded answers to `compat003`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-092513
- **Related target files**: `issues/20261021-092513_owner003_...`, `issues/20261020-122918_compat003_...`

## Owner Input Record
| Item | Answer | Answerer / Date |
|---|---|---|
| External importer of the twelve names exists? | _pending_ (confirm none) | — |
| Removal-notice policy applies? | _pending_ | — |
