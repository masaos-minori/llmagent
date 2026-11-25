## Goal
Regenerate the Agent API manifest (REQ-011) after the public symbols change; never hand-edit it.
## Scope
**Release unit**: N/A: not part of a release unit
## Assumptions
- Same generator and same compatible overlap with the cliplc006 Plan as the generated reference document; regenerate once more after the second Plan lands.
## Design decisions
- Run the generator, commit its output unchanged.
## Alternatives considered
N/A: generated file.
## Implementation
### Target file
`registry/manifests/agent_api.yaml`
### Procedure
Run the documented generator after all code procedures of this Plan.
### Method
- Run the manifest generator named in `tools/TOOL_DESCRIPTIONS.md`.
- Review the diff for the changed public entries.
### Details
- Do not edit the file by hand.
## Compatibility considerations
N/A: generated.
## Security considerations
N/A: generated.
## Rollback considerations
N/A: regenerate or revert the commit.
## Validation plan
- `uv run python tools/run_validation_gates.py` (contract manifest gate)
## Completion criteria
- The manifest matches the live source.
## Out of Scope
- Hand edits.
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the file per Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — |  |
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
- **Requirement ID**: REQ-011
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `registry/manifests/agent_api.yaml`
