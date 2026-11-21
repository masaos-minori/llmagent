## Goal

Remove the `RAGConfig` section reference and the cross-field rule that reads the RAG section, so the document no longer describes a class this Plan deletes (REQ-001; Documentation Impact).

## Scope
**Release unit**: N/A: documentation update (Phase 5)

## Assumptions
- Only the parts of this document that the change makes inaccurate are updated; the LLMConfig section stays as it is.
- The Memory key description belongs to `docs/23_agent/agent_08_03_configuration-tools-memory.md` (Plan row 28), not here.

## Design decisions
- The document keeps its scope split (LLM section here, Memory section there); the RAG page keeps only what is still true: the embedding endpoint is a Memory setting documented in the Memory reference.
- Where a paragraph only pointed at `RAGConfig`, the paragraph is removed rather than rewritten to name a class that no longer exists.

## Alternatives considered
- Keep the page as a historical note: rejected — documentation describes the current specification, per the Current-Specification-Only policy.

## Implementation
### Target file
`docs/23_agent/agent_08_02_configuration-llm-rag.md`
### Procedure
- Update the front matter title and the keywords so `RAGConfig` is not named.
- Remove the `RAGConfig` schema paragraph (line 55) and the `RAGConfig` entry in the section list (line 64).
- Replace the cross-field rule "memory_embed_enabled=True → rag.embed_url must not be empty" (line 59) with the `MemoryConfig` validation wording that Plan row 1 defines.
- Point the endpoint description (line 41) at `memory_embed_url` (new) in the Memory section, and keep the pointer to `docs/21_rag/rag_05_01-configuration-reference.md`.
### Method
- Wording changes only; no new section, no new document.
### Details
- Verified 2026-11-21: the statement that `RAGConfig` has no search-stage parameters (line 45) stays true as a statement about the RAG pipeline ownership, but it must be phrased without naming the removed class.

## Compatibility considerations
- `tools/check_docs_consistency.py --domain agent` cross-checks symbol references against `scripts/`; after this row and Plan row 1 land, the symbol is gone from both.
- Front matter `related:` entries must still resolve; run `tools/check_docs_structure.py`.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_02_configuration-llm-rag.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The document names no `RAGConfig` symbol, states the endpoint requirement as a `MemoryConfig` validation, and links to the Memory reference for the key.

## Out of Scope
- The Memory configuration reference (Plan row 28), the RAG configuration reference (Plan row 29), the generated API table (Plan row 31).

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
- **Related target files**: `docs/23_agent/agent_08_02_configuration-llm-rag.md`
