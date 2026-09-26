# RAG config validation rejects fixtures missing llm_url embed_url

## Priority
Medium

## Summary
15 tests across 4 files fail with `ValueError: RAG config requires non-empty llm_url, embed_url when use_search=True` — a shared test config/fixture builds a RAG config with `use_search=True` but without `llm_url`/`embed_url`, which current validation now rejects.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
Affected tests:
- `tests/agent/commands/test_agent_rag.py::TestAugmentHttpMode` (5 tests)
- `tests/rag/test_pipeline_http_result_kind.py` (4 tests)
- `tests/rag/test_rag_http_mode.py` (4 tests)
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py::TestServiceStart` (2 tests)

All raise the identical `ValueError` at config-construction time, before the test's actual assertions run — strongly suggesting one shared fixture/helper builds an invalid config, or the validation itself became newly strict without the shared fixture being updated.

## Reason for Change
This blocks 15 tests' actual behavior coverage (HTTP-mode RAG augmentation, fallback-to-in-process logic, pipeline service startup) since they never get past config construction. Determine which side is correct: either the shared fixture is stale and must supply `llm_url`/`embed_url`, or the validation is newly over-strict for legitimate test scenarios that don't need those URLs.

## Implementation Intent
Locate the shared RAG config construction path validation lives in (likely a `RagConfig`/similar dataclass or a `use_search` validator) and the shared test fixture/helper each of the 4 files' setup relies on. Confirm whether the validation is new/recently changed. Fix the fixture to supply the required fields if the validation is correct and intentional; otherwise adjust the validation if it incorrectly requires these fields for a valid test scenario.

## Target Files or Areas
- RAG config module (likely under `scripts/rag/` or `scripts/agent/` — confirm exact path defining the `llm_url`/`embed_url` validation)
- Shared test fixture/helper used by the 4 affected test files (confirm exact location, e.g. a `conftest.py` or local helper function)
- `tests/agent/commands/test_agent_rag.py`
- `tests/rag/test_pipeline_http_result_kind.py`
- `tests/rag/test_rag_http_mode.py`
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

## Required Changes
- Identify the exact validation call site and when it was introduced/changed.
- Identify the shared fixture/helper producing the invalid config.
- Apply the minimal correct-side fix (fixture update or validation adjustment).

## Constraints
Do not weaken the `llm_url`/`embed_url` validation if it is protecting a genuine production invariant (`use_search=True` requiring both URLs) — prefer fixing the test fixtures unless investigation shows the validation itself is wrong for these test scenarios.

## Acceptance Criteria
- All 15 listed tests pass.
- The `llm_url`/`embed_url` validation still rejects a genuinely invalid `use_search=True` config with no URLs (i.e. the fix does not silently disable the check).

## Testing Expectations
Run the 4 affected test files; run full suite once after the fix.

## Documentation Impact
N/A: unless the validation's contract changes, in which case document the `use_search` / `llm_url` / `embed_url` requirement (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: exact location of the shared fixture/helper and whether it is genuinely shared across all 4 files or coincidentally similar in each.

## AI Implementation Instruction
Read the RAG config validation source and the setup code of at least two of the four affected files before deciding the fix direction. Prefer fixing the test-side fixture over relaxing production validation unless there is clear evidence the validation itself is incorrect.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/commands/test_agent_rag.py, tests/rag/test_pipeline_http_result_kind.py, tests/rag/test_rag_http_mode.py, tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py
