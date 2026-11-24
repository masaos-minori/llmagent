## Goal
Rewrite the memory overview for the two-mechanism model, add the Repository Context and Context Budget sections, and remove the Semantic Memory, pin, JSONL, and `/memory` content (REQ-001, REQ-002, REQ-006).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_11_01_memory-overview-and-modes.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Keep the headings Purpose, Responsibility Boundary, Key Constraints, Memory Modes, and Keywords; add three new sections.
- Retrieval modes stay as Episodic Memory retrieval modes (ADR-008 keeps the Episodic FTS and Vector indexes).

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_11_01_memory-overview-and-modes.md`

### Procedure
1. Front matter title and H1: "Memory Layer — Repository Context and Episodic Memory".
2. Design Intent: replace the semantic-versus-episodic paragraph with the two mechanisms; Independence from Conversation Sessions: deleting, purging, loading, exporting, undoing, or compressing a session never modifies Episodic Memory, which has no user-facing deletion; remove `/memory delete` and `/memory prune`.
3. Responsibility Boundary: Episodic Memory Layer owns cross-session reusable work context; Repository Context is a separate read-only source.
4. Key Constraints: remove the importance-threshold and pinned-entry bullets; keep the local-only and snippets-as-data bullets.
5. Memory Modes: introduce them as Episodic Memory retrieval modes; replace the `/memory status` references with the diagnostics owner (`/stats`, not yet implemented, SHARED-003).
6. Implementation Note for `on_session_stop`: remove the JSONL write order and failure handling; persistence is SQLite only; keep embed-skip and duplicate-link statements; remove the manual-write deduplication sentence.
7. Operational Notes: remove the `/memory status` and JSONL rebuild bullets.
8. Add "Repository Context": explicitly configured repository files are the source of truth; read-only; not stored in SQLite or JSONL, not in the Session DB backup, no persistent FTS or Vector index; reloaded atomically at startup or through `/reload`; selected sections injected only for the active turn; authority values such as `canonical` and `observed` and the configuration keys are undefined (SHARED-003).
9. Add "Episodic Memory": the only persistent Agent long-term memory; generated internally from reusable work events, not from generic Q&A; Assistant-generated proposals are not persisted as durable rules; stored in `session.sqlite` with derived FTS and Vector indexes; no user-facing add, list, search, pin, delete, prune, or rebuild; managed by internal retention, consistency, backup, and recovery; recovered only from a verified SQLite backup; event categories and retention are undefined (SHARED-004).
10. Add "Context Budget": the budget order of the `/context` chapter; mandatory canonical Repository Context is never silently removed; overflow failure behavior undefined (SHARED-004).
11. Known Limitations: replace "None" with the SHARED-003 and SHARED-004 citations; Keywords: remove semantic and JSONL terms, add repository context and episodic memory.

### Method
- Edit section by section with the Edit tool; keep anchors linked from `agent_00` and `agent_04_01` (the canonical session and memory boundary).

### Details
- Keep the "Independence from Conversation Sessions" heading.
- Do not name event categories, keys, or authority sources beyond the two values already named in the Plan.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`; `uv run python tools/check_docs_content_policy.py`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- No Semantic Memory, pin, JSONL, or `/memory` operation text remains except one retired-command reference; Repository Context, Episodic Memory, and Context Budget sections exist with SHARED-003 and SHARED-004 citations.

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
- **Requirement ID**: REQ-001, REQ-002 (Repository Context), REQ-006 (context budget)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_11_01_memory-overview-and-modes.md`
