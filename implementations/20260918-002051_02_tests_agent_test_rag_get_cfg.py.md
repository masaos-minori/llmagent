## Goal
Update `tests/agent/test_rag_get_cfg.py::test_get_cfg_error_path` assertions based on the chosen direction from the sibling implementation procedure (`20260918-002051_01_scripts_rag_config_resolution.py.md`).

## Scope
- **In-Scope**: Update `tests/agent/test_rag_get_cfg.py::test_get_cfg_error_path` assertions based on the chosen direction from the sibling implementation procedure.
- **Out-of-Scope**: Do not change `RagConfigValidator`'s general validation rules beyond the specific `use_search`/`llm_url`/`embed_url` interaction described here. Do not investigate or fix any other file's test failures.

## Assumptions
- The sibling implementation procedure (`20260918-002051_01_scripts_rag_config_resolution.py.md`) will determine whether the defaults direction or the raise-based direction is chosen.
- The test's expectation of silent fallback is the intended behavior (the Issue's author seems to favor this interpretation).

## Design decisions
- If the defaults direction is chosen: update the test to assert that `result.llm_url == ""` and `result.embed_url == ""` still hold, but also verify that `result.use_search == False` (since we changed `_DEFAULTS_FOR_ALL["use_search"]` to `False`).
- If the raise-based direction is chosen: replace the assertion block with `pytest.raises(ValueError, match="...")` around the `resolve_rag_config` call.

## Alternatives considered
- Using a separate `_FALLBACK_DEFAULTS` dict for the "no config available" case vs. the "config loaded but incomplete" case — rejected because the Plan suggests this as a possible future enhancement, not an immediate fix.
- Adding try/except around the fallback path in `resolve_rag_config` itself — rejected because it doesn't address the root cause (self-contradiction between defaults and validation).

## Implementation
### Target file
`tests/agent/test_rag_get_cfg.py`

### Procedure
Update assertions based on the chosen direction from the sibling implementation procedure.

### Method
Mechanical edit: modify the test's assertion block.

### Details
1. **If defaults direction is chosen** (from sibling procedure):
   - In `test_get_cfg_error_path`, add assertion:
     ```python
     assert result.use_search == False  # Changed from True to False in _DEFAULTS_FOR_ALL
     ```
   - Keep existing assertions for `llm_url` and `embed_url` (they should remain empty strings)
   
2. **If raise-based direction is chosen** (from sibling procedure):
   - Replace the assertion block (lines 54-64) with:
     ```python
     with pytest.raises(ValueError, match="RAG config requires non-empty llm_url, embed_url when use_search=True"):
         result = pipeline_mod.resolve_rag_config(None, config_loader=failing_loader)
     ```
   - Update the docstring to reflect the new expected (raising) behavior

## Compatibility considerations
Updating the test based on the sibling procedure's choice ensures consistency between the implementation and its expectations.

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected side effects, revert the changes and instead choose the alternative direction (update the test to expect `ValueError` if the defaults direction was chosen, or revert the defaults change if the raise-based direction was chosen).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_rag_get_cfg.py | Unit test execution | `uv run pytest tests/agent/test_rag_get_cfg.py -v` | `test_get_cfg_error_path` passes |
| tests/rag/ | Integration regression | `uv run pytest tests/rag/ -q` | No new failures in RAG test suite |

## Completion criteria
- [ ] REQ-RAG-001-002: `uv run pytest tests/agent/test_rag_get_cfg.py -v` passes
- [ ] REQ-RAG-001-003: `uv run pytest tests/rag/ -q` shows no new regressions

## Out of scope
- Changing `RagConfigValidator`'s general validation rules beyond the specific `use_search`/`llm_url`/`embed_url` interaction
- Investigating or fixing any other file's test failures

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-RAG-001-002; Update test assertions based on sibling procedure | Pending | — | — | |
| 2 | REQ-RAG-001-002; Run targeted test | Pending | — | — | |
| 3 | REQ-RAG-001-003; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-RAG-001-002
- **Source issue**: issues/20260917-111003_rag01_test_get_cfg_error_path-failure-in-rag-pipeline-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-224558_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-002051
- **Related target files**: tests/agent/test_rag_get_cfg.py
- **Sibling implementation procedure**: 20260918-002051_01_scripts_rag_config_resolution.py.md
