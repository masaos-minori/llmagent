# Add INV-02 regression test and keep original Japanese text on empty normalization

## Priority
Low

## Summary
Add the missing regression test for ADR-014 INV-02 and stop discarding Japanese sentences (original text included) whose normalized form is empty.

## Background
Source: local investigation notes (memo1.md, ISSUE-14), from AGENT-002 and RAG-002. ADR-014 was created to prevent duplicate LlmTurnExecutor ownership; ADR-009's purpose is not to lose original text through normalization.

## Problem
- No regression test checks ADR-014 INV-02 (the Orchestrator creates exactly one LlmTurnExecutor) (AGENT-002).
- A Japanese sentence whose normalized result is empty is dropped together with its original text (RAG-002).

## Reason for Change
- Without the test, refactoring can reintroduce the duplicate-executor defect unnoticed.
- RAG-002 contradicts ADR-009's intent that normalization must not lose original text.

## Implementation Intent
- Pin the invariant with a test and mark it verified in adr-index.
- On normalization failure, keep the original text and exclude nothing from search.

## Target Files or Areas
- `tests/agent/`, `scripts/rag/ingestion/chunk_japanese.py` (current implementation not read)

## Required Changes
- Add a test that Orchestrator construction creates exactly one LlmTurnExecutor and all components share that instance.
- When normalization yields empty, keep the original text in `content` and set `normalized_content` to NULL (the existing COALESCE rule then indexes the original text in FTS).
- Add a test for that behavior.

## Constraints
- Do not change normalization of non-empty results.

## Acceptance Criteria
- Both tests pass in CI; the corresponding adr-index row is updated to Confirmed.

## Testing Expectations
- The two new tests; ruff, mypy, targeted pytest.

## Documentation Impact
Update adr-index verification status for ADR-014 INV-02; remove Known Issues AGENT-002 and RAG-002 when done; update ADR-009/ADR-010 text only if needed.

## Out of Scope
- Other chunking behavior.

## Dependencies
- Run after the workflow fail-closed issue, which changes the Orchestrator.

## Unresolved Questions
- Current implementation of `chunk_japanese.py`.

## AI Implementation Instruction
Add the tests first and confirm the RAG-002 test fails before the fix. Keep the change minimal.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154050
- **Related target files**: `tests/agent/`, `scripts/rag/ingestion/chunk_japanese.py`
