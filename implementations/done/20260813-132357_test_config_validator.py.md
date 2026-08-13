# Implementation Procedure: Update Config Validator Tests After Dimension Validation Removal

## Goal

Update `tests/shared/test_config_validator.py` to reflect removal of `embedding_dim` vs `vec_dim` validation from `RagConfigValidator.validate()`:
- Remove `test_embedding_dim_mismatch` entirely.
- Update remaining tests that reference `embedding_dim`/`vec_dim` keys.

## Scope

- **In scope**: Modify `tests/shared/test_config_validator.py` only.
- **Out of scope**: Schema changes, config validator source changes, config file changes.

## Assumptions

- The validator no longer produces errors for `embedding_dim`/`vec_dim` mismatch.
- Tests should verify behavior consistent with the updated validator.

## Design decisions

- Remove `test_embedding_dim_mismatch` entirely rather than modifying it — the scenario no longer exists.
- For tests that include both dimension keys and other settings, remove only the dimension keys while preserving the rest of the test's purpose.

## Alternatives considered

- Keep `test_embedding_dim_match` as-is but change its assertion: rejected because the test name implies dimension matching matters, which it no longer does.
- Rename `test_embedding_dim_match` to something generic: rejected because the test's purpose (validating a config without errors) is already covered by `test_ok_no_errors`.

## Implementation

### Target file

`tests/shared/test_config_validator.py`

### Procedure

**Dependency:** Complete `implementations/20260813-132357_config_validator.py.md` first. The validator source change must precede test updates.

1. Remove `test_embedding_dim_mismatch` method (lines 15–23).
2. Update `test_embedding_dim_match` — remove dimension keys, rename if appropriate.
3. Update `test_multiple_errors` — remove dimension keys from test input.
4. Update `test_flat_shape_uses_root_dict` — remove dimension keys from test input.
5. Verify all references to `embedding_dim`, `vec_dim`, `embedding_dims` are removed or updated.

### Method

Inline modifications: deletions and updates to test inputs/assertions.

### Details

#### Change 1: Remove `test_embedding_dim_mismatch` (lines 15–23)

Delete entire method:

```python
    def test_embedding_dim_mismatch(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"embedding_dim": 768, "vec_dim": 1536},
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert "embedding_dim=768 != vec_dim=1536" in result.errors[0]
```

#### Change 2: Update `test_embedding_dim_match` (lines 25–31)

Remove dimension keys from config. Since the test's sole purpose was validating dimension matching, and that validation is removed, consider whether this test still has value. Options:
- Option A: Delete the test entirely (simpler, since `test_ok_no_errors` covers the same scenario).
- Option B: Keep the test but rename and update — keep only if there is additional logic being tested beyond dimension matching.

Recommended: delete the test. If kept, update to:

```python
    def test_rag_config_with_dimension_keys_no_error(self) -> None:
        """Dimension keys no longer trigger validation errors."""
        result = self.validator.validate(
            {
                "rag": {},
            }
        )
        assert result.ok is True
```

#### Change 3: Update `test_multiple_errors` (lines 67–80)

Remove dimension keys from test input. Current:

```python
    def test_multiple_errors(self) -> None:
        result = self.validator.validate(
            {
                "rag": {
                    "embedding_dim": 768,
                    "vec_dim": 1536,
                    "use_rrf": False,
                    "semantic_cache_threshold": 0.2,
                },
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 2
```

After removing dimension keys, the expected error count drops from 1 to 0 (only semantic_cache_threshold_low warning remains):

```python
    def test_multiple_warnings(self) -> None:
        result = self.validator.validate(
            {
                "rag": {
                    "use_rrf": False,
                    "semantic_cache_threshold": 0.2,
                },
            }
        )
        assert result.ok is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 2
```

#### Change 4: Update `test_flat_shape_uses_root_dict` (lines 86–95)

Remove dimension keys from test input. Current:

```python
    def test_flat_shape_uses_root_dict(self) -> None:
        result = self.validator.validate(
            {
                "embedding_dim": 768,
                "vec_dim": 1536,
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert "embedding_dim=768 != vec_dim=1536" in result.errors[0]
```

After removal, the config has no invalid settings:

```python
    def test_flat_shape_uses_root_dict(self) -> None:
        result = self.validator.validate(
            {
                "use_rrf": False,
            }
        )
        assert result.ok is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "use_rrf=false" in result.warnings[0]
```

#### Verification

After all changes:

```bash
grep -n "embedding_dim\|vec_dim\|embedding_dims" tests/shared/test_config_validator.py
```

Expected: no results (all references removed or updated).

## Compatibility considerations

- Test assertions change: fewer errors reported, different expected counts.
- No behavioral change to production code — only test alignment.

## Security considerations

N/A — test-only changes.

## Rollback considerations

- To roll back, restore deleted methods and original test inputs/assertions.
- No data loss risk.

## Validation plan

| Step | Command | Expected Outcome |
|---|---|---|
| 1 | `grep -n "embedding_dim\|vec_dim\|embedding_dims" tests/shared/test_config_validator.py` | No results |
| 2 | `pytest tests/shared/test_config_validator.py -v` | All tests pass |

## Out of scope

- Schema constraint additions (handled separately).
- Config validator source changes (handled separately).
- Config file reference removal (handled separately).
- Documentation updates.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260807_06_issue.md
- Source requirement: requires/20260813_094450_require.md
- Source plan: plans/20260813-103307_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-132357
- Related target files: tests/shared/test_config_validator.py
