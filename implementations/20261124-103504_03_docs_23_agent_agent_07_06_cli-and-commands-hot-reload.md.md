## Goal
Document Repository Context reload under `/reload` with atomic behavior (REQ-004).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- One new subsection after Apply Atomicity; the existing configuration atomicity text stays unchanged.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`

### Procedure
1. Add "Repository Context Reload" after the Apply Atomicity subsection: `/reload` also reloads the configured repository files; all sources are loaded into a candidate snapshot; a validation failure rejects the complete reload and preserves the active snapshot; the new snapshot applies only to subsequent turns; Repository Context is never persisted.
2. State that the Repository Context loader and its `/reload` behavior are not implemented yet (SHARED-003) and that its source list and keys are undefined.

### Method
- Use the Edit tool; follow the heading level and bullet style of Apply Atomicity.

### Details
- The open issue cliplc005 also edits this document for configuration staging; keep this subsection independent of it.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The atomic candidate-snapshot behavior, the preserved active snapshot, and the apply-to-subsequent-turns rule are documented with the SHARED-003 citation.

## Out of Scope
- Any other file, code, configuration, the generated memory reference, and the API manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | Release unit agent-memory-docs |

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
- **Requirement ID**: REQ-004 (Repository Context reload)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`
