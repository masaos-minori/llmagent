## Goal
Resolve the self-contradiction in `scripts/rag/config_resolution.py`: `_DEFAULTS_FOR_ALL["use_search"]` is `True` while `llm_url`/`embed_url` are empty strings, causing `resolve_rag_config` to always raise `ValueError` on the pure-fallback path instead of degrading gracefully.

## Scope
- **In-Scope**: Fix the self-contradiction in `scripts/rag/config_resolution.py`; update `tests/agent/test_rag_get_cfg.py::test_get_cfg_error_path` if needed.
- **Out-of-Scope**: Do not change `RagConfigValidator`'s general validation rules beyond the specific `use_search`/`llm_url`/`embed_url` interaction described here. Do not investigate or fix any other file's test failures.

## Assumptions
- Changing `_DEFAULTS_FOR_ALL["use_search"]` to `False` will resolve the self-contradiction and allow the fallback path to work correctly.
- The test's expectation of silent fallback is the intended behavior (the Issue's author seems to favor this interpretation).

## Design decisions
- For Direction 1 (fix defaults): Change `_DEFAULTS_FOR_ALL["use_search"]` to `False` so the fallback defaults don't trigger the "critical fields required when use_search=True" validation. This makes the fallback path degrade gracefully (search disabled) instead of failing loudly.
- For Direction 2 (fix test): Add `pytest.raises(ValueError, match="...")` around the `resolve_rag_config` call in `test_get_cfg_error_path`, updating the docstring to reflect the new expected behavior.

## Alternatives considered
- Using a separate `_FALLBACK_DEFAULTS` dict for the "no config available" case vs. the "config loaded but incomplete" case — rejected because the Plan suggests this as a possible future enhancement, not an immediate fix.
- Adding try/except around the fallback path in `resolve_rag_config` itself — rejected because it doesn't address the root cause (self-contradiction between defaults and validation).

## Implementation
### Target file
`scripts/rag/config_resolution.py`

### Procedure
Change `_DEFAULTS_FOR_ALL["use_search"]` to `False` OR add try/except around fallback path.

### Method
Mechanical edit: modify `_DEFAULTS_FOR_ALL` dictionary value.

### Details
1. Line 65: Change `"use_search": True` to `"use_search": False` in `_DEFAULTS_FOR_ALL` dictionary
2. After making this change, re-run the full `test_rag_get_cfg.py` file and `tests/rag/` to confirm no other test relies on `use_search=True` being the fallback default
3. If the raise-based direction is chosen instead:
   - In `tests/agent/test_rag_get_cfg.py`, replace the assertion block (lines 54-64) with:
     ```python
     with pytest.raises(ValueError, match="RAG config requires non-empty llm_url, embed_url when use_search=True"):
         result = pipeline_mod.resolve_rag_config(None, config_loader=failing_loader)
     ```
   - Update the docstring to reflect the new expected (raising) behavior

## Compatibility considerations
Changing `_DEFAULTS_FOR_ALL["use_search"]` to `False` may affect other parts of the system that rely on `use_search=True` being the default. Run `uv run pytest tests/rag/ -q` after making the change to catch any regressions early.

## Security considerations
N/A: changing a configuration default does not introduce security concerns.

## Rollback considerations
If the fix causes unexpected side effects, revert the `_DEFAULTS_FOR_ALL["use_search"]` change and instead choose the raise-based direction (updating the test to expect `ValueError`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/config_resolution.py | Unit test execution | `uv run pytest tests/agent/test_rag_get_cfg.py -v` | `test_get_cfg_error_path` passes |
| tests/rag/ | Integration regression | `uv run pytest tests/rag/ -q` | No new failures in RAG test suite |

## Completion criteria
- [ ] REQ-RAG-001-001: The self-contradiction is resolved — either `_DEFAULTS_FOR_ALL["use_search"]` is `False` for fallback, or the test asserts `ValueError`
- [ ] REQ-RAG-001-002: `uv run pytest tests/agent/test_rag_get_cfg.py -v` passes
- [ ] REQ-RAG-001-003: `uv run pytest tests/rag/ -q` shows no new regressions
- [ ] REQ-RAG-001-003: The chosen behavior (silent fallback vs. explicit raise) is consistent between `_DEFAULTS_FOR_ALL` and the validation logic in `resolve_rag_config`, and documented in the docstring/comment for `resolve_rag_config` if not already clear

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
| 1 | REQ-RAG-001-001; Determine correct direction (defaults vs. test) | Pending | — | — | |
| 2 | REQ-RAG-001-001; Implement defaults change | Pending | — | — | |
| 3 | REQ-RAG-001-002; Re-run tests after defaults change | Pending | — | — | |
| 4 | REQ-RAG-001-001; Implement test change (raise direction) | Pending | — | — | |
| 5 | REQ-RAG-001-002; Run targeted test | Pending | — | — | |
| 6 | REQ-RAG-001-003; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-RAG-001-001
- **Source issue**: issues/20260917-111003_rag01_test_get_cfg_error_path-failure-in-rag-pipeline-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-224558_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-002051
- **Related target files**: scripts/rag/config_resolution.py
