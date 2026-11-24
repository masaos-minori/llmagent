## Goal
Remove the JSONL storage and format and the semantic-only data-model content from the memory gate and data-model document, keeping Episodic search strategies (REQ-001).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_11_02_memory-gate-data-model-search.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Delete the JSONL Format section; reword the data model without the dual type model; keep Search Strategies and Disabled Behavior.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_11_02_memory-gate-data-model-search.md`

### Procedure
1. Operational Notes: replace the `/memory status` bullet with the diagnostics owner (`/stats`, not yet implemented, SHARED-003).
2. Data Model: rename "MemoryEntry (Stored in JSONL + SQLite)" to "MemoryEntry (Stored in SQLite)"; remove the `semantic`/`episodic` typing and `rule`/`conversation`/`decision`/`failure` source typing and the importance threshold wording; keep provenance, context filters (`project`, `repo`, `branch`), content, summary, and tags; state that event categories are undefined (SHARED-004); replace the storage-ownership sentence so it names SQLite as authoritative and FTS and Vector as derived, with no JSONL.
3. MemorySnippet: remove the memory-type prefix and the semantic/episodic source wording.
4. Delete the whole "JSONL Format" section.

### Method
- Use the Edit tool; confirm with `rg -n -i "jsonl" docs/23_agent/agent_11_02_memory-gate-data-model-search.md` that no match remains.

### Details
- Keep the branch-filtering note; it applies to Episodic retrieval.
- The old `MemoryType` and `SourceType` explanations leave with the typing text.

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
- No JSONL storage, format, or `/memory status` text remains; the data model has no dual type model; the search strategies are unchanged.

## Out of Scope
- Any other file, code, configuration, the generated memory reference, and the API manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-104109 | 20261124-104109 | Changed: docs/23_agent/agent_11_02_memory-gate-data-model-search.md |
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
- **Requirement ID**: REQ-001 (data model, JSONL removal)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_11_02_memory-gate-data-model-search.md`