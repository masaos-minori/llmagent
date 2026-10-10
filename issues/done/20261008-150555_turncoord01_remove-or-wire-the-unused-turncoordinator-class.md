# Remove or wire the unused TurnCoordinator class

## Priority
Low

## Summary
The `TurnCoordinator` class and its module are exported from the agent package but are never constructed or used; decide whether to delete them or wire them into the turn flow, and fix the documents that still describe them as active.

## Background
Found while removing the Orchestrator's fallback mode and compatibility wrappers. The Orchestrator docstring used to list the coordinator as a composed component, but a search of the production code and the tests finds no construction of it. The real owner of the behavior it documents (system-prompt synchronization) is the conversation state manager.

## Problem
- `TurnCoordinator` is defined in its own module and re-exported from the package, with no production caller and no test.
- A comment in the workflow adapter says planning is done by the coordinator's turn-start method, which nothing calls.
- The generated agent API reference lists it as a component, and an ADR names it among the extracted concern classes, so readers may believe it is active.

## Reason for Change
Dead code that looks active misleads maintainers and conflicts with the repository's policy against leftover compatibility layers.

## Implementation Intent
- Confirm there is no caller (including dynamic use), then delete the class, its module, the package export, and the stale comment; update the documents that list it. If a caller is found, document and test it instead.

## Target Files or Areas
- `scripts/agent/turnd_coordinator.py`
- `scripts/agent/__init__.py`
- `scripts/agent/workflow_engine_adapter.py` (one comment)
- `docs/23_agent/agent_13_reference-api-generated.md` (regenerated reference) and `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` (text listing the class)

## Required Changes
- Search for any use (imports, string references, dynamic lookup) and record the result.
- Remove the module, the export, and the comment; regenerate or edit the reference document; adjust the ADR text.
- Run lint, type, import-boundary, and the agent tests.

## Constraints
- No backward-compatibility shims; do not change other agent components.
- The ADR text change must not alter its decisions.

## Acceptance Criteria
- No reference to the coordinator remains in code, tests, or documents, or it is documented and covered by a test.
- The agent test suite and the documentation checkers pass.

## Testing Expectations
Run ruff, mypy, the import-boundary check, the agent tests, and the documentation checkers; the full suite once.

## Documentation Impact
Yes: the generated API reference and the ADR-014 text that lists the class; use the generator if the reference is generated.

## Out of Scope
- Redesigning the Orchestrator or the workflow adapter.

## Dependencies
- N/A: none.

## Unresolved Questions
- Whether any external tool or plugin imports the class from the package (unknown; the repository shows none).

## AI Implementation Instruction
Search before deleting and report any caller instead of removing it. Keep the change to the listed files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-143632_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-150555
- **Related target files**: `scripts/agent/turnd_coordinator.py`, `scripts/agent/__init__.py`
