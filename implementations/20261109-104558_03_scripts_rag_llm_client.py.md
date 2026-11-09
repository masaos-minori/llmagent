## Goal
Make the refiner prompt built by `RagLLM.refine_context` apply the same title handling as the context block: the chunk title (currently interpolated unsanitized) goes through the single-line field sanitizer, while content keeps its existing sanitize-then-truncate handling (`REQ-003`).

## Scope
**Release unit**: ragrev002-core

- In scope: the title line construction in `RagLLM.refine_context` and the companion refiner tests in `tests/rag/test_augment_refiner.py`.
- Depends on the `scripts/rag/utils.py` procedure of this Plan (`seq` 01), which creates the sanitizer used here.

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` also edits `scripts/rag/llm_client.py`, but only `RagLLM.expand_queries`; this procedure edits `refine_context`: compatible, any order. The ragrev001 Plan, which edited `expand_queries` too, is already converted to procedures and is compatible for the same reason.
- `sanitize_field` is created by the `seq` 01 sibling and resolved from it.
- Marker neutralization of content needs no change here: `refine_context` already calls `sanitize_document`, which the `seq` 01 procedure extends.
- The existing helper `_make_capture_llm` in `tests/rag/test_augment_refiner.py` captures the refiner request body, so the companion tests reuse it.

## Design decisions
- Sanitize the title first, then choose the label: an empty or whitespace-only title falls back to the sanitized url, matching the context block.
- Keep the order of content handling (sanitize, then truncate to `per_chunk_chars`); an existing test pins it.

## Alternatives considered
N/A: single-line change inside one method; the Plan's Design section records the decision.

## Implementation
### Target file
`scripts/rag/llm_client.py`

### Procedure
1. Extend the existing `from rag.utils import sanitize_document` line to also import `sanitize_field`.
2. In `RagLLM.refine_context`, build the label from `sanitize_field` of the title (an empty string when absent), falling back to `sanitize_field` of the url, and use it in the `[{i}] {label}` line.
3. Leave the content line, the prompt template, the request body, and every other method unchanged.

### Method
- No new control flow: the title expression becomes a two-step sanitized selection.

### Details
- Do not touch `expand_queries` (ragrev001 and ragrev007 territory) or `cross_encoder_rerank`.
- Comments in English.

### Companion test files
- `tests/rag/test_augment_refiner.py`
  - Procedure: next to the existing refiner prompt sanitization tests, add tests built on `_make_capture_llm`: a chunk whose title holds a line break plus a fake `[2]` header, a marker, and an injection phrase yields a prompt in which that title occupies one line, has no raw marker, and contains `[REMOVED]`; a chunk whose content holds the markers (mixed case, inner whitespace) leaves no raw marker in the prompt; an empty title falls back to the url.
  - Validation: `uv run pytest tests/rag/test_augment_refiner.py -q`; the new tests fail before the change and pass after; the existing refiner tests pass unmodified.

## Compatibility considerations
`refine_context`'s signature, request body, and return value are unchanged. Only the title line differs, and only for titles with line breaks, control characters, markers, or injection phrases; plain titles are byte-identical.

## Security considerations
Chunk titles come from crawled pages and reach an LLM prompt. After this change a title cannot break out of its line or carry a raw marker; the blocklist remains best-effort.

## Rollback considerations
Revert the commit together with the other procedures of release unit ragrev002-core; this file imports a name that the `scripts/rag/utils.py` change creates.

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_llm_client_timeout.py -q`
- `uv run ruff format scripts/rag/llm_client.py tests/rag/test_augment_refiner.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- The refiner prompt contains a neutralized single-line title and no raw marker for forged title or content.
- An empty title falls back to the url; existing refiner tests pass unmodified; ruff, mypy, and lint-imports are clean.

## Out of Scope
- Wrapping the refiner output in boundary markers (Plan UNK-01); `expand_queries`; `cross_encoder_rerank`; the context block (separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Sanitize the chunk title in `RagLLM.refine_context` | Pending | — | — | |
| 2 | Add the companion refiner tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (the refiner applies the same title and content handling)
- **Source issue**: issues/20261108-131004_ragrev002_rag-context-boundary-injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164455_ragrev002_rag-context-boundary-injection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104558
- **Related target files**: `scripts/rag/llm_client.py`, `tests/rag/test_augment_refiner.py`
