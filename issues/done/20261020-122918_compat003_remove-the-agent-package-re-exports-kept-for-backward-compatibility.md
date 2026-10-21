# Remove the Agent package re-exports kept for backward compatibility

## Priority
Medium

## Summary
Remove the component classes and the `AgentREPL` facade that `scripts/agent/__init__.py` re-exports "for backward compatibility", after the owner confirms that nothing outside the repository imports them from the package. Add a test that locks the removal so the re-exports and their import side effect do not return.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility features. It read documents only; the facts below were re-checked against the current code on 2026-10-20. The investigation proposed High; the evidence below (no in-repository user, no runtime failure mode) supports Medium under the maintainability criterion.
- The module docstring of `scripts/agent/__init__.py` says it "Exports all component classes and the AgentREPL facade for backward compatibility". It imports and lists twelve names: `ReplInputLoop`, `SessionPersister`, `WalCheckpointManager`, `ResourceShutdownCoordinator`, `StartupBanner`, `SignalHandler`, `AgentREPL`, `BgTaskMonitor`, `AuditEventEmitter`, `ConversationStateManager`, `LlmTurnExecutor`, `WorkflowEngineAdapter`. (Explicit in code)
- No file under `scripts/`, `tests/`, or `tools/` imports any of those names from the package. The entry point `scripts/agent/__main__.py` imports `AgentREPL` from `agent.repl` directly, and the tests that use `from agent import ...` import submodules such as `factory`, `context`, `lifecycle_router`, and `http_lifecycle`. (Explicit in code: searched `from agent import`, `import agent`, and attribute access on the package)
- Because `__init__.py` executes the twelve imports, importing any submodule loads them all. Running `import agent.context` in a clean interpreter loads `agent.repl`, `agent.repl_input_loop`, `agent.startup_banner`, `agent.signal_handler`, and `agent.workflow_engine_adapter`. (Verified by execution)
- The package is part of the distributed code: `pyproject.toml` includes `agent*` in the package discovery, and `init.d/llama-agent` starts the Agent with `python -m agent`. Whether a script, plugin, or other tool outside the repository imports the re-exports is not visible from the repository. (Needs confirmation)
- The Glossary in `docs/00_governance/governance_02_documentation-metadata.md` uses this docstring as its example of Backward Compatibility.

## Problem
A re-export layer with no in-repository user adds a second import path for each component and forces every `agent.*` import to load the whole REPL stack, which hides import cycles and side effects. It also leaves an undocumented support promise to unknown external callers, with no owner and no end date.

## Reason for Change
Removing it narrows the package boundary to the real module paths, removes an import side effect, and removes a compatibility promise nobody can name a user for. The risk is limited to unknown external callers, which the owner can confirm before the change.

## Implementation Intent
- Make `scripts/agent/__init__.py` carry no re-exports and import nothing from its submodules, keeping only the module docstring.
- Do not add a compatibility alias, a lazy `__getattr__` forwarder, or a deprecation shim; this is an intentional breaking change after the owner's confirmation.
- Lock the removal with a test: the package exposes none of the twelve names, and importing a lightweight submodule does not load `agent.repl`.
- Leave the Glossary example to `compat009`, which replaces symbol-specific examples; this issue must not leave a stale example behind.

## Target Files or Areas
- `scripts/agent/__init__.py` (remove imports and `__all__`; update the docstring)
- `tests/agent/test_import_smoke.py` or a new test beside it (lock the removal)
- `docs/00_governance/governance_02_documentation-metadata.md` (Glossary example; owned by `compat009`)
- Read for evidence: `scripts/agent/__main__.py`, `pyproject.toml`, `init.d/llama-agent`

## Required Changes
- Obtain the owner's confirmation that no external script, plugin, or tool imports the twelve names from the package.
- Remove the twelve imports and `__all__` from `scripts/agent/__init__.py`.
- Add a test asserting that none of the twelve names is an attribute of the `agent` package and that importing a submodule such as `agent.context` does not import `agent.repl`.
- Run the full Agent test suite, mypy with the project's invocation, and the import-layer check to confirm nothing depended on the removed names or on the side effect.
- Confirm that `python -m agent` still starts.

## Constraints
- Do not remove a name if the owner reports an external user; in that case stop and record the user, the support period, and the removal version instead.
- Preserve runtime behavior: the REPL, startup, and shutdown paths must work unchanged.
- Follow the project's import-layer contract in `skills/DESIGN.md` (Shared Vocabulary) and the coding rules in `rules/coding.md`.
- Do not use a suppression comment to hide a new import cycle; fix the cycle.

## Acceptance Criteria
- `scripts/agent/__init__.py` has no re-exports and no import of its submodules.
- A test fails if any of the twelve names is restored on the package or if importing `agent.context` loads `agent.repl`.
- `python -m agent` starts, and the full test suite passes.
- mypy passes with `--no-namespace-packages`, and ruff passes.
- The Glossary no longer cites the removed docstring (handled by `compat009`).

## Testing Expectations
- New regression test for the removed names and the removed import side effect.
- Full pytest run, `uv run mypy --no-namespace-packages`, `uv run ruff check`, `uv run python tools/check_dependency_graph_cycles.py`, and `uv run python tools/check_module_size.py`.
- Manual check: start the Agent entry point and confirm the REPL banner appears.

## Documentation Impact
Yes, but limited. The Glossary example is replaced under `compat009`. If any Agent document lists the package re-exports as the public import path, correct it to the module paths. No history of the removal is written into current documents.

## Out of Scope
- Moving or renaming any component module.
- Adding a replacement public API, a compatibility alias, or a deprecation period.
- Changing the other Backward-Compatibility-related items (`requeue_event()`, `read_json_file()`, the export `md` alias).
- Any change to `agent.repl` behavior.

## Dependencies
- Depends on: owner confirmation of external callers (see Unresolved Questions), and on `compat009` so the Glossary no longer cites the removed docstring.
- Sibling-issue check: no open issue under `issues/` touches `scripts/agent/__init__.py`.

## Unresolved Questions
- Does any script, plugin, or operations tool outside the repository import any of the twelve names from `agent`? (Needs confirmation)
- Is there a release or support policy that requires a notice before a public import path is removed? (Needs confirmation)
- Should the package `__init__` stay entirely empty, or keep a one-line docstring only?

## AI Implementation Instruction
- Do not start the removal until the owner has confirmed there is no external user; if that is not recorded, stop and report the open question.
- Change only `scripts/agent/__init__.py` and the new or extended test; do not touch other modules, and do not add any forwarding or compatibility code.
- If a test, tool, or module fails because it relied on a removed name or the import side effect, fix that caller to import from the canonical module; do not restore the re-export.
- Run the commands in Testing Expectations before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-122918
- **Related target files**: `scripts/agent/__init__.py`, `tests/agent/test_import_smoke.py`, `docs/00_governance/governance_02_documentation-metadata.md`, `scripts/agent/__main__.py`, `pyproject.toml`, `init.d/llama-agent`
