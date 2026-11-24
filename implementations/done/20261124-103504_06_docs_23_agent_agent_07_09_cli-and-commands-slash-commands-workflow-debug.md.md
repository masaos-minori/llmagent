## Goal
Document the `/debug verbose` source, section selection, exclusion, fallback, and budget diagnostics (REQ-004).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Extend the `/debug verbose` row; keep the other `/debug` rows unchanged.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`

### Procedure
1. `/debug verbose` row: add that it also reports Repository Context source and section selection, exclusion, fallback, and budget diagnostics (not yet implemented, SHARED-003).
2. Add one sentence that diagnostics expose aggregate state only and never individual Episodic contents, IDs, secrets, or personal information.

### Method
- Use the Edit tool on the table row and add the sentence below the table.

### Details
- Do not invent diagnostic field names or output formats.

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
- The `/debug verbose` row states the diagnostics and the privacy rule with the SHARED-003 citation.

## Out of Scope
- Any other file, code, configuration, the generated memory reference, and the API manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-104109 | 20261124-104109 | Changed: docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261124-104109 | 20261124-104109 | Release unit agent-memory-docs agent docs consistency (command and usage coverage), structure, quality, content policy, known-deviation sync, needs-confirmation inventory, reference drift checks and 30 tests pass; preservation findings are intended title changes |

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
- **Requirement ID**: REQ-004 (`/debug verbose`)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`