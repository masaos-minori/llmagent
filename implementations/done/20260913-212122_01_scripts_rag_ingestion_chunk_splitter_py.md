## Goal

Resolve the disconnect between TypedDict interface specifications (`CrawlJsonPayload`, `ChunkJsonPayload`, `ChunkJsonRaw`) and their lack of use as type annotations in `scripts/rag/ingestion/chunk_splitter.py`, per REQ-001 through REQ-006.

## Scope

- In-Scope: Resolving the TypedDict usage mismatch across `scripts/rag/ingestion/chunk_splitter.py` and related files; updating `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` to reflect the resolution
- Out-of-Scope: Changes to other RAG modules not directly involved in this TypedDict mismatch; database schema changes; MCP server modifications

## Assumptions

- The TypedDict declarations in `pipeline_utils.py` were intentionally created as interface specifications, not accidental remnants
- Enforcing TypedDict usage would require adding type annotations to function signatures in `chunk_splitter.py` that currently process raw dicts
- The TypedDict names in the documentation (`CrawlFilePayload`, `ChunkOutputPayload`) are stale and should be corrected to the actual names (`CrawlJsonPayload`, `ChunkJsonPayload`)

## Design decisions

1. **Decision-first approach**: Before implementing any option, determine which is most appropriate based on:
   - Whether TypedDict enforcement would provide meaningful type safety benefits
   - Whether the cost of adding type annotations outweighs the benefit
   - Whether the TypedDicts serve a valid purpose as interface specifications even without enforcement

2. **Evidence-based comparison**: Compare the TypedDict schemas against `ChunkDocument` to assess redundancy (UNK-02). If `ChunkDocument` already provides equivalent type safety, TypedDict enforcement may be unnecessary.

3. **Minimal coupling**: If enforcing TypedDicts, ensure the dependency direction is correct — `chunk_splitter.py` should depend on `pipeline_utils.py`'s TypedDicts, not vice versa.

4. **Documentation accuracy**: Always correct the TypedDict name discrepancy regardless of the chosen approach.

Evidence grounding:
- `pipeline_utils.py:23-51`: `CrawlJsonPayload` (8 required keys) and `ChunkJsonPayload` (13 required keys) — strict TypedDicts with no optional fields
- `pipeline_utils.py:236-256`: `ChunkJsonRaw` — relaxed TypedDict with `NotRequired` fields for flexibility
- `chunk_splitter.py:25-29`: imports `read_crawl_json` from pipeline_utils but doesn't use TypedDicts directly
- `chunk_splitter.py:30`: uses `ChunkDocument` from models_data for internal processing
- `models_data.py`: `ChunkDocument` dataclass likely provides equivalent type safety to `ChunkJsonPayload`

## Alternatives considered

- **Enforce TypedDict**: Add type annotations to chunk_splitter.py referencing TypedDicts from pipeline_utils.py. Requires mypy validation. Risk: could introduce circular dependencies.
- **Remove declarations**: Delete TypedDict declarations from pipeline_utils.py and update all references. Risk: could break external consumers.
- **Document as interface spec**: Add clear documentation explaining TypedDicts' role as interface specifications. Lowest risk, preserves design intent without runtime enforcement.

## Implementation
### Target files
- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/ingestion/pipeline_utils.py`
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Decision Analysis — compare TypedDict schemas against ChunkDocument, search for TypedDict consumers, review git history
2. Core Implementation — choose one path (enforce TypedDict / remove declarations / document as interface spec)
3. Documentation Correction — correct TypedDict name discrepancy and reflect chosen resolution
4. Verification — confirm the chosen approach accurately resolves the mismatch

### Method
Phase-gated implementation: Phase 1 determines the approach, Phase 2 implements it, Phase 3 updates documentation, Phase 4 verifies.

### Details
1. **Phase 1: Decision Analysis — Determine which approach to take**
   a. Compare TypedDict schemas (`CrawlJsonPayload`, `ChunkJsonPayload`, `ChunkJsonRaw`) against `ChunkDocument` dataclass fields to assess redundancy
      - Read `scripts/rag/models_data.py` to verify `ChunkDocument` dataclass fields
      - Compare field definitions: CrawlJsonPayload (8 keys), ChunkJsonPayload (13 keys), ChunkJsonRaw (relaxed with NotRequired)
   
   b. Search for all TypedDict consumers across the repository to assess breaking risk
      - Run: `grep -r "CrawlJsonPayload\|ChunkJsonPayload\|ChunkJsonRaw" --include="*.py"`
      - Check for external consumers outside this scope
   
   c. Review git history of TypedDict additions vs. ChunkDocument changes if available
      - Run: `git log --follow --oneline scripts/rag/ingestion/pipeline_utils.py`
      - Run: `git log --follow --oneline scripts/rag/models_data.py`
      - Assess whether TypedDicts evolved independently of ChunkDocument
   
   d. Make decision on which approach to take (REQ-001):
      - **Option 1 — Enforce TypedDict**: Choose if TypedDicts provide meaningful type safety beyond ChunkDocument AND no circular dependency risks exist
      - **Option 2 — Remove declarations**: Choose if TypedDicts are redundant with ChunkDocument AND no external consumers rely on them
      - **Option 3 — Document as interface spec**: Choose if TypedDicts serve a valid purpose as interface specifications even without enforcement

2. **Phase 2: Core Implementation — Implement the chosen path**
   
   **Option 1 — Enforce TypedDict:**
   a. Add type annotations to chunk_splitter.py functions referencing TypedDicts from pipeline_utils.py:
      ```python
      # Add import at top of chunk_splitter.py:
      from rag.ingestion.pipeline_utils import CrawlJsonPayload, ChunkJsonPayload
      
      # Update function signatures where TypedDicts apply:
      def some_function(data: dict[str, object]) -> SomeResult:
          ...
      
      # Becomes:
      def some_function(data: CrawlJsonPayload) -> SomeResult:
          ...
      ```
   
   b. Run mypy to validate type annotations:
      ```bash
      uv run mypy scripts/rag/ingestion/chunk_splitter.py
      ```
      Expected outcome: Clean type checking results

   **Option 2 — Remove declarations:**
   a. Delete TypedDict declarations from pipeline_utils.py:
      - Remove `CrawlJsonPayload` definition (lines 23-51)
      - Remove `ChunkJsonPayload` definition (lines 23-51)
      - Remove `ChunkJsonRaw` definition (line 236)
   
   b. Update all TypedDict references to use `dict[str, Any]` instead:
      - Find all usages of `CrawlJsonPayload`, `ChunkJsonPayload`, `ChunkJsonRaw`
      - Replace with `dict[str, Any]` or appropriate alternative types
   
   c. Verify no broken imports remain:
      ```bash
      uv run python -c "from rag.ingestion.pipeline_utils import *"
      ```
      Expected outcome: No import errors

   **Option 3 — Document as interface spec:**
   a. Add clear documentation explaining TypedDicts' role as interface specifications:
      ```python
      # Add docstring comment above each TypedDict declaration:
      """
      Interface specification for crawl/chunk JSON payloads.
      This TypedDict defines the expected structure but is NOT enforced at runtime.
      Runtime enforcement is handled by ChunkDocument dataclass in models_data.py.
      Use this as a reference for contract, not as a type annotation requirement.
      """
      class CrawlJsonPayload(TypedDict):
          ...
      ```
   
   b. Add cross-reference to ChunkDocument as the runtime-enforced alternative:
      - Note in the TypedDict docstrings that `ChunkDocument` provides equivalent type safety at runtime

3. **Phase 3: Documentation Correction**
   a. Correct TypedDict name discrepancy in `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`:
      - Replace `CrawlFilePayload` → `CrawlJsonPayload`
      - Replace `ChunkOutputPayload` → `ChunkJsonPayload`
   
   b. Reflect the chosen resolution in the documentation:
      - If Option 1: Document that TypedDicts are now enforced via type annotations
      - If Option 2: Document that TypedDicts have been removed and replaced with `dict[str, Any]`
      - If Option 3: Document that TypedDicts serve as interface specifications only

4. **Phase 4: Verification**
   a. Confirm the chosen approach accurately resolves the mismatch (all requirements)
   b. Confirm no unintended modifications were made to other files

## Compatibility considerations

- If enforcing TypedDicts: Could introduce circular dependencies between `chunk_splitter.py` and `pipeline_utils.py` — mitigated by verifying import direction before adding TypedDict imports
- If removing TypedDicts: Could break external consumers — mitigated by thorough search for all TypedDict consumers before deletion; keep backward-compatible aliases if needed
- If documenting as interface spec: Does not resolve the underlying mismatch but makes the design intent explicit — acceptable trade-off if enforcement is deemed unnecessary
- The documentation file correction (REQ-005) is independent of the chosen approach and must always be performed

## Security considerations

N/A: Type annotation/documentation change only, no security impact.

## Rollback considerations

- Option 1: Revert TypedDict imports and type annotations; restore original function signatures
- Option 2: Restore TypedDict declarations from git history; revert `dict[str, Any]` replacements
- Option 3: Remove added docstring comments; restore original TypedDict names in documentation

No data migration or state rollback needed for any option.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/ingestion/chunk_splitter.py | Type validation (if Option 1) | uv run mypy scripts/rag/ingestion/chunk_splitter.py | Clean type checking results |
| scripts/rag/ingestion/pipeline_utils.py | Import validation (if Option 2) | uv run python -c "from rag.ingestion.pipeline_utils import *" | No import errors |
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual review | Read target files + compare | Documentation matches actual behavior |

## Completion criteria

- [ ] A clear decision has been made on which approach to take
- [ ] If enforcing TypedDict: type annotations added and mypy passes
- [ ] If removing declarations: all references updated and no broken imports remain
- [ ] If documenting as interface spec: documentation added and verified accurate
- [ ] Documentation file corrected to use actual TypedDict names
- [ ] No unintended side effects from the chosen approach

## Out of scope

- Modifying `scripts/rag/models_data.py` (reference file only)
- Modifying `scripts/rag/ingestion/crawler.py` (reference file only)
- Modifying `scripts/rag/ingestion/ingester.py` (reference file only)
- Modifying `scripts/rag/ingestion/file_routing.py` (reference file only)
- Modifying `scripts/rag/ingestion/crawl_persister.py` (reference file only)
- Changes to other RAG modules not directly involved in this TypedDict mismatch
- Database schema changes
- MCP server modifications

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Compare TypedDict schemas against ChunkDocument | Completed | — | — | Assess redundancy |
| 2 | Search for TypedDict consumers | Completed | — | — | grep -r CrawlJsonPayload ChunkJsonPayload ChunkJsonRaw |
| 3 | Review git history of TypedDict vs ChunkDocument | Completed | — | — | git log --follow |
| 4 | Make decision on approach | Completed | — | — | Option 1/2/3 |
| 5 | Implement chosen approach | Completed | — | — | See Phase 2 details |
| 6 | Correct TypedDict name discrepancy in docs | Completed | — | — | CrawlFilePayload→CrawlJsonPayload, ChunkOutputPayload→ChunkJsonPayload |
| 7 | Validate (mypy/import/manual review) | Completed | — | — | Per Validation plan |

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
- **Requirement ID**: REQ-001 through REQ-006 — resolve RAG ChunkSplitter TypedDict usage mismatch
- **Source issue**: issues/20260913-183048_missing_chunksplitter_typedict_usage_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-195011_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-212122
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py, scripts/rag/ingestion/pipeline_utils.py, docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
