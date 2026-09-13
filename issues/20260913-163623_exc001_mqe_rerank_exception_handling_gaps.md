# Fix exception handling gaps in MQE and Rerank stages

## Priority
High

## Summary
Add broad exception catching in MqeStage.run() and RerankStage.run() to prevent non-critical failures from crashing the entire RAG pipeline. Currently only RagExpansionError and RagRerankError are caught; other exceptions propagate up and abort the pipeline.

## Background
The RAG pipeline has a fallback chain: HTTP augment -> semantic cache -> in-process pipeline -> refiner -> raw chunks. Each stage should fail gracefully and allow fallback to subsequent stages. The HttpAugment and Refiner stages already implement this pattern — they catch all relevant exceptions and return None/fallback results. However, MQE and Rerank stages do not.

## Problem
When MQE or Rerank encounters a non-critical error (e.g., TypeError, ValueError, unexpected API response format), the exception propagates up through the pipeline lifecycle, causing the entire augment() call to fail. This means a transient LLM API issue or malformed response causes complete retrieval failure instead of falling back to raw chunks.

## Reason for Change
The current behavior violates the pipeline's design intent: each stage should be independently fault-tolerant. The HttpAugment and Refiner stages demonstrate the correct pattern — catch errors, log warnings, and fall back. MQE and Rerank should follow the same pattern.

## Implementation Intent
Apply the same exception-handling pattern used in HttpAugment.run() and AugmentRefiner.run_refiner():
1. In MqeStage.run(), wrap the _run_mqe() call in a try/except that catches all exceptions (not just RagExpansionError), logs a warning, sets ctx._fallback_reason = "mqe_exception", and falls back to the original query.
2. In RerankStage.run(), apply the same pattern for RagRerankError — catch all exceptions, not just RagRerankError.
3. Ensure the fallback logic preserves the existing ctx.queries / ctx.reranked assignment semantics.

## Target Files or Areas
- scripts/rag/stages/mqe.py
- scripts/rag/stages/rerank.py

## Required Changes
- MqeStage.run(): change `except RagExpansionError:` to `except Exception as e:` with appropriate logging and fallback
- RerankStage.run(): change `except RagRerankError:` to `except Exception as e:` with appropriate logging and fallback
- Update get_status() methods to recognize the new fallback conditions consistently

## Constraints
- Must preserve existing fallback behavior: MQE fallback returns [original_query], Rerank fallback applies _rerank_fallback()
- Must not suppress critical errors (e.g., KeyboardInterrupt, SystemExit)
- Logging must remain at WARNING level for transient failures

## Acceptance Criteria
- MQE stage fails gracefully on any exception (HTTP error, parse error, connection timeout) and falls back to original query
- Rerank stage fails gracefully on any exception and falls back to RRF-ranked results
- Existing RagExpansionError and RagRerankError handling remains unchanged
- Stage result status correctly reflects "failure" or "fallback" for both cases
- All existing tests pass after changes

## Testing Expectations
- Add unit tests for MqeStage.run() with non-RagExpansionError exceptions (TypeError, ValueError, httpx.RequestError)
- Add unit tests for RerankStage.run() with non-RagRerankError exceptions
- Verify fallback behavior produces correct ctx.queries / ctx.reranked values
- Run existing test suite: pytest tests/rag/test_rag_stages.py

## Documentation Impact
Update docstrings in MqeStage.run() and RerankStage.run() to document the broader exception handling behavior.

## Out of Scope
- Changes to the exception hierarchy (no new exception types needed)
- Changes to the pipeline lifecycle or stage ordering
- Changes to HttpAugment or Refiner exception handling (already correct)

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
1. Read scripts/rag/stages/mqe.py and scripts/rag/stages/rerank.py
2. In MqeStage.run(): replace `except RagExpansionError:` with `except Exception as e:` — keep the logger.info line, add `logger.warning("MQE failed: %s", e)` before the fallback assignment
3. In RerankStage.run(): replace `except RagRerankError:` with `except Exception as e:` — keep the logger.info line, add `logger.warning("Rerank failed: %s", e)` before the fallback assignment
4. Do NOT change the fallback assignments (ctx.queries = [ctx.query] / ctx.reranked = _rerank_fallback(...))
5. Run pytest tests/rag/test_rag_stages.py to verify existing tests still pass
6. Add new test cases for non-specific exceptions in TestMqeStage.test_run_non_expansion_error and TestRerankStage.test_run_non_rerank_error

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/stages/mqe.py, scripts/rag/stages/rerank.py
