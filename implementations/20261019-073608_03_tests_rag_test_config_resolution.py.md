## Goal

Add an integration test to `tests/rag/test_config_resolution.py` asserting that `resolve_rag_config`
raises a `ValueError` naming the RAG config validation failure when a prompt template is non-string,
and resolves normally when both templates are valid strings (T2 / REQ-002 / AC-2). This drives the
**real** `RagConfigValidator` path (no mock), proving the config-boundary fix closes the gap.

## Scope

- **In-Scope**: add an integration test in `tests/rag/test_config_resolution.py` asserting
  `resolve_rag_config` raises on a non-string template and succeeds on string templates.
- **Out-of-Scope**: changing the validator's or `resolve_rag_config`'s behavior; adding tests for
  other RAG fields; any `docs/*.md` change.

## Assumptions

- Passing a plain `dict` to `resolve_rag_config` uses the dict as-is (`config_resolution.py:115-116`)
  and never touches `ConfigLoader`, so no external config file is required.
- Defaults are filled for missing fields (`config_resolution.py:134-136`); providing a value for a
  key prevents its default from overriding it, so a non-string value supplied by the test reaches
  the validator.
- The `use_search` critical-fields check (`config_resolution.py:148-156`) fires when
  `use_search=True` and `llm_url`/`embed_url` are empty. To isolate the template-validation path,
  the tests set `use_search=False`.
- `resolve_rag_config` raises `ValueError(f"RAG config validation failed: {errors}")` on
  `ok=False` (`config_resolution.py:146`), matching the pattern already asserted by
  `test_validation_error_raises`.

## Design decisions

- Do **not** use the `mock_validator` fixture for these tests — the whole point is to exercise the
  real validator end-to-end.
- One test per path: (1) non-string template raises, (2) valid string templates resolve.

## Alternatives considered

N/A: exercising the real path is the lowest-risk way to prove REQ-002.

## Implementation

### Target file

`tests/rag/test_config_resolution.py`

### Procedure

1. Add `test_non_string_template_raises` that drives the real validator with a non-string template
   and asserts a `ValueError`:
   ```python
   def test_non_string_template_raises():
       """A non-string prompt template fails fast via the real validator."""
       with pytest.raises(ValueError, match="RAG config validation failed"):
           resolve_rag_config(
               {
                   "use_search": False,
                   "mqe_prompt_template": 123,
                   "rerank_prompt_template": "Rerank results for: {query}",
               }
           )
   ```
2. Add `test_valid_string_templates_resolve` that resolves a config with valid string templates:
   ```python
   def test_valid_string_templates_resolve():
       """Valid string templates resolve normally through the real validator."""
       result = resolve_rag_config(
           {
               "use_search": False,
               "mqe_prompt_template": "Expand query: {query}",
               "rerank_prompt_template": "Rerank results for: {query}",
           }
       )
       assert isinstance(result, RagConfigImpl)
       assert result.mqe_prompt_template == "Expand query: {query}"
       assert result.rerank_prompt_template == "Rerank results for: {query}"
   ```
3. Confirm the existing `test_validation_error_raises` still passes unchanged.
4. Run the affected test target and confirm clean. (T2)

### Method

- **Real validator, no mock.** These tests take no `mock_validator` argument, so
  `resolve_rag_config` constructs a real `RagConfigValidator` and validates the resolved config.
- **Isolate the path.** Set `use_search=False` so the `use_search` critical-fields check
  (`config_resolution.py:148-156`) does not raise first and mask the template-validation error.
- **Prove the contract.** The non-string case raises `ValueError` (REQ-002); the valid case returns
  a `RagConfigImpl` with the expected template strings (AC-2).

### Details

- `REQ-002`: `resolve_rag_config` raises `ValueError` naming the key when a template is non-string,
  before any pipeline run, and resolves normally when templates are valid strings.
- **Note on existing coverage:** the existing `test_validation_error_raises` uses the
  `mock_validator` fixture (it mocks `RagConfigValidator`), so it does **not** drive the real
  validator path. The new tests above fill that gap by exercising the real path.

## Compatibility considerations

Test-only change; does not affect production code or the CI exit contract. No `docs/*.md` change.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_config_resolution.py` | Integration: real validator raises on bad template, resolves on good | `uv run pytest tests/rag/test_config_resolution.py` | Non-string raises `ValueError`; valid templates resolve; existing tests pass |

## Completion criteria

- A test asserting `resolve_rag_config` raises on a non-string template via the real validator (T2).
- A test asserting `resolve_rag_config` resolves normally with valid string templates (AC-2).
- The existing `test_validation_error_raises` suite passes unchanged.

## Out of scope

Changing the validator's or `resolve_rag_config`'s behavior, adding tests for other RAG fields, and
any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Add prompt-template type validation to `RagConfigValidator.validate` | Pending | — | — | REQ-001; AC-1, AC-3 |
| 2 | Phase 2: Add unit + integration tests | Pending | — | — | REQ-001/002; T1/T2 |
| 3 | Phase 3: Run ruff / mypy / bandit / affected tests | Pending | — | — | all REQs |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261018-193310_rag001_rag-prompt-templates-are-not-type-validated-at-config-load-so-the-pipeline-crashes-with-typeerror.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-220244_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-073608
- **Related target files**: tests/rag/test_config_resolution.py
