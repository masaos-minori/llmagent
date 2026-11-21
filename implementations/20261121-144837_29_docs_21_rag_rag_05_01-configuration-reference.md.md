## Goal

State that the embedding endpoint is owned by the Memory section, not by `AgentConfig.rag` (REQ-001, REQ-003; Documentation Impact).

## Scope
**Release unit**: N/A: documentation update (Phase 5)

## Assumptions
- The RAG pipeline's own key list (`config/rag_pipeline_mcp_server.toml`) is unchanged; only the sentence about `AgentConfig.rag` and the consumer statement are corrected.
- The refiner-keys-in-agent.toml rejection stays documented, because that behaviour is preserved.

## Design decisions
- The sentence that says `AgentConfig.rag` (`RAGConfig`) carries only `embed_url` is replaced by the current specification: the Memory section owns `memory_embed_url` (new), and the Agent-side consumers read it from `ctx.cfg.memory`.
- The list of infrastructure keys that includes `embed_url` (line 52) moves the endpoint out of that list and names the Memory key.

## Alternatives considered
- Keep the RAG page as the place that documents the endpoint: rejected — the document would describe ownership the code no longer has.

## Implementation
### Target file
`docs/21_rag/rag_05_01-configuration-reference.md`
### Procedure
- Remove the `AgentConfig.rag` (`RAGConfig`) statement (line 90) and rewrite it as the Memory-owned key with a link to `docs/23_agent/agent_08_03_configuration-tools-memory.md`.
- Update the key-coverage list (line 52) so `embed_url` is no longer listed as an infrastructure key.
- Update the consumer statement (line 92) to name the Memory-owned key.
### Method
- Wording changes only; the refiner paragraph and the search-stage ownership statements stay.
### Details
- Verified 2026-11-21: the consumers are `scripts/agent/factory.py` and `scripts/agent/services/mcp_health.py`, both changed by Plan rows 3 and 4, so the corrected sentence is only true once those rows land.

## Compatibility considerations
- `tools/check_docs_consistency.py --domain rag` cross-checks config keys against `config/agent.toml`; run it after Plan row 19 lands.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_05_01-configuration-reference.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`

## Completion criteria
- The RAG reference attributes the endpoint to the Memory section and links to the Memory configuration reference; no `RAGConfig` symbol remains in the document.

## Out of Scope
- The Memory reference (Plan row 28), the LLM/RAG agent reference (Plan row 27), the pipeline's own configuration file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation row; the checkers listed in the Validation plan are the verification. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - the rag-domain consistency check must be re-run after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - sibling documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003 (documentation impact)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `docs/21_rag/rag_05_01-configuration-reference.md`
