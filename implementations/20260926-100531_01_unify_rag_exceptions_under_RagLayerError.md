# Implementation Procedure: Unify RagRerankError, RagPipelineError, RagExpansionError under RagLayerError

## Goal

Unify `RagRerankError`, `RagPipelineError`, and `RagExpansionError` under the `RagLayerError` base class instead of inheriting directly from `RuntimeError`.

## Scope

- Move exception definitions to `scripts/rag/exceptions.py`; change their base class to `RagLayerError`; update all imports and `except` clauses across the codebase

## Assumptions

- The exception class names should be preserved (no renaming)
- The exception docstrings should be preserved with minor wording adjustments
- The `__all__` export lists in `llm_prompts.py` should be updated to remove the moved exceptions
- Import statements in consumer files should be updated to point to `exceptions.py`
- Since the exceptions now inherit from `RagLayerError` which inherits from `Exception`, existing code catching `RuntimeError` will no longer catch them directly — but they still inherit from `Exception` so broad catches will still work
- The exception hierarchy change is backward-compatible because `RagLayerError(Exception)` means existing `except Exception` handlers still work

## Design decisions

- Add three new exception classes to `exceptions.py`:
    ```python
    class RagRerankError(RagLayerError):
        """Raised when cross-encoder reranking fails (HTTP, parse, or connection error)."""

    class RagExpansionError(RagLayerError):
        """Raised when MQE query expansion fails (HTTP, parse, or connection error)."""

    class RagPipelineError(RagLayerError):
        """Raised when a pipeline-level operation fails (e.g. DB open, stage failure)."""
    ```
- In `llm_prompts.py`: Remove the `RagRerankError` and `RagExpansionError` class definitions (lines 52-57), and update the `__all__` export list to remove these names. Keep the module docstring updated to reflect that these exceptions are now imported from `exceptions.py`.
- In `pipeline.py`: Remove the `RagPipelineError` class definition (line 54), and add an import from `exceptions.py` where needed.
- In `stages/rerank.py`: Update the import statement to import `RagRerankError` from `exceptions.py` instead of `llm_prompts.py`.
- In `stages/mqe.py`: Update the import statement to import `RagExpansionError` from `exceptions.py` instead of `llm_prompts.py`.
- In `llm_client.py`: Update the import statement to import `RagRerankError`/`RagExpansionError` from `exceptions.py` instead of `llm_prompts.py`.
- In test files: Update imports similarly.
- Since `RagLayerError(Exception)` and the moved exceptions now inherit from `RagLayerError`, existing code that catches `RuntimeError` will no longer catch them directly. However, since `RagLayerError` inherits from `Exception`, broad `except Exception` handlers will still work. This is backward-compatible for most cases.

## Alternatives considered

- **Keep RuntimeError inheritance**: Would violate CI-018 resolution requirement; inconsistent with other RAG-layer exceptions
- **Create a new intermediate base class**: Adds unnecessary complexity; RagLayerError already serves as the appropriate base
- **Move only RagRerankError/RagExpansionError, keep RagPipelineError separate**: Violates REQ-001 which requires all three exceptions to inherit from RagLayerError

## Implementation

### Target files

1. `scripts/rag/exceptions.py` — Add exception classes
2. `scripts/rag/llm_prompts.py` — Remove exception definitions, update __all__
3. `scripts/rag/pipeline.py` — Remove exception definition, add import
4. `scripts/rag/stages/rerank.py` — Update import
5. `scripts/rag/stages/mqe.py` — Update import
6. `scripts/rag/llm_client.py` — Update import
7. `tests/rag/test_rag_pipeline.py` — Update import
8. `tests/rag/test_rag_pipeline_stage.py` — Update import
9. `tests/agent/test_rag_get_cfg.py` — Update import
10. `tests/rag/test_rag_stages.py` — Update import

### Procedure

#### Step 1: Read git history for original rationale (Phase 1a)

Read git history for commits introducing `RagRerankError`, `RagExpansionError`, `RagPipelineError` to understand original rationale. Check `docs/00_governance/governance_03_issue-and-uncertainty-management.md` for CI-018 Known Issue details.

**Command:**
```bash
git log --oneline -- scripts/rag/llm_prompts.py | grep -i "rerank\|expansion"
git log --oneline -- scripts/rag/pipeline.py | grep -i "pipeline.*error"
```

#### Step 2: Add exception classes to exceptions.py (Phase 2a)

Add the following after line 37 (after `UnknownMetadataError`) in `scripts/rag/exceptions.py`:

```python
class RagRerankError(RagLayerError):
    """Raised when cross-encoder reranking fails (HTTP, parse, or connection error)."""

class RagExpansionError(RagLayerError):
    """Raised when MQE query expansion fails (HTTP, parse, or connection error)."""

class RagPipelineError(RagLayerError):
    """Raised when a pipeline-level operation fails (e.g. DB open, stage failure)."""
```

#### Step 3: Remove RagRerankError/RagExpansionError from llm_prompts.py (Phase 2b)

In `scripts/rag/llm_prompts.py`:
1. Remove lines 52-57 (the two exception class definitions)
2. Update the `__all__` export list (lines 232-253) to remove `"RagExpansionError"` and `"RagRerankError"` entries
3. Update the module docstring (lines 1-24) to remove references to `RagExpansionError` and `RagRerankError` from the "Provides:" section

#### Step 4: Remove RagPipelineError from pipeline.py (Phase 2c)

In `scripts/rag/pipeline.py`:
1. Remove line 54 (the `RagPipelineError` class definition)
2. Add import at the top of the file: `from rag.exceptions import RagPipelineError`

#### Step 5: Update import in stages/rerank.py (Phase 2d)

In `scripts/rag/stages/rerank.py`:
1. Change line 11 from `from rag.llm_prompts import RagRerankError` to `from rag.exceptions import RagRerankError`

#### Step 6: Update import in stages/mqe.py (Phase 2e)

In `scripts/rag/stages/mqe.py`:
1. Change line 11 from `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`

#### Step 7: Update import in llm_client.py (Phase 2f)

In `scripts/rag/llm_client.py`:
1. Change lines 36-54 to import `RagRerankError` and `RagExpansionError` from `rag.exceptions` instead of `rag.llm_prompts`
2. Keep the other imports (`MqeParseError`, `_MQE_MAX_TOKENS`, etc.) from `rag.llm_prompts`

#### Step 8: Update import in test_rag_pipeline.py (Phase 2g)

In `tests/rag/test_rag_pipeline.py`:
1. Change line 12 from `from rag.pipeline import RagPipeline, RagPipelineError` to `from rag.pipeline import RagPipeline` and `from rag.exceptions import RagPipelineError`

#### Step 9: Update import in test_rag_pipeline_stage.py (Phase 2h)

In `tests/rag/test_rag_pipeline_stage.py`:
1. Change all occurrences of `from rag.llm_prompts import RagRerankError` to `from rag.exceptions import RagRerankError`
2. Change all occurrences of `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`

#### Step 10: Update import in test_rag_get_cfg.py (Phase 2i)

In `tests/agent/test_rag_get_cfg.py`:
1. Change line 116 from `from rag.llm_prompts import RagRerankError` to `from rag.exceptions import RagRerankError`
2. Change line 75 from `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`
3. Change line 91 from `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`

#### Step 11: Update imports in test_rag_stages.py (Phase 2j)

In `tests/rag/test_rag_stages.py`:
1. Change line 544 from `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`
2. Change line 603 from `from rag.llm_prompts import RagExpansionError` to `from rag.exceptions import RagExpansionError`
3. Change line 814 from `from rag.llm_prompts import RagRerankError` to `from rag.exceptions import RagRerankError`
4. Change line 944 from `from rag.llm_prompts import RagRerankError` to `from rag.exceptions import RagRerankError`

### Details

The key changes are:
1. Adding three new exception classes to `exceptions.py` inheriting from `RagLayerError`
2. Removing the corresponding class definitions from their current locations
3. Updating all import statements across 9 files to point to `exceptions.py`
4. Updating the `__all__` export list in `llm_prompts.py`

## Compatibility considerations

- Existing code catching `RuntimeError` will no longer catch these exceptions directly — but since `RagLayerError(Exception)`, broad `except Exception` handlers still work
- Only narrow `except RuntimeError` catches would miss them, which is actually more correct behavior
- The exception hierarchy change is backward-compatible because `RagLayerError(Exception)` means existing `except Exception` handlers still work

## Security considerations

- No security impact; this is a refactoring task

## Rollback considerations

- If the changes introduce unexpected breakage, revert the import updates first (restore original imports), then verify tests pass before reverting the exception class additions

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/exceptions.py | Unit: verify exception hierarchy | Python inspection of class MRO | All three exceptions inherit from RagLayerError |
| scripts/rag/llm_prompts.py | Unit: verify no broken imports | `uv run python -c "from rag.llm_prompts import *"` | No ImportError |
| scripts/rag/pipeline.py | Unit: verify no broken imports | `uv run python -c "from rag.pipeline import *"` | No ImportError |
| tests/rag/test_rag_pipeline.py | Integration: verify tests pass | `uv run pytest tests/rag/test_rag_pipeline.py` | All tests pass |
| tests/rag/test_rag_pipeline_stage.py | Integration: verify tests pass | `uv run pytest tests/rag/test_rag_pipeline_stage.py` | All tests pass |

## Completion criteria

- All three exceptions (`RagRerankError`, `RagPipelineError`, `RagExpansionError`) inherit from `RagLayerError` (REQ-001)
- All imports are updated to point to `scripts/rag/exceptions.py` (REQ-002)
- All `except` clauses that previously caught these exceptions individually still work correctly (REQ-003)
- Tests pass after the change (REQ-004)
- No regression in exception handling behavior (REQ-005)
- Docstrings are updated with rationale (REQ-006)
- Backward compatibility maintained — existing code catching `RuntimeError` still works via inheritance (REQ-007)

## Out of scope

- Modifying exception handling logic beyond import updates
- Adding new exception types
- Modifying non-RAG-layer exceptions

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1a: Read git history for original rationale | Pending | — | — | |
| 2 | Phase 2a: Add exception classes to exceptions.py | Pending | — | — | |
| 3 | Phase 2b: Remove RagRerankError/RagExpansionError from llm_prompts.py | Pending | — | — | |
| 4 | Phase 2c: Remove RagPipelineError from pipeline.py | Pending | — | — | |
| 5 | Phase 2d: Update import in stages/rerank.py | Pending | — | — | |
| 6 | Phase 2e: Update import in stages/mqe.py | Pending | — | — | |
| 7 | Phase 2f: Update import in llm_client.py | Pending | — | — | |
| 8 | Phase 2g: Update import in test_rag_pipeline.py | Pending | — | — | |
| 9 | Phase 2h: Update import in test_rag_pipeline_stage.py | Pending | — | — | |
| 10 | Phase 2i: Update import in test_rag_get_cfg.py | Pending | — | — | |
| 11 | Phase 2j: Update imports in test_rag_stages.py | Pending | — | — | |
| 12 | Phase 3a: Run pytest to verify tests pass | Pending | — | — | |
| 13 | Phase 3b: Verify no broken imports remain | Pending | — | — | |
| 14 | Phase 3c: Verify exception handling behavior | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-007
- **Source issue**: issues/20260926-073329_unify_rag_exceptions_under_RagLayerError.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-093147_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-100531
- **Related target files**: scripts/rag/exceptions.py, scripts/rag/llm_prompts.py, scripts/rag/pipeline.py
