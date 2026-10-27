# Procedure: Correct stale `sanitize_document` call-site claims in docstrings

## Goal
- Update the two stale boundary claims so they name all sanitized sites after procedures 01/02
  land, keeping every test assertion intact (REQ-006: stale call-site claims corrected; AC-5).

## Scope
- Docstring text only: the module docstring's "Sanitization boundary" paragraph and the
  `test_f04_rag_injection_pattern_sanitization_boundary` docstring. No code or assertion changes.

## Assumptions
- N/A: the corrected wording is dictated by REQ-006 (all query-path chunk-to-prompt sites
  sanitize after this Plan); no open questions for this row.

## Design decisions
- State the invariant positively ("sanitized at each formatting site: `scripts/rag/stages/augment.py`
  chunk formatting, `RagLLM.refine_context`, `_build_rerank_prompt`") instead of a count
  ("exactly once"), so future sites can be added to the list without making the sentence stale again.
- Keep the paragraph's conclusion — the agent layer (`agent/tool_runner.py`) does no sanitization —
  unchanged, because the test's assertion still proves exactly that.

## Alternatives considered
- Deleting the boundary paragraphs: rejected — they are actively consulted as the sanitization
  boundary record (Plan Problem section); removal would erase the justification they carry.

## Implementation
### Target file
`tests/integration/test_rag_turn_integration.py`

### Procedure
1. Rewrite the module docstring sentence "sanitize_document() (rag/utils.py) is called exactly
   once, inside rag/stages/augment.py's chunk-formatting step" to name the three sanitized
   query-path formatting sites after this Plan (see Design decisions for the list).
2. Rewrite the `test_f04` docstring sentence "sanitize_document() belongs to and is only ever
   called from rag/stages/augment.py's chunk-formatting step" with the same three-site wording.

### Details
- Both replacements must keep the surrounding context (inside the RAG MCP server process, before
  the mocked HTTP response is formed) so the test's mocked-response scenario stays coherent.
- "See Also" references stay: the `test_f04` docstring's "(see module docstring)" pointer remains valid.

## Compatibility considerations
- N/A: comments only; no assertion, fixture, or behavior change (Plan row evidence: assertions untouched).

## Security considerations
- N/A: no behavior change; the docstring no longer misstates where sanitization happens (AC-5).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/integration/test_rag_turn_integration.py` — suite green with assertions unchanged.
- Grep check for AC-5: no remaining "only ever called from" / "exclusively" claim about
  `sanitize_document` in this file.

## Completion criteria
- AC-5: neither docstring claims `sanitize_document` is used only by the augment stage.
- All tests in the file pass with byte-identical assertion code.

## Out of Scope
- The test's mocked-response scenario, its assertions, and the agent-layer sanitization question
  (explicitly out of scope, REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two docstring corrections per Implementation > Procedure | Completed | 20261027-201844 | 20261027-201844 | — |
| 2 | Run `uv run pytest tests/integration/test_rag_turn_integration.py` and the AC-5 grep check | Completed | 20261027-201844 | 20261027-201844 | — |

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
- **Requirement ID**: REQ-006 (stale call-site docstring correction, assertions unchanged)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: tests/integration/test_rag_turn_integration.py