# Unify RAG exception hierarchy under RagLayerError base class

## Priority
Medium

## Summary
Unify `RagRerankError`, `RagPipelineError`, and `RagExpansionError` under the `RagLayerError` base class instead of inheriting directly from `RuntimeError`. Create an ADR documenting the rationale for the split if it remains intentional.

## Background
`RagRerankError` and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` and inherit from `RuntimeError` rather than the `RagLayerError` base class used by the other 7 rag-layer exceptions. This was tracked as Known Issue CI-018 in `governance_03_issue-and-uncertainty-management.md`: "The exception hierarchy is not unified under a single base class across the rag layer." Three independent refactoring commits introduced these exceptions:
- `5ac7b757 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` introduced `RagLayerError` and its 6 subclasses
- `2ff62348 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` introduced `RagRerankError`/`RagExpansionError` (`RuntimeError`-based)
- `c0477811 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` introduced `RagPipelineError` (`RuntimeError`-based)

No ADR or design document records a rationale for keeping them separate.

## Problem
Future unification would require touching every `except` clause across `scripts/rag/` that currently catches `RagRerankError`/`RagPipelineError`/`RagExpansionError`/`RuntimeError` by name — a cross-cutting change; until then, a caller could catch the wrong exception type or miss one to a base-class catch.

## Reason for Change
CI-018 has been open since 2026-09-19 without resolution. An inconsistent exception hierarchy makes error handling fragile and increases the risk of catching the wrong exception type.

## Implementation Intent
1. Decide whether to unify `RagRerankError`, `RagPipelineError`, and `RagExpansionError` under `RagLayerError` in a dedicated cross-cutting refactor, OR document the split as an accepted permanent exception via ADR
2. If unifying:
   - Move `RagRerankError` from `scripts/rag/llm_prompts.py` to `scripts/rag/exceptions.py`
   - Move `RagPipelineError` from `scripts/rag/pipeline.py` to `scripts/rag/exceptions.py`
   - Move `RagExpansionError` from `scripts/rag/llm_prompts.py` to `scripts/rag/exceptions.py`
   - Change their base class from `RuntimeError` to `RagLayerError`
   - Update all `except` clauses across `scripts/rag/` that catch these exceptions individually
   - Update imports in all files that reference these exceptions
3. If documenting the split:
   - Create an ADR explaining the rationale for the split
   - Document the decision in each exception's docstring

## Target Files or Areas
- `scripts/rag/exceptions.py`
- `scripts/rag/llm_prompts.py`
- `scripts/rag/pipeline.py`
- All files importing `RagRerankError`, `RagPipelineError`, or `RagExpansionError`

## Required Changes
- Move `RagRerankError`, `RagPipelineError`, `RagExpansionError` definitions to `scripts/rag/exceptions.py`
- Change their base class from `RuntimeError` to `RagLayerError`
- Update all imports across the codebase
- Update all `except` clauses that catch these exceptions individually
- Add/update docstrings with rationale

## Constraints
- Must preserve existing exception behavior (no behavioral changes)
- Must update all callers to avoid breaking exception handling
- Must ensure tests pass after the change

## Acceptance Criteria
- All three exceptions inherit from `RagLayerError`
- All imports are updated to point to `scripts/rag/exceptions.py`
- All `except` clauses that previously caught these exceptions individually still work correctly
- Tests pass after the change
- No regression in exception handling behavior

## Testing Expectations
- Run existing tests: `uv run pytest`
- Verify exception handling works correctly for all affected code paths
- Manual verification: confirm no broken imports remain

## Documentation Impact
If the split is documented via ADR, create a new ADR. Otherwise, update exception docstrings.

## Out of Scope
- Changing the exception hierarchy beyond unifying these three exceptions
- Modifying exception messages or adding new fields
- Changing any other part of the exception handling logic

## Dependencies
- CI-018 Known Issue (source of this work item)
- `scripts/rag/exceptions.py` (current `RagLayerError` definition)

## Unresolved Questions
- Is there a documented rationale for the split that should be preserved?
- Should `RagExpansionError` also be moved (it was introduced alongside `RagRerankError`)?

## AI Implementation Instruction
Read `scripts/rag/exceptions.py`, `scripts/rag/llm_prompts.py`, and `scripts/rag/pipeline.py`. Move `RagRerankError`, `RagPipelineError`, and `RagExpansionError` to `exceptions.py` and change their base class to `RagLayerError`. Update all imports and `except` clauses. Do not change exception behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-232919
- **Related target files**: scripts/rag/exceptions.py, scripts/rag/llm_prompts.py, scripts/rag/pipeline.py
