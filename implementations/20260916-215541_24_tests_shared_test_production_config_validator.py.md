## Goal

Add regression coverage proving `ConfigValidationResult` is the same class as `shared.config_validator.ConfigValidationResult`; add a test proving the valid-key set is unchanged after REQ-006's schema-source consolidation; add the REQ-007 integration test against the real `config/agent.toml`.

## Scope

- Modify `tests/shared/test_production_config_validator.py`: add three new tests.

## Assumptions

- The canonical `ConfigValidationResult` will be hosted in `scripts/shared/config_validator.py` (covered in previous row).
- The valid-key set must remain identical to today's (T-7).
- The real `config/agent.toml` can be loaded via `ConfigLoader().load_all()` and accepted by both validators with zero errors.

## Design decisions

- Add each new test as a separate method in the appropriate existing test class.
- Use `pytest.importorskip` for any optional dependencies needed by the integration test.

## Alternatives considered

- Creating a new test class for each requirement — rejected: adds unnecessary class proliferation.
- Merging all three requirements into one test — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_production_config_validator.py`

### Procedure

1. Add a test asserting `ConfigValidationResult` identity.
2. Add a test asserting `validate_unknown_tool_safety_tiers()`'s single-argument construction works.
3. Add a test asserting the valid-key set is unchanged after REQ-006's schema-source consolidation.
4. Add an integration test loading `config/agent.toml` through both validators.

### Method

- **Step 1**: Add ConfigValidationResult identity test:

```python
def test_config_validation_result_identity(self) -> None:
    """REQ-004: production_config_validator.ConfigValidationResult IS shared.config_validator.ConfigValidationResult."""
    from shared.production_config_validator import ConfigValidationResult as PCVResult
    from shared.config_validator import ConfigValidationResult as CVResult
    assert PCVResult is CVResult
```

- **Step 2**: Add validate_unknown_tool_safety_tiers compatibility test:

```python
def test_validate_unknown_tool_safety_tiers_single_arg_construction(self) -> None:
    """REQ-004: validate_unknown_tool_safety_tiers()'s single-arg construction still works."""
    from shared.production_config_validator import ProductionConfigValidator
    validator = ProductionConfigValidator()
    result = validator.validate_unknown_tool_safety_tiers(["unknown_tool"])
    # Should not raise; warnings should default to empty list
    assert isinstance(result, object)  # ConfigValidationResult instance
    assert hasattr(result, 'errors')
    assert hasattr(result, 'warnings')
```

- **Step 3**: Add valid-key-set-unchanged test:

```python
def test_valid_key_set_unchanged_after_schema_consolidation(self) -> None:
    """REQ-006: the valid-key set is unchanged after consolidating _get_valid_production_keys()."""
    from shared.production_config_validator import ProductionConfigValidator
    validator = ProductionConfigValidator()
    keys = validator._get_valid_production_keys()
    # Assert specific known keys are present (regression baseline)
    assert "agent_memory_max_startup_snippets" in keys
    assert "system_prompt_tool" in keys
    assert "security_profile" in keys
    assert "embed_url" in keys
    assert "chunk_size" in keys
```

- **Step 4**: Add integration test against real config/agent.toml:

```python
@pytest.mark.integration
def test_integration_real_config_agent_toml(self) -> None:
    """REQ-007: real config/agent.toml passes both validators with zero errors."""
    import os
    from pathlib import Path
    
    # Load the real config/agent.toml
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    from shared.config_loader import ConfigLoader
    loader = ConfigLoader(config_dir=config_dir)
    cfg = loader.load_all(strict=True)
    
    # Validate with RagConfigValidator
    from shared.config_validator import RagConfigValidator
    rag_result = RagConfigValidator().validate(cfg)
    assert rag_result.ok is True
    assert len(rag_result.errors) == 0
    
    # Validate with ProductionConfigValidator
    from shared.production_config_validator import ProductionConfigValidator
    prod_result = ProductionConfigValidator().validate(cfg)
    assert prod_result.ok is True
    assert len(prod_result.errors) == 0
```

### Details

**Step 1 — ConfigValidationResult identity:**

Add after the existing test methods in the appropriate test class:

```python
def test_config_validation_result_identity(self) -> None:
    """REQ-004: production_config_validator.ConfigValidationResult IS shared.config_validator.ConfigValidationResult."""
    from shared.production_config_validator import ConfigValidationResult as PCVResult
    from shared.config_validator import ConfigValidationResult as CVResult
    assert PCVResult is CVResult
```

**Step 2 — validate_unknown_tool_safety_tiers compatibility:**

Add after the identity test:

```python
def test_validate_unknown_tool_safety_tiers_single_arg_construction(self) -> None:
    """REQ-004: validate_unknown_tool_safety_tiers()'s single-arg construction still works."""
    from shared.production_config_validator import ProductionConfigValidator
    validator = ProductionConfigValidator()
    result = validator.validate_unknown_tool_safety_tiers(["unknown_tool"])
    assert isinstance(result, object)
    assert hasattr(result, 'errors')
    assert hasattr(result, 'warnings')
```

**Step 3 — Valid-key-set-unchanged:**

Add after the compatibility test:

```python
def test_valid_key_set_unchanged_after_schema_consolidation(self) -> None:
    """REQ-006: the valid-key set is unchanged after consolidating _get_valid_production_keys()."""
    from shared.production_config_validator import ProductionConfigValidator
    validator = ProductionConfigValidator()
    keys = validator._get_valid_production_keys()
    assert "agent_memory_max_startup_snippets" in keys
    assert "system_prompt_tool" in keys
    assert "security_profile" in keys
    assert "embed_url" in keys
    assert "chunk_size" in keys
```

**Step 4 — Integration test:**

Add after the valid-key-set test:

```python
@pytest.mark.integration
def test_integration_real_config_agent_toml(self) -> None:
    """REQ-007: real config/agent.toml passes both validators with zero errors."""
    import os
    from pathlib import Path
    
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    from shared.config_loader import ConfigLoader
    loader = ConfigLoader(config_dir=config_dir)
    cfg = loader.load_all(strict=True)
    
    from shared.config_validator import RagConfigValidator
    rag_result = RagConfigValidator().validate(cfg)
    assert rag_result.ok is True
    assert len(rag_result.errors) == 0
    
    from shared.production_config_validator import ProductionConfigValidator
    prod_result = ProductionConfigValidator().validate(cfg)
    assert prod_result.ok is True
    assert len(prod_result.errors) == 0
```

## Compatibility considerations

- New tests use existing patterns; no changes to existing test methods.
- The integration test requires access to `config/agent.toml` — may fail if run outside the repository root.

## Security considerations

- No security impact. This is a behavioral change test for REQ-004/006/007.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_production_config_validator.py -v`
- Verify all four new tests pass.
- Static analysis: `uv run ruff check tests/shared/test_production_config_validator.py`, `uv run mypy tests/shared/test_production_config_validator.py`.

## Completion criteria

- ConfigValidationResult identity test passes.
- validate_unknown_tool_safety_tiers compatibility test passes.
- Valid-key-set-unchanged test passes.
- Integration test against real config/agent.toml passes.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/config_validator.py` source code — covered in previous row (REQ-004).
- Modifying `scripts/shared/production_config_validator.py` source code — covered in previous row (REQ-004).
- Modifying `scripts/agent/config_dataclasses.py` source code — covered in previous row (REQ-006).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add ConfigValidationResult identity test | Completed | 20260917-200258 | 20260917-200258 |  |
| 2 | Add validate_unknown_tool_safety_tiers compatibility test | Completed | 20260917-200258 | 20260917-200258 |  |
| 3 | Add valid-key-set-unchanged regression test | Completed | 20260917-200258 | 20260917-200258 |  |
| 4 | Add REQ-007 integration test against real config/agent.toml | Completed | 20260917-200259 | 20260917-200259 |  |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-200259 | 20260917-200259 |  |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-200259 | 20260917-200259 |  |

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
- **Requirement ID**: REQ-004, REQ-006, REQ-007
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_production_config_validator.py