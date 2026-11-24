## Goal
Replace the Memory Status section with the diagnostics owner statement (REQ-001).

## Scope
**Release unit**: terminology-sweep

- Edits only `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`; applied with the other documents of the release unit because the documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it or to `agent_09_01` instead of restating it.
- Where code still implements the retired feature the document cites SHARED-003, and where policy is undecided it cites SHARED-004; no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Only the retired-feature descriptions named in Procedure change; valid names such as the `agent/memory/` path, the `USER MEMORY` snippet framing, and the retrieval mode labels stay.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.

## Design decisions
- Rename the section; keep the counters that the code reports.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

### Procedure
1. Rename the heading "Memory Status (`/memory status`)" to "Memory Diagnostics".
2. Add a first sentence: the `/memory status` command is retired by ADR-008; the diagnostics owner is `/stats`, which is not yet implemented (SHARED-003).
3. Keep the Mode label, Local-only, FTS fallback count, and Embed skip count bullets as the retrieval modes and counters of the Episodic Memory layer; remove the Pinned bullet.

### Method
- Use the Edit tool; check links to the old heading anchor first.

### Details
- The mode labels are retrieval modes and stay.

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
- The section names no `/memory` command as supported and has no pinned count.

## Out of Scope
- Any other file, code, configuration, generated references, and manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | Release unit terminology-sweep |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-104416_adrdoc004_docs-regenerate-cross-validate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-105117
- **Related target files**: `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
