## Goal
Replace the config-field prompt mapping with the single-source contract (REQ-009, documentation claim correction).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 51 presents `system_prompt_tool` as a config field mapped to `ctx.conv.system_prompt_content`; after rows 01, 04, 06 and 11 land no config field exists, so the line must name the single source as the stored prompt and the runtime value as the live copy. Hand edit inside the Hot-Reloadable Scope section; the document is not renamed, moved, or a guarded `AUTO-GENERATED` block, and `docs/00_index.md` maps this task scope to the Agent spec.
## Design decisions
- State the source, not the implementation detail; keep the existing section and its wording style. No documentation-structure decision.
## Alternatives considered
- Deleting the line instead of restating it: rejected, the hot-reload scope for prompt content is still an operational fact operators need.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
### Procedure
Rewrite the prompt mapping line as the single-source contract: prompt content is read from the single source through the typed model, and `ctx.conv.system_prompt_content` is the live copy updated only in the reload commit phase. No other line changes, and no removed key is named.

## Compatibility considerations
- Operators must be told where the prompt now lives; `check_docs_consistency.py --domain agent` cross-checks config-key claims against `config/agent.toml`, so commit with row 01.

## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`; then `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py` (the `docs/` gates in `rules/tool-gates.md`).
## Completion criteria
- No statement here presents a config field as the prompt source, and the agent-domain docs checks pass (AC-6).
## Out of Scope
- History-style comment cleanup (`adrchk022`); any other documentation file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Completed | 20261122-182817 | 20261122-182817 | commit with row 01 for the config-key check batch-run; line rewritten as single-source contract; removed key not named |
| 3 | Run the validation sequence (`rules/tool-gates.md`) | Completed | — | 20261122-182820 | the docs checkers listed in Validation plan docs gates pass; consistency warning is pre-existing at baseline (agent_14 line 49), not caused by this change |

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
- **Requirement ID**: `REQ-009` (correct the documentation statements presenting the removed key as a config field)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`