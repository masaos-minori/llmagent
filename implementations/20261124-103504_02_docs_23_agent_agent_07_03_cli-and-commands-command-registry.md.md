## Goal
Mark `/memory` as retired in the Built-in Command Index while keeping it indexed, and update the `/stats`, `/context`, `/reload`, and `/debug` descriptions for the diagnostic responsibilities (REQ-003, REQ-004).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- The `/memory` row stays because `check_command_coverage` requires every registered command in this index; its text says retired.
- Row descriptions stay one line each.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure
1. `/memory` row: replace the description with "Retired by ADR-008: not a supported command and not a compatibility alias; still registered until it is removed from code (SHARED-003)".
2. `/stats` row: add Repository Context and Episodic Memory aggregate state (not yet implemented, SHARED-003).
3. `/context` row: add Repository Context and Episodic Memory token usage.
4. `/reload` row: add the Repository Context reload as an atomic snapshot.
5. `/debug` row: add that `/debug verbose` reports source and section selection diagnostics.
6. Leave the `[non-fatal]` notice example unchanged.

### Method
- Use the Edit tool on each table row; keep the leading backticked command cell exactly (`| `/memory` | ... |`) because the checker parses it.

### Details
- The row format is `| `/name` | description |`; do not add columns.
- Do not remove any registered command from the index.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`; `uv run pytest tests/docs/test_command_docs_sync.py -q`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- `/memory` appears as a retired entry with SHARED-003; the four diagnostic rows mention the new responsibilities; the command-coverage check passes.

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
- **Requirement ID**: REQ-003 (retire `/memory`), REQ-004 (diagnostic responsibilities)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
