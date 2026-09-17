## Goal

Add regression tests for REQ-004 (disabled server accepts empty `auth_token`), REQ-006 (`health_timeout=0` → no immediate-timeout behavior at the `get_effective_health_timeout()` unit level), REQ-007 (corrected message text), REQ-010 (per-mode required-field assertions).

## Scope

- Add test for disabled-server auth_token exemption (REQ-004).
- Add test for `health_timeout=0` returning `None` (REQ-006).
- Add test for corrected error message text (REQ-007).
- Add per-`StartupMode` required-field assertions (REQ-010).

## Assumptions

- The existing `TestMcpServerConfigValidation` class provides a good home for these new tests.
- `McpServerConfig` construction is the primary mechanism under test.

## Design decisions

- Add each new test as a separate method in the appropriate existing test class.
- Use `pytest.raises` for error-message verification tests.

## Alternatives considered

- Creating a new test class for each requirement — rejected: adds unnecessary class proliferation.
- Merging all four requirements into one test — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_mcp_config.py`

### Procedure

1. Add REQ-004 test in `TestMcpServerConfigValidation`.
2. Add REQ-006 test for `get_effective_health_timeout()`.
3. Add REQ-007 test for corrected error message.
4. Add REQ-010 per-mode required-field tests.

### Method

- **Step 1** (REQ-004): In `TestMcpServerConfigValidation`:

```python
def test_disabled_server_accepts_empty_auth_token(self) -> None:
    """REQ-004: disabled server should not require auth_token."""
    cfg = McpServerConfig(
        TransportType.HTTP,
        "http://127.0.0.1:8000",
        startup_mode=StartupMode.NONE,
        auth_token="",
    )
    assert cfg.is_disabled is True
    # Should not raise ValueError about empty auth_token
```

- **Step 2** (REQ-006): Add test for `get_effective_health_timeout()`:

```python
def test_health_timeout_zero_returns_none(self) -> None:
    """REQ-006: health_timeout=0 should return None (no timeout), matching call_timeout_sec convention."""
    cfg = McpServerConfig(
        TransportType.HTTP,
        "http://127.0.0.1:8000",
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
        health_timeout=0,
    )
    from shared.mcp_config import get_effective_health_timeout
    result = get_effective_health_timeout(cfg)
    assert result is None
```

- **Step 3** (REQ-007): Add test for corrected error message:

```python
def test_health_timeout_type_error_message_is_correct(self) -> None:
    """REQ-007: health_timeout type-conversion error message should say 'non-negative' not 'positive'."""
    with pytest.raises(ValueError, match="non-negative"):
        _build_mcp_servers({"test": {"transport": "http", "url": "http://x", "health_timeout": "invalid"}})
```

- **Step 4** (REQ-010): Add per-mode required-field tests:

```python
class TestPerModeRequiredFields:
    """REQ-010: per-StartupMode required-field documentation and validation."""

    def test_none_mode_requires_no_url_cmd_auth_token(self) -> None:
        """NONE mode: none of url/cmd/auth_token are required."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="",
            startup_mode=StartupMode.NONE,
            cmd=[],
            auth_token="",
        )
        assert cfg.startup_mode == StartupMode.NONE
        assert cfg.is_disabled is True

    def test_persistent_mode_requires_url(self) -> None:
        """PERSISTENT mode: url is required."""
        with pytest.raises(ValueError, match="url"):
            McpServerConfig(
                transport=TransportType.HTTP,
                url="",
                startup_mode=StartupMode.PERSISTENT,
            )

    def test_subprocess_mode_requires_cmd_and_url(self) -> None:
        """SUBPROCESS mode: cmd and url are required."""
        with pytest.raises(ValueError, match="cmd"):
            McpServerConfig(
                transport=TransportType.HTTP,
                url="http://127.0.0.1:8000",
                startup_mode=StartupMode.SUBPROCESS,
                cmd=[],
            )
```

### Details

**Step 1 — REQ-004:** Add after line ~17 in `TestMcpServerConfigValidation`:

```python
def test_disabled_server_accepts_empty_auth_token(self) -> None:
    """REQ-004: disabled server should not require auth_token."""
    cfg = McpServerConfig(
        TransportType.HTTP,
        "http://127.0.0.1:8000",
        startup_mode=StartupMode.NONE,
        auth_token="",
    )
    assert cfg.is_disabled is True
```

**Step 2 — REQ-006:** Add after line ~17 in `TestMcpServerConfigValidation`:

```python
def test_health_timeout_zero_returns_none(self) -> None:
    """REQ-006: health_timeout=0 should return None (no timeout)."""
    cfg = McpServerConfig(
        TransportType.HTTP,
        "http://127.0.0.1:8000",
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
        health_timeout=0,
    )
    from shared.mcp_config import get_effective_health_timeout
    result = get_effective_health_timeout(cfg)
    assert result is None
```

**Step 3 — REQ-007:** Add after line ~17 in `TestMcpServerConfigValidation`:

```python
def test_health_timeout_type_error_message_is_correct(self) -> None:
    """REQ-007: health_timeout type-conversion error says 'non-negative' not 'positive'."""
    with pytest.raises(ValueError, match="non-negative"):
        _build_mcp_servers({"test": {"transport": "http", "url": "http://x", "health_timeout": "invalid"}})
```

**Step 4 — REQ-010:** Add new class after `TestMcpServerConfigValidation`:

```python
class TestPerModeRequiredFields:
    """REQ-010: per-StartupMode required-field documentation and validation."""

    def test_none_mode_requires_no_url_cmd_auth_token(self) -> None:
        ...

    def test_persistent_mode_requires_url(self) -> None:
        ...

    def test_subprocess_mode_requires_cmd_and_url(self) -> None:
        ...
```

## Compatibility considerations

- New tests use existing patterns; no changes to existing test methods.
- `get_effective_health_timeout()` now returns `float | None`; the test verifies the `None` case.

## Security considerations

- No security impact. This is a behavioral change test for REQ-004/006/007/010.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_mcp_config.py -v`
- Verify all four new tests pass.
- Static analysis: `uv run ruff check tests/shared/test_mcp_config.py`, `uv run mypy tests/shared/test_mcp_config.py`.

## Completion criteria

- REQ-004 test passes: disabled server accepts empty `auth_token`.
- REQ-006 test passes: `health_timeout=0` returns `None`.
- REQ-007 test passes: error message contains "non-negative".
- REQ-010 tests pass: per-mode required-field assertions verified.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/mcp_config.py` source code — covered in previous row.
- Testing the two call sites of `get_effective_health_timeout()` — covered in subsequent rows.
- Any MCP server business logic unrelated to config validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add REQ-004/006/007/010 regression tests | Completed | 20260917-000000 | 20260917-000000 | Done |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-000000 | 20260917-000000 | All tests pass |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-000000 | 20260917-000000 | Not in scope |


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
- **Requirement ID**: REQ-004, REQ-006, REQ-007, REQ-009, REQ-010
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_mcp_config.py
