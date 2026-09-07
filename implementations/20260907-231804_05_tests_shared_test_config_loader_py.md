## Goal

Add a new unit test for unknown-top-level-key rejection in production (REQ-004). The test asserts that an unknown/mistyped top-level config key (not present among `config_dataclasses.py`'s introspected fields) is rejected by `ProductionConfigValidator.validate()` in production mode.

## Scope

Modify exactly one file: `tests/shared/test_config_loader.py`. Add a new test class or method for unknown-key rejection.

## Assumptions

- The `ProductionConfigValidator` is available via `from shared.production_config_validator import ProductionConfigValidator`.
- The test can use `pytest` fixtures and `unittest.mock` for mocking.
- Existing tests in this file use `tmp_path` fixture for temporary config files — follow the same pattern.

## Design decisions

- Add a new test class `TestUnknownTopLevelKeyRejection` with methods for production and non-production scenarios.
- Use `pytest` fixtures and mock configurations to avoid needing actual TOML files.
- Follow the existing test patterns in this file (e.g., `TestRestrictToIsolation`, `TestMergeOrder`).

## Alternatives considered

- Adding the test as a standalone function: rejected because the existing file uses class-based test organization.
- Using a real TOML file with an unknown key: rejected because it would require file I/O setup; mock configs are sufficient and more deterministic.

## Implementation
### Target file
`tests/shared/test_config_loader.py`

### Procedure
Add a new test class `TestUnknownTopLevelKeyRejection` with methods for production and non-production scenarios.

### Method
1. Open `tests/shared/test_config_loader.py`.
2. At the end of the file, add a new class:
```python
class TestUnknownTopLevelKeyRejection:
    """Tests for unknown top-level key rejection in production."""

    def test_unknown_top_level_key_rejected_in_production(self) -> None:
        """Assert that an unknown/mistyped top-level config key is rejected in production."""
        from shared.production_config_validator import ProductionConfigValidator

        validator = ProductionConfigValidator(is_production=True)
        result = validator.validate({"unknown_mistyped_key": "value"})
        assert len(result.errors) > 0
        assert any("unknown" in e.lower() for e in result.errors)

    def test_known_keys_pass_in_production(self) -> None:
        """Assert that known keys derived from dataclass fields pass validation."""
        from agent.config_dataclasses import LLMConfig
        from shared.production_config_validator import ProductionConfigValidator

        # llm_url is a field name in LLMConfig
        validator = ProductionConfigValidator(is_production=True)
        result = validator.validate({"llm_url": "http://localhost:8080"})
        assert len(result.errors) == 0

    def test_unknown_key_allowed_in_non_production(self) -> None:
        """Assert that unknown keys are not rejected in non-production environments."""
        from shared.production_config_validator import ProductionConfigValidator

        validator = ProductionConfigValidator(is_production=False)
        result = validator.validate({"unknown_mistyped_key": "value"})
        assert len(result.errors) == 0
```

### Details
1. Read the existing test patterns in the file (e.g., `TestRestrictToIsolation`).
2. Ensure imports match the project's conventions (`from shared.production_config_validator import ProductionConfigValidator`).
3. Verify that `ProductionConfigValidator.__init__` accepts `is_production` parameter.
4. Run the tests locally before committing: `uv run pytest tests/shared/test_config_loader.py::TestUnknownTopLevelKeyRejection -xvs`.

## Compatibility considerations

- This adds new tests only; no existing behavior changes.
- The test depends on `ProductionConfigValidator` being importable from `shared.production_config_validator`.

## Security considerations

This test validates a security-relevant behavior: unknown config keys should be rejected in production to prevent misconfiguration from reaching production undetected.

## Rollback considerations

Reverting this change means removing the new test class. No operational impact since this is a test-only change.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_loader.py` | Unit: verify unknown key rejection in production | `pytest -xvs tests/shared/test_config_loader.py::TestUnknownTopLevelKeyRejection` | All 3 tests pass |

## Completion criteria

- [ ] New test asserts unknown/mistyped top-level config key is rejected in production
- [ ] New test asserts known keys derived from dataclass fields pass validation
- [ ] New test asserts unknown keys are allowed in non-production environments
- [ ] All tests pass: `uv run pytest tests/shared/test_config_loader.py -q`

## Out of scope

- Modifying source code files.
- Adding tests for other requirements (covered by separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test for unknown-key rejection in production | Pending | — | — | |
| 2 | Add test for known keys passing validation | Pending | — | — | |
| 3 | Add test for unknown keys allowed in non-production | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: tests/shared/test_config_loader.py
