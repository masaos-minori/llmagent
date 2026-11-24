## Goal
Replace the memory tables and JSONL archive in the Session DB document with Episodic Memory in `session.sqlite`, and state the backup, recovery, and schema-mismatch scope (REQ-001, REQ-005).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_09_01_data-layer-session-db.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Keep the document structure; rewrite the inventory row, the retention and ownership subsections, and the Key Constraints JSONL line.
- Backup and recovery are stated once here and linked from the CLI documents.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`

### Procedure
1. Database Responsibility Separation: change the `session.sqlite` responsibility to "Sessions, messages, conversation state, session diagnostics, Episodic Memory".
2. Session Retention Policy: remove the `/memory prune` retention statement; Episodic Memory retention is managed internally and its policy is undecided (SHARED-004); keep the session and diagnostics retention; deleting a session never deletes Episodic Memory.
3. Replace "Memory Table Ownership" with "Episodic Memory Ownership": Episodic Memory events and relations are authoritative data in `session.sqlite`, the Episodic FTS and Vector indexes are derived, no JSONL file exists, Repository Context is not stored in the Session DB, and Episodic Memory is recovered only from a verified SQLite backup.
4. Add "Backup and Recovery Scope": Episodic Memory is part of the Session DB backup and of full Session DB recovery; `/session recover` restores the whole database; Repository Context is reloaded from configured files; a `session.sqlite` that does not match the current schema is archived and recreated (ADR-008 Decision Detail 22, with `/session export` first and Episodic Memory not carried over); whether a destructive recreation is the final policy for Episodic Memory is undecided (SHARED-004).
4a. State that `/clear`, `/undo`, session deletion, and session purge give no user-level Episodic deletion semantics.
5. Key Constraints: remove the JSONL append-only archive bullet.

### Method
- Use the Edit tool; locate with `rg -n -i "memory|jsonl" docs/23_agent/agent_09_01_data-layer-session-db.md`.

### Details
- Remove the provenance paragraph about the old memory table's source session column and the design-judgment paragraph about JSONL replay; Episodic table names are not defined, so none is written.
- Keep the heading "Session Retention Policy".

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
- No memory table, JSONL archive, or `/memory prune` statement remains; Episodic Memory ownership, the backup and recovery scope, and the schema-mismatch rule are stated with SHARED-004 for the undecided parts.

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
- **Requirement ID**: REQ-001 (Episodic Memory ownership), REQ-005 (backup and recovery)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
