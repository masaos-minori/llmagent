
## Migration Note

This document was populated on 2026-08-06 based on the audit of requirement `requires/20260802-184051_require.md`. All candidate items from the original review's list were re-verified against current source and sibling issue outcomes; every item was confirmed resolved (moved to `issues/done/` by prior commits). No new entries were added from that list. Previous entries (`RAG-001`, `RAG-002`) were removed as they were resolved design decisions, not bugs. The remaining entries below represent genuinely open issues not covered by that resolution pass.

---

## Template Migration Note

**Migration date:** 2026-08-20

**Source format:** Ad hoc bullet fields (entries used informal bullet lists with fields like "Description", "Impact", "Resolution", but lacked standardized field set)

**Destination format:** Common Known Issues Template (17 fields per `00_governance_04_known-issues-template.md`)

**Field-by-field confirmation for RAG-003 and RAG-004:**

| Field | RAG-003 | RAG-004 | Status |
|---|---|---|---|
| ID | RAG-003 | RAG-004 | ✓ |
| Title | Unresolved usage status of `RegisteredDocument` DTO | Unresolved usage status of `models_config.py` configuration dataclasses | ✓ |
| Status | open | open | ✓ |
| Severity | Low | Low | ✓ |
| Area | RAG | RAG | ✓ |
| Type | design-gap | design-gap | ✓ |
| Source | `requires/20260802-192621_require.md` | `requires/20260802-192621_require.md` | ✓ |
| Owner | Team | Team | ✓ |
| First Found | 2026-08-02 | 2026-08-02 | ✓ |
| Target | `docs/03_rag_04_01_dto-models_data.md` | `docs/03_rag_04_04_dto-models_config.md` | ✓ |
| Related | N/A | N/A | ✓ |
| Summary | `RegisteredDocument` in `scripts/rag/models_data.py` appears to be unused throughout the codebase. | Several dataclasses in `scripts/rag/models_config.py` appear to be unused. | ✓ |
| Current Description | It is defined in `scripts/rag/models_data.py`, but grep shows zero external references. Its role as either a forward-looking placeholder or dead code is unconfirmed. | `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, and `PipelineConfig` are defined in `scripts/rag/models_config.py` but do not appear to be imported or instantiated elsewhere. Configuration is currently handled via raw `dict` access from TOML files. | ✓ |
| Observed Implementation | Definition exists in `the RegisteredDocument class`, but no imports or instantiations found in any other `.py` files. | Grep confirms no imports or instantiations of these classes outside `scripts/rag/models_config.py`. | ✓ |
| Impact | Potential accumulation of dead code or confusion regarding intended data structures. | Potential accumulation of dead code or confusion regarding the intended configuration mechanism. | ✓ |
| Recommended Action | Confirm with design/implementation owner whether this is a required future component or removable dead code. | Confirm with design/implementation owner whether these are intentional placeholders for a future validation layer or removable dead code. | ✓ |
| Resolution Notes | N/A | N/A | ✓ |

**Confirmation:** Both RAG-003 and RAG-004 currently satisfy all 17 fields of the common template. No field reformatting was needed; only this declarative note was missing. The existing 2026-08-06 "Migration Note" documents a content-curation audit and is distinct from this format-compliance declaration.

---

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
