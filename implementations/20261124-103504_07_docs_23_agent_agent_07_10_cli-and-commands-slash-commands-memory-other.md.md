## Goal
Remove the Memory Category contract from the memory-and-other commands document, keep a short retired-command notice and the `/help` entry (REQ-003).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Replace the whole Memory Category section with a short notice; keep the Other Category and the file name.
- The notice mentions `/memory` once so the chapter still satisfies the command-coverage check.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`

### Procedure
1. Front matter title and H1 context: rename the title to "Agent CLI and Commands - Slash Commands: Other and Retired Memory Commands"; update the Purpose sentence.
2. Replace the Memory Category subsection (table, ID, rebuild, and retention paragraphs) with "Retired Memory Commands": the `/memory` command and its subcommands (status, list, delete, pin, unpin, prune, reindex, rebuild) are retired by ADR-008; no compatibility alias is retained; the command is still registered in code until it is removed (SHARED-003); Episodic Memory has no user-facing add, list, search, pin, delete, prune, or rebuild; its diagnostics move to `/stats`, `/context`, `/debug verbose`, and `/reload`.
3. Keep the Other Category (`/help`) unchanged.
4. Responsibility Boundary: replace the Memory bullet with "Memory: none; the commands are retired".
5. Keywords: replace "memory category" with "retired memory commands".

### Method
- Use the Edit tool, or rewrite the section between the Design Intent heading and the Other Category heading.

### Details
- Do not list the subcommand forms or flags again.
- `tests/docs/test_command_docs_sync.py` checks documented command references against the registry; `/memory` stays registered, so the mention is valid.

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
- No `/memory` subcommand contract, JSONL rebuild text, or pin text remains; the notice states retired, not an alias, SHARED-003; `/help` stays.

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
- **Requirement ID**: REQ-003 (retire the Memory Category)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`
