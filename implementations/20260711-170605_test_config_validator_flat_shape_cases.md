# Implementation: tests/test_config_validator.py — flat-shape + max_size test additions

## Goal

Add tests confirming `RagConfigValidator.validate()` correctly validates the flat
`module_cfg` shape (MCP path) in addition to the nested `{"rag": {...}}` shape, and
correctly rejects negative `semantic_cache_max_size` while accepting `0`, without
disturbing any of the 9 pre-existing nested-shape tests.

## Scope

**In:**
- `tests/test_config_validator.py` — add 4 new test methods/functions (flat-shape
  `use_rrf` warning, flat-shape negative `max_size` error, flat-shape zero `max_size`
  no-error, nested-shape negative `max_size` error)

**Out:**
- No modification to any of the 9 existing test cases — they must remain exactly as-is
  and continue passing (this is itself an acceptance criterion: the normalization is a
  strict superset of prior behavior for nested-shape input)
- No changes to `scripts/shared/config_validator.py` itself (covered by the companion
  implementation doc `20260711-170540_config_validator_flat_shape_normalization.md`;
  this test file assumes that fix is in place when tests run)

## Assumptions

1. `RagConfigValidator` and `ConfigValidationResult` are importable from
   `shared.config_validator` (matching however the existing 9 tests already import them —
   check the existing import block in `tests/test_config_validator.py` and reuse it as-is).
2. Existing tests construct `self.validator = RagConfigValidator()` in a `setUp`/fixture,
   or construct one per test — match whichever pattern the existing 9 tests already use.
3. `ConfigValidationResult.ok` is `True` iff `errors` is empty (per its existing `@property`
   definition) — tests assert on `.ok` and/or `len(result.warnings)` as appropriate.
4. Flat-shape input for these tests is a plain dict with no `"rag"` key, e.g.
   `{"use_rrf": False}` or `{"semantic_cache_max_size": -1}` — matching the actual shape
   `scripts/mcp_servers/rag_pipeline/service.py`'s `module_cfg` produces.

## Implementation

### Target file

`tests/test_config_validator.py`

### Procedure

1. Locate the existing test class/module structure and the 9 existing tests; do not
   modify them.
2. Add 4 new test cases, appended after the existing tests (or in a logically grouped
   location near related existing tests, e.g. near any existing `use_rrf`/`max_size`
   tests if such grouping already exists):
   - `test_flat_config_use_rrf_false_warning`: `validate({"use_rrf": False})`; assert
     exactly 1 warning is produced (the `use_rrf=false degrades retrieval quality...`
     message).
   - `test_flat_config_negative_max_size_error`: `validate({"semantic_cache_max_size": -1})`;
     assert `result.ok is False`.
   - `test_flat_config_max_size_zero_no_error`: `validate({"semantic_cache_max_size": 0})`;
     assert `result.ok is True` (confirms `0` is accepted, no error and no warning).
   - `test_nested_config_negative_max_size_error`: `validate({"rag": {"semantic_cache_max_size": -1}})`;
     assert `result.ok is False` (confirms the new `max_size` check also works correctly
     under the pre-existing nested shape, not just the new flat shape).
3. Run the full file to confirm 9 pre-existing + 4 new = 13 tests, all passing.

### Method

Pure test-file addition; no production code touched by this doc. Follow whatever test
framework convention (`unittest.TestCase` vs plain `pytest` functions) the existing 9
tests already use — do not introduce a second convention in the same file.

### Details

- Keep new test names descriptive and distinct from existing ones (no name collisions).
- Each new test should construct its own input dict inline (no need for shared fixtures
  beyond what the existing tests already use for validator construction).

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_config_validator.py` | 0 errors |
| Tests | `uv run pytest tests/test_config_validator.py -v` | All 13 tests pass (9 pre-existing unmodified + 4 new) |
| Regression | Diff review of `tests/test_config_validator.py` | Confirms none of the 9 pre-existing test bodies were altered, only new tests appended |
