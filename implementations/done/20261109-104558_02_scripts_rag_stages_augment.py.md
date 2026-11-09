## Goal
Make the context block built by `_format_chunks` unforgeable: take the marker strings from `rag.utils` while keeping `_RAG_BLOCK_START` / `_RAG_BLOCK_END` importable from this module (`REQ-005`), and sanitize title and url in each `[Source: ... | ...]` header through the single-line field sanitizer (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: ragrev002-core

- In scope: the marker definitions and the header construction in `_format_chunks`.
- Depends on the `scripts/rag/utils.py` procedure of this Plan (`seq` 01), which creates the names imported here.

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): this file is not shared with another Frozen Plan.
- The names `RAG_BLOCK_START` and `RAG_BLOCK_END` and the function `sanitize_field` are created by the `seq` 01 sibling and resolved from it.
- No code outside this module and its tests parses the marker strings (`rg` over `scripts/`, `config/`, `tests/`, `tools/`: only `scripts/rag/stages/augment.py`, a docstring in `scripts/rag/pipeline.py`, and tests).
- Existing header tests use plain titles and urls, which the sanitizer leaves unchanged.

## Design decisions
- Keep the private names as aliases of the `rag.utils` constants, so every existing import (`from rag.stages.augment import _RAG_BLOCK_START, _RAG_BLOCK_END`) keeps working.
- Sanitize first, then choose the label: an empty or whitespace-only title falls back to the sanitized url, so the header never shows an empty label.

## Alternatives considered
N/A: the Plan's Design section records the rejected alternatives (escaping only here, extending the blocklist).

## Implementation
### Target file
`scripts/rag/stages/augment.py`

### Procedure
1. Replace the two literal marker assignments with imports of `RAG_BLOCK_START` and `RAG_BLOCK_END` from `rag.utils`, bound to the existing names `_RAG_BLOCK_START` and `_RAG_BLOCK_END`.
2. In `_format_chunks`, compute the sanitized title (from the title, or an empty string when absent) and the sanitized url with `sanitize_field`; the label is the sanitized title when non-empty, otherwise the sanitized url.
3. Build the header as `[Source: {label} | {url}]` with the sanitized values; the content line keeps `sanitize_document`.

### Method
- Keep the empty-list result and the join with the separator unchanged.
- Extend the existing `from rag.utils import sanitize_document` line rather than adding a second import statement.

### Details
- The output format for plain titles and urls must stay byte-identical so the existing assertions in `tests/rag/test_rag_stages.py` and `tests/rag/test_rag_pipeline.py` pass unmodified.
- Update the `_format_chunks` docstring to mention that header fields are sanitized.

## Compatibility considerations
The block format and marker strings are unchanged. Only headers whose title or url contains a marker, a line break, a control character, or an injection phrase differ. `_RAG_BLOCK_START` and `_RAG_BLOCK_END` remain importable from this module. The raw-chunk fallback in `RagPipeline.augment()` calls `_format_chunks` and benefits without change.

## Security considerations
Title and url come from crawled pages and were interpolated verbatim. After this change a title cannot start a new line that mimics a header or a marker, and neither field can carry a raw marker. The phrase blocklist stays best-effort.

## Rollback considerations
Revert the commit together with the other procedures of release unit ragrev002-core; this file imports names that the `scripts/rag/utils.py` change creates.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_rag_stages.py -q` (existing header and marker assertions unmodified)
- `uv run pytest tests/integration/test_rag_turn_integration.py -q`
- `uv run ruff format scripts/rag/stages/augment.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- `_format_chunks` output for forged content, title, or url contains exactly one start and one end marker and single-line headers.
- `from rag.stages.augment import _RAG_BLOCK_START, _RAG_BLOCK_END` still works and the values are unchanged.
- Existing tests pass unmodified; ruff, mypy, and lint-imports are clean.

## Out of Scope
- Changing what the Agent does with the block, renaming the markers, and the refiner and rerank paths (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the marker constants and sanitize the header fields in `_format_chunks` | Completed | 20261109-143405 | 20261109-150615 | Implemented and verified; full suite and diff-cover 100% pass |
| 2 | Add or update tests per Validation plan (written in the `tests/rag/test_rag_pipeline.py` procedure) | Completed | 20261109-143405 | 20261109-150615 | Implemented and verified; full suite and diff-cover 100% pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-143405 | 20261109-150615 | Implemented and verified; full suite and diff-cover 100% pass |

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
- **Requirement ID**: `REQ-001` (markers cannot close or reopen the block), `REQ-002` (single-line title and url), `REQ-005` (marker names stay importable)
- **Source issue**: issues/20261108-131004_ragrev002_rag-context-boundary-injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164455_ragrev002_rag-context-boundary-injection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104558
- **Related target files**: `scripts/rag/stages/augment.py`