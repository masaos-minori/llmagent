## Goal

Rewrite the nested `{"rag": {...}}` fixtures (`TestRagConfigValidator`, every test method) to the canonical flat shape per REQ-005; add the REQ-007 integration-test half for `RagConfigValidator` against the real `config/agent.toml`.

## Scope

- Modify `tests/shared/test_config_validator.py`: rewrite all fixtures and test methods in `TestRagConfigValidator`; add one integration test.

## Assumptions

- The canonical flat RAG shape has top-level keys like `embed_url`, `chunk_size`, etc., matching `config/agent.toml`'s actual structure.
- Every test method in `TestRagConfigValidator` currently constructs `{"rag": {...}}` (confirmed by direct read: `test_ok_no_errors`, `test_use_rrf_false_warning`, `test_use_rrf_true_no_warning`, `test_multiple_errors`, and the semantic-cache-removed-key tests).

## Design decisions

- Replace each `{"rag": {...}}` fixture with a flat dict containing the same RAG keys at the top level.
- Rename the fixture variable from `rag_cfg` to `rag_flat_cfg` for clarity.
- Update all assertions to reflect the new shape.

## Alternatives considered

- Creating a separate fixture for the flat shape — rejected: would require duplicating all existing fixture logic.
- Using `pytest.param` to parameterize both shapes — rejected: adds unnecessary complexity; the flat shape is the only correct one post-fix.

## Implementation

### Target file

`tests/shared/test_config_validator.py`

### Procedure

1. Rewrite the `rag_cfg` fixture in `TestRagConfigValidator` to use the flat shape.
2. Rewrite each test method to use the flat shape.
3. Add the REQ-007 integration test.

### Method

- **Step 1**: Rewrite the `rag_cfg` fixture:

```python
# Before:
@pytest.fixture
def rag_cfg(self) -> dict[str, object]:
    return {"rag": {
        "embed_url": "http://localhost:8000/embed",
        "chunk_size": 512,
        "use_rrf": False,
    }}

# After:
@pytest.fixture
def rag_flat_cfg(self) -> dict[str, object]:
    """REQ-005: canonical flat RAG shape matching config/agent.toml."""
    return {
        "embed_url": "http://localhost:8000/embed",
        "chunk_size": 512,
        "use_rrf": False,
    }
```

- **Step 2**: Rewrite each test method:

```python
# Before:
class TestRagConfigValidator:
    def test_ok_no_errors(self) -> None:
        result = RagConfigValidator().validate(self.rag_cfg)
        assert result.ok is True
        assert len(result.errors) == 0
    
    def test_use_rrf_false_warning(self) -> None:
        cfg = self.rag_cfg.copy()
        cfg["rag"]["use_rrf"] = False
        result = RagConfigValidator().validate(cfg)
        assert len(result.warnings) > 0
    
    # ... etc.

# After:
class TestRagConfigValidator:
    def test_ok_no_errors(self) -> None:
        result = RagConfigValidator().validate(self.rag_flat_cfg)
        assert result.ok is True
        assert len(result.errors) == 0
    
    def test_use_rrf_false_warning(self) -> None:
        cfg = self.rag_flat_cfg.copy()
        cfg["use_rrf"] = False
        result = RagConfigValidator().validate(cfg)
        assert len(result.warnings) > 0
    
    # ... etc.
```

- **Step 3**: Add the REQ-007 integration test:

```python
@pytest.mark.integration
def test_integration_rag_validator_real_config(self) -> None:
    """REQ-007: real config/agent.toml passes RagConfigValidator with zero errors."""
    from pathlib import Path
    from shared.config_loader import ConfigLoader
    from shared.config_validator import RagConfigValidator
    
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    loader = ConfigLoader(config_dir=config_dir)
    cfg = loader.load_all(strict=True)
    
    result = RagConfigValidator().validate(cfg)
    assert result.ok is True
    assert len(result.errors) == 0
```

### Details

**Step 1 — Rewrite the fixture:**

Replace lines ~20-30 in `tests/shared/test_config_validator.py`:

```python
@pytest.fixture
def rag_flat_cfg(self) -> dict[str, object]:
    """REQ-005: canonical flat RAG shape matching config/agent.toml."""
    return {
        "embed_url": "http://localhost:8000/embed",
        "chunk_size": 512,
        "use_rrf": False,
    }
```

**Step 2 — Rewrite each test method:**

Replace each test method in `TestRagConfigValidator`:

```python
class TestRagConfigValidator:
    def test_ok_no_errors(self) -> None:
        result = RagConfigValidator().validate(self.rag_flat_cfg)
        assert result.ok is True
        assert len(result.errors) == 0
    
    def test_use_rrf_false_warning(self) -> None:
        cfg = self.rag_flat_cfg.copy()
        cfg["use_rrf"] = False
        result = RagConfigValidator().validate(cfg)
        assert len(result.warnings) > 0
    
    def test_use_rrf_true_no_warning(self) -> None:
        cfg = self.rag_flat_cfg.copy()
        cfg["use_rrf"] = True
        result = RagConfigValidator().validate(cfg)
        assert len(result.warnings) == 0
    
    def test_multiple_errors(self) -> None:
        cfg = {}  # Empty config should produce errors
        result = RagConfigValidator().validate(cfg)
        assert result.ok is False
        assert len(result.errors) > 0
    
    # ... etc.
```

**Step 3 — Add integration test:**

Add after the existing test class:

```python
@pytest.mark.integration
def test_integration_rag_validator_real_config(self) -> None:
    """REQ-007: real config/agent.toml passes RagConfigValidator with zero errors."""
    from pathlib import Path
    from shared.config_loader import ConfigLoader
    from shared.config_validator import RagConfigValidator
    
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    loader = ConfigLoader(config_dir=config_dir)
    cfg = loader.load_all(strict=True)
    
    result = RagConfigValidator().validate(cfg)
    assert result.ok is True
    assert len(result.errors) == 0
```

## Compatibility considerations

- Renamed fixture from `rag_cfg` to `rag_flat_cfg` — may break any external code using this fixture name (unlikely since it's internal to the test module).
- All test assertions remain unchanged (same behavior, different input shape).

## Security considerations

- No security impact. This is a behavioral change test for REQ-005/007.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_config_validator.py -v`
- Verify all rewritten tests pass with the flat shape.
- Static analysis: `uv run ruff check tests/shared/test_config_validator.py`, `uv run mypy tests/shared/test_config_validator.py`.

## Completion criteria

- All fixtures in `TestRagConfigValidator` use the flat shape.
- All test methods updated to use the flat shape.
- Integration test added for REQ-007.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/config_validator.py` source code — covered in previous row (REQ-004).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite rag_cfg fixture to flat shape | Completed | 20260917-201328 | 20260917-201328 |  |
| 2 | Rewrite each test method in TestRagConfigValidator | Completed | 20260917-201328 | 20260917-201328 |  |
| 3 | Add REQ-007 integration test | Completed | 20260917-201328 | 20260917-201328 |  |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-201338 | 20260917-201338 |  |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-201338 | 20260917-201338 |  |

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
- **Requirement ID**: REQ-005, REQ-007
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_config_validator.py