
## RAG-003: Unresolved usage status of `RegisteredDocument` DTO
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `requires/20260802-192621_require.md`
- **Owner**: Team
- **First Found**: 2026-08-02
- **Target**: `docs/03_rag_04_01_dto-models_data.md`
- **Related**: N/A
- **Summary**: `RegisteredDocument` in `scripts/rag/models_data.py` appears to be unused throughout the codebase.
- **Current Description**: It is defined in `scripts/rag/models_data.py`, but grep shows zero external references. Its role as either a forward-looking placeholder or dead code is unconfirmed.
- **Observed Implementation**: Definition exists in `the RegisteredDocument class`, but no imports or instantiations found in any other `.py` files.
- **Impact**: Potential accumulation of dead code or confusion regarding intended data structures.
- **Recommended Action**: Confirm with design/implementation owner whether this is a required future component or removable dead code.
- **Resolution Notes**: N/A

## RAG-004: Unresolved usage status of `models_config.py` configuration dataclasses
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `requires/20260802-192621_require.md`
- **Owner**: Team
- **First Found**: 2026-08-02
- **Target**: `docs/03_rag_04_04_dto-models_config.md`
- **Related**: N/A
- **Summary**: Several dataclasses in `scripts/rag/models_config.py` appear to be unused.
- **Current Description**: `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, and `PipelineConfig` are defined in `scripts/rag/models_config.py` but do not appear to be imported or instantiated elsewhere. Configuration is currently handled via raw `dict` access from TOML files.
- **Observed Implementation**: Grep confirms no imports or instantiations of these classes outside `scripts/rag/models_config.py`.
- **Impact**: Potential accumulation of dead code or confusion regarding the intended configuration mechanism.
- **Recommended Action**: Confirm with design/implementation owner whether these are intentional placeholders for a future validation layer or removable dead code.
- **Resolution Notes**: N/A
