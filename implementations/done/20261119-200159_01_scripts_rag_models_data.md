## Goal

Add the chunk-settings value object that aggregates the seven chunking settings currently spread across `ChunkSplitter.__init__`, so the chunk mixins receive one collaborator instead of reading undeclared host attributes (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The value object belongs in `scripts/rag/models_data.py` alongside the other frozen dataclasses (`ChunkDocument`, `ChunkRecord`, `PreparedChunk`, …) — the domain-data home already confirmed by an inventory scan.
- The object holds exactly seven settings: `min_chunk`, `max_chunk`, `chunk_overlap`, `md_snippet_max_chars`, `md_index_enable`, `en_stopwords` (frozenset[str]), `ja_stop_pos` (frozenset[str]) — the seven values assigned inline in `ChunkSplitter.__init__` (lines 111–131).
- `ChunkSplitter.__init__` validates these once (existing range checks, lines 96–130) and then constructs the value object; validation stays in `__init__`, not in the value object.
- The value object is a single importable type (data class or `TypedDict`); `UNK-02` (exact module) is resolved here to `models_data.py` per the plan's assumption.
- Cross-plan overlap: `chunk_splitter.py` is also targeted by `ragcrv007` (sequencing dependency, verified compatible — different concerns).

## Design decisions
- Use a frozen data class (`@dataclass(frozen=True)`) to match the surrounding `models_data.py` convention and give immutability for free; fields carry the exact types used in `__init__` (`int`, `bool`, `frozenset[str]`).
- Name it `ChunkSettings`; expose the seven fields as public attributes and nothing else, so the mixins read `settings.min_chunk` etc. instead of `self._min_chunk`.

## Alternatives considered
- `TypedDict` vs data class: the settings mix scalar and `frozenset` fields and are constructed once and read positionally, so a frozen data class matches the module's existing frozen-dataclass style better and gives attribute access and equality for tests.
- A dedicated new module vs `models_data.py`: the plan constrains only a single importable value object; `models_data.py` is the established domain-data home, so no new module.

## Implementation
### Target file
`scripts/rag/models_data.py`

### Procedure
1. Add a frozen data class `ChunkSettings` after the other data classes holding the seven fields with their `__init__` types.
2. Do not reference it from `chunk_splitter.py` yet — row 2 (`chunk_splitter.py`) consumes it; keep this row a pure definition so the two edits stay decoupled.

### Method
- Mirror the existing `@dataclass(frozen=True)` pattern (field annotations, no body) so the diff matches repo style.

### Details
- Keep field order stable and documented so the constructor call in `chunk_splitter.py` reads positionally or by keyword consistently.

## Compatibility considerations
- Pure addition; no existing symbol changes, so no caller impact.

## Security considerations
N/A: plain configuration value object.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `uv run mypy --no-namespace-packages scripts/rag/models_data.py` clean.
- Import: `ChunkSettings` imports from `rag.models_data` without side effects.

## Completion criteria
- `ChunkSettings` exists in `models_data.py` with the seven fields and correct types; importable from `rag.models_data`.

## Out of Scope
- Constructing the object in `chunk_splitter.py` — covered by row 2.
- Tokenizer `Protocol` — covered by row 4.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | |

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
- **Requirement ID**: `REQ-001` (chunk-settings value object holding the seven settings)
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-190454_ragcrv006_chunk-mixin-state-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-200159
- **Related target files**: `scripts/rag/models_data.py`
