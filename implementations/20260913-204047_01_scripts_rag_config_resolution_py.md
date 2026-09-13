## Goal

Add runtime validation for critical RagConfigImpl fields (`rag_db_path`, `llm_url`, `embed_url`) when `use_search=True`, ensuring fail-fast behavior with a clear `ValueError` naming every empty field, per REQ-001.

## Scope

- In-Scope: Adding a post-resolution check in `resolve_rag_config()` for `rag_db_path`/`llm_url`/`embed_url` non-emptiness, gated on `use_search=True`; updating `resolve_rag_config()`'s docstring to document the new validation behavior
- Out-of-Scope: Adding default values to RagConfigImpl fields; changing RagConfigValidator's existing checks; type validation for other fields (e.g., rejecting rag_top_k=0); runtime hot-reload of config

## Assumptions

- `filtered_cfg["use_search"]` is always present at the check point (guaranteed by the `_ALL_FIELDS`/`_DEFAULTS_FOR_ALL` back-fill loop)
- A config source may legitimately omit `rag_db_path`/`llm_url`/`embed_url` when `use_search=False` (e.g., a pipeline instance that never searches) — the new check must not break that case
- No caller currently relies on `resolve_rag_config()` succeeding with `use_search=True` and an empty `rag_db_path`/`llm_url`/`embed_url` (if one did, it was already heading toward a downstream failure — this Plan surfaces it earlier, not differently)

## Design decisions

1. Gate the check on `use_search=True` only — a non-search pipeline instance has no structural need for these fields to be non-empty, and backward compatibility with configs that work today requires preserving this distinction.
2. Collect and report every empty field in one `ValueError`, not just the first — matches the Issue's own Implementation Intent phrasing ("validate ... raise ValueError with the list of missing fields") applied to emptiness rather than presence.
3. Implement as a single guard-clause block (collect-then-raise) rather than distributing checks throughout the function body, per Design decision 2 in the Plan — avoids pushing radon cyclomatic complexity further beyond its current C (19) rating.
4. Do not touch RagConfigValidator — its scope (cross-file consistency: use_rrf, removed keys) is a different concern than per-field emptiness on the already-merged filtered_cfg.

## Alternatives considered

- **Per-field early returns**: Raise immediately on the first empty field. Rejected because collecting all empty fields in one error message is more actionable for operators.
- **Adding defaults to RagConfigImpl**: Would change the dataclass contract. Rejected per Plan scope.
- **Extending RagConfigValidator**: Its scope (cross-file consistency) is separate from per-field emptiness. Conflating them would widen blast radius unnecessarily.

## Implementation
### Target file
`scripts/rag/config_resolution.py`

### Procedure
1. After `filtered_cfg` is built (line 134) and before the `RagConfigImpl(**filtered_cfg)` return (line 143), add a validation check
2. Update `resolve_rag_config()`'s docstring to document the new failure mode

### Method
Guard-clause insertion + docstring update in `resolve_rag_config()`.

### Details
1. **Phase 1: Preparation — Confirm no existing caller relies on the current silent-empty behavior**
   a. Locate `scripts/rag/pipeline.py:98`'s single call site
   b. Verify it does not pass `use_search=True` with an empty `rag_db_path`/`llm_url`/`embed_url`
   
2. **Phase 2: Core Logic — Add the validation check**
   a. After line 134 (`filtered_cfg` construction) and before line 143 (`RagConfigImpl(**filtered_cfg)` return):
      ```python
      # After filtered_cfg is built, validate critical fields when search is enabled
      if filtered_cfg.get("use_search", False):
          empty_fields = []
          for field_name in ("rag_db_path", "llm_url", "embed_url"):
              value = filtered_cfg.get(field_name)
              if value == "" or value is None:
                  empty_fields.append(field_name)
          if empty_fields:
              raise ValueError(
                  f"RAG config requires non-empty {', '.join(empty_fields)} "
                  f"when use_search=True"
              )
      ```
      This collects all empty critical fields into a list and raises a single `ValueError` naming every empty field found.
   
   b. Update `resolve_rag_config()`'s docstring to document the new failure mode:
      - Add a "Raises" section documenting the `ValueError` condition
      - Example: `raises ValueError: If use_search=True and any of rag_db_path, llm_url, embed_url is empty`

3. **Phase 3: Deployment & Verification**
   a. Run `pytest tests/rag/test_config_resolution.py` to verify existing and new tests pass

## Compatibility considerations

- The new `ValueError` path changes failure behavior for any caller with `use_search=True` and an empty critical field — but Phase 1 confirms no such caller exists in this repository
- The new error message is actionable and points directly at the missing configuration, which is the explicit intent of this change
- When `use_search=False`, the check is skipped entirely, preserving backward compatibility with non-search pipeline instances

## Security considerations

N/A: Runtime validation addition, no security impact.

## Rollback considerations

Simple revert of the guard-clause insertion and docstring update — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/config_resolution.py | Unit — verify ValueError raised/not-raised per use_search/empty-field combination | pytest tests/rag/test_config_resolution.py -k use_search | Raises naming every empty field when use_search=True; silent when use_search=False |

## Completion criteria

- [ ] `resolve_rag_config()` raises `ValueError` when `use_search=True` and `rag_db_path` is empty
- [ ] `resolve_rag_config()` raises `ValueError` when `use_search=True` and `llm_url` is empty
- [ ] `resolve_rag_config()` raises `ValueError` when `use_search=True` and `embed_url` is empty
- [ ] The `ValueError` message names every empty field, not just the first found
- [ ] `resolve_rag_config()` does NOT raise when `use_search=False`, even if these fields are empty
- [ ] All existing tests pass after changes
- [ ] `pytest tests/rag/test_config_resolution.py` runs without errors

## Out of scope

- Modifying `scripts/rag/models_config.py` (reference file only)
- Modifying `scripts/shared/config_validator.py` (reference file only)
- Modifying `tests/rag/test_config_resolution.py` (reference file only — tests added separately)
- Adding default values to RagConfigImpl fields
- Changing RagConfigValidator's existing checks
- Type validation for other fields (e.g., rejecting rag_top_k=0)
- Runtime hot-reload of config

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no existing caller relies on silent-empty behavior | Completed | — | — | Check pipeline.py:98 |
| 2 | Add guard-clause validation after filtered_cfg construction | Completed | — | — | Collect-then-raise pattern |
| 3 | Update resolve_rag_config() docstring | Completed | — | — | Document ValueError condition |
| 4 | Run validation sequence (rules/toolchain.md) | Completed | — | — | pytest tests/rag/ |

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
- **Requirement ID**: REQ-001 — add runtime validation for critical RagConfigImpl fields when use_search=True
- **Source issue**: issues/20260913-163623_cfg001_rag_config_runtime_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-191219_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-204047
- **Related target files**: scripts/rag/config_resolution.py
