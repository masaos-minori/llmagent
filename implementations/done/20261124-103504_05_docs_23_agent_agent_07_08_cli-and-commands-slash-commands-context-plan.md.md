## Goal
Document the `/context` token-usage components and the context-budget reduction order (REQ-004, REQ-006).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Update the `/context` row and add one short Context Budget subsection; keep `/compact` text unchanged.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`

### Procedure
1. `/context` row: add Repository Context and Episodic Memory token usage beside the system prompt, conversation, tool schemas, and response reserve (not yet implemented, SHARED-003).
2. Add "Context Budget": the final payload is budgeted across the system prompt, Repository Context, Episodic Memory, conversation history, tool schemas, current input, and response reserve; reduction order is low-ranked Episodic Memory, then low-ranked Repository Context sections, then older conversation history; mandatory canonical Repository Context is never silently removed; the failure behavior when mandatory input exceeds the context limit is undefined (SHARED-004).

### Method
- Use the Edit tool; link to the memory overview for the full definition.

### Details
- Do not state a failure behavior; only the no-silent-removal rule.

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
- The `/context` row lists the components; the budget order, the no-silent-removal rule, and the undefined overflow behavior (SHARED-004) are stated.

## Out of Scope
- Any other file, code, configuration, the generated memory reference, and the API manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-104109 | 20261124-104109 | Changed: docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md |
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
- **Requirement ID**: REQ-004 (`/context`), REQ-006 (budget)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`