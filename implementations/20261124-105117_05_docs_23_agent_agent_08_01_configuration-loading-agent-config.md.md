## Goal
Mark the memory configuration keys that belong to the retired model in the key table (REQ-002).

## Scope
**Release unit**: terminology-sweep

- Edits only `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`; applied with the other documents of the release unit because the documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it or to `agent_09_01` instead of restating it.
- Where code still implements the retired feature the document cites SHARED-003, and where policy is undecided it cites SHARED-004; no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Only the retired-feature descriptions named in Procedure change; valid names such as the `agent/memory/` path, the `USER MEMORY` snippet framing, and the retrieval mode labels stay.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.

## Design decisions
- Keep the rows because the keys still exist in code; change only the consumer cell.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure
1. Rows `memory_jsonl_dir`, `memory_max_inject_semantic`, `memory_min_importance`, `memory_retention_days`, and `memory_max_pinned`: replace the consumer cell with "retired by ADR-008; removal pending (SHARED-003)".
2. Keep the other memory rows (`use_memory_layer`, `memory_max_inject_episodic`, `memory_dedup_threshold`, `memory_embed_*`, `memory_local_only`, `memory_max_content_chars`).
3. Section intro (line 30 area): leave the Memory section name unchanged.

### Method
- Use the Edit tool on each row; keep the six columns.

### Details
- `memory_max_inject_semantic` is added to the plan's four keys because it belongs to the same dual model (found in Step 3a).
- Do not describe the retired keys' former effect.

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
- The five retired keys are marked retired and cite SHARED-003; other rows are unchanged.

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-104416_adrdoc004_docs-regenerate-cross-validate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-105117
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
