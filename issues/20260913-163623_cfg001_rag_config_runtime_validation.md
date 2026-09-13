# Add runtime validation for RagConfigImpl required fields

## Priority
Medium

## Summary
Add validation in resolve_rag_config() to ensure RagConfigImpl receives all required fields with valid values. Currently missing or invalid fields cause TypeError or unexpected behavior at runtime rather than failing fast with a clear error message.

## Background
RagConfigImpl (models_config.py:12-43) is a dataclass with no default values — every field must be provided. resolve_rag_config() fills missing fields from _DEFAULTS_FOR_ALL (config_resolution.py:55-84) and filters unknown keys via `_ALL_FIELDS` (config_resolution.py:22-53). However, the validator only checks for deprecated keys, not for missing required fields or type mismatches.

## Problem
When a config source omits a required field (e.g., rag_db_path, llm_url, embed_url), the code fails silently or with confusing errors:
1. Missing field → TypeError: __init__() missing required positional argument
2. Invalid value (e.g., negative top_k) → ValueError raised deep in the pipeline
3. Type mismatch (e.g., string instead of int) → AttributeError or silent wrong behavior

The current flow: resolve_rag_config() → filtered_cfg → RagConfigImpl(**filtered_cfg). If filtered_cfg is missing a key, Python raises TypeError. The error message does not indicate which field is missing.

## Reason for Change
Fail-fast with a clear error message identifying the missing field. This prevents confusing downstream errors and makes configuration debugging easier.

## Implementation Intent
In resolve_rag_config(), after filling defaults and filtering known fields, validate that all _ALL_FIELDS keys are present in filtered_cfg. Raise ValueError with the list of missing fields if any are absent. Additionally, validate critical fields (rag_db_path, llm_url, embed_url) are non-empty strings when use_search=True.

## Target Files or Areas
- scripts/rag/config_resolution.py
- scripts/rag/models_config.py

## Required Changes
- After line ~134 in config_resolution.py (after filtered_cfg construction):
  - Check that all keys in _ALL_FIELDS are present in filtered_cfg
  - Raise ValueError with missing key names if any are absent
- Validate critical fields (rag_db_path, llm_url, embed_url) are non-empty when use_search=True
- Consider adding @dataclass(frozen=True) to RagConfigImpl for immutability

## Constraints
- Must preserve existing default values from _DEFAULTS_FOR_ALL
- Must not break backward compatibility — configs that currently work must still work
- Validation errors must be clear and actionable

## Acceptance Criteria
- Missing required field produces ValueError listing the missing key name(s)
- Critical fields validated when use_search=True
- Existing configs that pass current validation continue to work
- All existing tests pass after changes

## Testing Expectations
- Add test for resolve_rag_config() with missing rag_db_path
- Add test for resolve_rag_config() with missing llm_url
- Add test for resolve_rag_config() with empty rag_db_path when use_search=True
- Run: pytest tests/rag/ -k config

## Documentation Impact
Update docstring of resolve_rag_config() to document the new validation behavior.

## Out of Scope
- Adding default values to RagConfigImpl fields (would change the dataclass contract)
- Changing the validation logic in RagConfigValidator (separate concern)
- Runtime hot-reload of config (out of scope for this fix)

## Dependencies
N/A: none

## Unresolved Questions
Should we also validate field types at resolution time? E.g., reject rag_top_k=0 or rag_min_score=-1.0. This would catch more errors early but adds complexity.

## AI Implementation Instruction
1. Read scripts/rag/config_resolution.py
2. After line 134 (`filtered_cfg = {k: v for k, v in _raw_cfg.items() if k in _ALL_FIELDS}`), add:
   ```python
   missing_keys = _ALL_FIELDS - set(filtered_cfg.keys())
   if missing_keys:
       raise ValueError(f"Missing RAG config fields: {', '.join(sorted(missing_keys))}")
   ```
3. Optionally add validation for critical fields (rag_db_path, llm_url, embed_url) being non-empty when use_search=True
4. Run pytest tests/rag/ -k config to verify existing tests pass
5. Do NOT modify models_config.py unless requested

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/config_resolution.py, scripts/rag/models_config.py
