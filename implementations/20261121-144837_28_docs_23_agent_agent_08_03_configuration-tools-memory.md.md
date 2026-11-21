## Goal

Document `memory_embed_url` as a Memory-owned key and state the endpoint requirement as a `MemoryConfig` validation (REQ-001; Documentation Impact).

## Scope
**Release unit**: N/A: documentation update (Phase 5)

## Assumptions
- Only the Memory parts of this document change; the ToolConfig sections stay.
- The mode table driven by `use_memory_layer` and `memory_embed_enabled` is unchanged: the behaviour is the same, only the key location and the validation owner change.

## Design decisions
- The key list gains `memory_embed_url` (new) with the enabled-gated requirement written as a `MemoryConfig` rule, matching Plan row 1.
- The cross-field wording "memory_embed_enabled=True → rag.embed_url must not be empty" (line 88) is removed, because after the move there is no cross-section read.

## Alternatives considered
- Keep the wording as a cross-section rule: rejected — it describes a validation that no longer exists.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`
### Procedure
- Add `memory_embed_url` (new) to the Memory key list and to the Canonical Source line's owning section.
- Update the `memory_local_only` line (line 69) to name `memory_embed_url` instead of `embed_url`.
- Replace the cross-field rule (line 88) with the `MemoryConfig` validation statement.
### Method
- Wording and key-list updates only; no new section.
### Details
- Verified 2026-11-21: the local-address rejection is enforced in `scripts/agent/memory/embedding_client.py`, so the document must keep pointing at that runtime check while naming the Memory-owned key.

## Compatibility considerations
- `tools/check_docs_consistency.py --domain agent` cross-checks config keys against `config/agent.toml`; the key must exist in the file (Plan row 19) before this row is valid.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The Memory reference lists `memory_embed_url` as an owned key, describes the enabled-gated requirement as a Memory validation, and no longer points at the RAG section.

## Out of Scope
- The LLM/RAG reference (Plan row 27), the RAG configuration reference (Plan row 29), the runtime client behaviour (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation row; the checkers listed in the Validation plan are the verification. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - the agent-domain consistency check must be re-run after that Issue lands |
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
- **Requirement ID**: REQ-001 (documentation impact)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
