## Goal

State the configuration resolution order and the required `rag_db_path` (when search is enabled) in the RagPipeline class documentation (`REQ-007`: document resolution order and required path).

## Scope
**Release unit**: ragrev008-core

- In scope: section 2 (RagPipeline Class) of `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`, intent and boundary only.
- Plan step 3 (documentation); apply after the code procedure.

## Assumptions

- Re-verified at generation time: section 2 says `RagPipeline` is constructed from a flat `module_cfg` (the `RagConfig` Protocol) and defers to the source for attributes and methods; it states neither the resolution order nor that `rag_db_path` is required.
- `docs/21_rag/rag_05_01-configuration-reference.md` documents no key as optional with a `:memory:` default (Plan Step 3 grep), so it is not a target.
- Docs are English (`skills/DESIGN.md` Output language) and follow the Docs content policy: state the contract, not the helper structure or code.

## Design decisions

- Add one short paragraph to section 2: for a dict or object config, the caller's values take precedence, then the explicitly passed `module_cfg`, then built-in defaults; with no config object, the config loader is used and `module_cfg` is only a fallback; resolution never mutates the caller's config.
- State that `rag_db_path` has no default and must be non-empty whenever `use_search` is enabled, otherwise construction fails together with an empty `llm_url` or `embed_url`.

## Alternatives considered

N/A: single-paragraph documentation edit.

## Implementation
### Target file
`docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`

### Procedure
1. Edit section 2, adding the paragraph described under Design decisions after the construction sentence.
2. Keep headings, anchors, front matter, and links unchanged.

### Method
- Plain prose; no code block and no function names beyond `module_cfg`, `use_search`, `rag_db_path`.

### Details
- Do not edit another document; a needed change elsewhere is an additional target file discovery.

## Compatibility considerations

N/A: documentation only; no file is renamed or removed.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- Section 2 states the resolution order, that the caller's config is not mutated, and that `rag_db_path` is required when `use_search` is enabled.
- All five checkers report no findings.

## Out of Scope

- Code, tests, and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit section 2 of the RagPipeline class document | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (document resolution order and required path)
- **Source issue**: issues/20261108-131121_ragrev008_rag-config-defaults-mutation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165441_ragrev008_rag-config-defaults-mutation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-135232
- **Related target files**: `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`
