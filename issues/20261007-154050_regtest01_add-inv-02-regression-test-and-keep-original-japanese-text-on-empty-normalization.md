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

## Adversarial Verification

Verified against current source on 2026-10-09 (issue-to-plan Step 2). Each claim is classified per that step.

| Claim | Location | Classification | Evidence |
|---|---|---|---|
| AGENT-002: no regression test for ADR-014 INV-02 | `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` line 165; `tests/agent/` | Confirmed by repository evidence | ADR-014 line 165 states the regression test "does not exist". No test asserts a single shared `LlmTurnExecutor` instance. Only one instantiation site exists: `scripts/agent/orchestrator.py:119` (`self._llm_executor = LlmTurnExecutor(...)`). |
| RAG-002: a sentence whose normalized result is empty is dropped with its original text | `scripts/rag/ingestion/chunk_japanese.py:54` | Confirmed by repository evidence | `_split_into_ja_sentences` discards the pair when `_normalize_ja_sentence` returns `""`: both original and normalized are lost, not just the normalized form. |
| Fix: set `normalized_content` to NULL so the FTS indexes the original text | `scripts/db/schema_sql.py:65,77,80`; `scripts/db/store_impl.py:147-160` | Partially confirmed - see U-1 | The `chunks_ai`/`chunks_ad`/`chunks_au` triggers use standard SQL `COALESCE(new.normalized_content, new.content)`. `chunk_insert(normalized: str | None = None)` accepts NULL, so NULL falls back to `content`. An empty string `""` does NOT fall back (`COALESCE("", content)` returns `""`), so the fix must propagate NULL, not `""`. |
| Dependency: run after the workflow fail-closed issue, which changes the Orchestrator | Issue "Dependencies" | Needs confirmation | The referenced "workflow fail-closed issue" could not be identified, and it could not be confirmed that it changes `Orchestrator` in a way that affects the INV-02 test. |

### Flaw detected in `plans/20261008-164920_plan.md` (REQ-002)

That plan's implementation step says to change `if normalized:` to `pairs.append((original, normalized))` unconditionally, i.e. append `(original, "")`. That produces an empty string, not NULL, so `COALESCE("", content)` returns `""` and the original text is NOT indexed. The fix must convert an empty normalized result to NULL before `chunk_insert`. The issue's own wording ("set `normalized_content` to NULL") is correct; the plan's step is insufficient.

### Governance note

`plans/20261008-164920_plan.md` matches this issue's title, Goal, Problem and Scope and reads `Freeze status: Frozen`, yet it has no `## Traceability` section and no `- **Source issue**: issues/20261007-154050...` link. The Step 1b content-based duplicate check therefore finds no matching plan despite identical scope. Whether it is this issue's plan is unresolved (see U-2).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154050
- **Related target files**: `tests/agent/`, `scripts/rag/ingestion/chunk_japanese.py`
