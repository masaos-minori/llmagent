## Goal
Replace the memory table ownership, the JSONL store note, and the `/memory` prune statement with Episodic Memory ownership (REQ-001, REQ-006).

## Scope
**Release unit**: terminology-sweep

- Edits only `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`; applied with the other documents of the release unit because the documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it or to `agent_09_01` instead of restating it.
- Where code still implements the retired feature the document cites SHARED-003, and where policy is undecided it cites SHARED-004; no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Only the retired-feature descriptions named in Procedure change; valid names such as the `agent/memory/` path, the `USER MEMORY` snippet framing, and the retrieval mode labels stay.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.

## Design decisions
- Rewrite the ownership paragraphs; keep the headings.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. DB Ownership: replace "for memory tables, `MemoryStore`" with "for Episodic Memory, `MemoryStore`".
2. Note paragraph: state that the memory layer persists Episodic Memory in `session.sqlite` (events and relations authoritative, FTS and Vector indexes derived), that no JSONL file exists, and that `JsonlMemoryStore` is retired by ADR-008 and removal-pending (SHARED-003); drop the old table list.
3. Logical ownership paragraph: `AgentSession` owns `sessions`, `messages`, and `session_diagnostics`; Episodic Memory has a separate logical owner; session operations never write Episodic data and the reverse; there is no session-scoped Episodic deletion and no user-level deletion API.
4. Replace the `prune_old_memories()` bullet with a statement that it is retired with the `/memory` commands and removal-pending (SHARED-003).

### Method
- Use the Edit tool; locate with `rg -n -i "memor|JSONL" docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`.

### Details
- Table names of the old model are not repeated; the Session DB document defines Episodic ownership.

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
- No memory table list, JSONL store, or `/memory` call statement remains as current behavior.

## Out of Scope
- Any other file, code, configuration, generated references, and manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-110725 | 20261124-110725 | Changed: 23/agent_agent_04_03_state-and-persistence-platform-databases |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261124-110725 | 20261124-110725 | Release unit terminology-sweep eight consistency domains, docs structure/quality/content-policy, ADR checks, known-deviation sync, needs-confirmation inventory, reference and authority drift, DB separation, 75 cited ADR tests and 117 tests pass; preservation findings on the ADR-004 label are intended |

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-104416_adrdoc004_docs-regenerate-cross-validate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-105117
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`