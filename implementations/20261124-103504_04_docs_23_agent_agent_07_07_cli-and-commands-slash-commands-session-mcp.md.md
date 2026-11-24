## Goal
Update the session and MCP commands document: the Episodic Memory scope of `/session recover`, the absence of user-level Episodic deletion semantics, and the `/stats` and `/reload` rows (REQ-004, REQ-005).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Rewrite the Session and Memory Separation section in place so its anchor stays; link the recovery statement to the Session DB document instead of repeating it.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure
1. `/clear` paragraph and `/undo` paragraph: replace "long-term Memory" statements with Episodic Memory wording: neither command deletes or modifies Episodic Memory, and neither gives user-level Episodic deletion semantics.
2. `/session recover` row: state that it restores the whole Session DB from a verified backup, so Episodic Memory returns with it, and that Repository Context is reloaded from the configured files and is not restored from the backup.
3. Session and Memory Separation: rewrite: `/session load`, `/session delete`, `/session export`, and `/session purge` operate on conversation sessions and messages only and never delete or restore Episodic Memory; Episodic Memory has no user-facing delete, prune, or rebuild; Episodic Memory is restored only with a full Session DB restore (see the Session DB document).
4. `/stats` row: add Repository Context and Episodic Memory aggregate state (not yet implemented, SHARED-003); diagnostics never expose individual Episodic contents, IDs, secrets, or personal information.
5. `/reload` row: add the Repository Context atomic reload (link to the hot-reload document).

### Method
- Use the Edit tool; locate with `rg -n -i "memory|/stats|/reload|recover" docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`.

### Details
- Keep the heading text "Session and Memory Separation" (other documents link to the Session and memory boundary).
- `/undo` trims the in-memory history and the database; its wording about "Memory and the DB" refers to history in memory, so change only the long-term memory sentence.

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
- No long-term memory deletion or restore semantics for users remain; `/session recover`, `/stats`, `/reload`, and the separation section state the new scope; links resolve.

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
- **Requirement ID**: REQ-004 (`/stats`, `/reload`), REQ-005 (recovery and separation)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
