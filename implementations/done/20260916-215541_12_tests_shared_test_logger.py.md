## Goal

Add a direct unit test for the new `attach_redaction_filter`-style helper introduced in `scripts/shared/logger.py`.

## Scope

- Add a test in `tests/shared/test_logger.py` for the new `attach_redaction_filter()` helper.

## Assumptions

- The test can create a mock `logging.Logger` and verify the filter is attached.
- The existing test infrastructure supports mocking `logging.Logger`.

## Design decisions

- Add a single test method in the appropriate test class that verifies the helper attaches `_RedactionFilter` and that a subsequent log call redacts a registered secret.

## Alternatives considered

- Creating a new test class for this single test — rejected: adds unnecessary class proliferation.
- Merging this test with the existing `TestContextFilter` or `TestJsonFormatter` classes — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_logger.py`

### Procedure

Add a unit test for the new `attach_redaction_filter()` helper.

### Method

- **Step 1**: Add a test method to the appropriate test class:

```python
class TestAttachRedactionFilter:
    """REQ-006/REQ-010: unit test for the attach_redaction_filter helper."""

    def test_attach_redaction_filter_adds_filter(self) -> None:
        """The helper attaches _RedactionFilter to the given logger."""
        # ... implement using mock Logger
        pass

    def test_attached_filter_redacts_registered_secret(self) -> None:
        """A log record through the filtered logger redacts a registered secret."""
        # ... implement using mock Logger + registered secret
        pass
```

### Details

**Step 1 — Add tests for the helper:**

Add after the existing test classes in `tests/shared/test_logger.py`:

```python
class TestAttachRedactionFilter:
    """REQ-006/REQ-010: unit test for the attach_redaction_filter helper."""

    @patch.object(logging.Logger, 'addFilter')
    def test_attach_redaction_filter_adds_filter(self, mock_add_filter: MagicMock) -> None:
        """The helper attaches _RedactionFilter to the given logger."""
        from shared.logger import attach_redaction_filter
        logger = logging.getLogger("test.attach_redaction")
        attach_redaction_filter(logger)
        mock_add_filter.assert_called_once()
        assert isinstance(mock_add_filter.call_args[0][0], _RedactionFilter)

    def test_attached_filter_redacts_registered_secret(self) -> None:
        """A log record through the filtered logger redacts a registered secret."""
        import io
        from shared.logger import attach_redaction_filter, register_secret
        
        logger = logging.getLogger("test.redact")
        handler = logging.StreamHandler(io.StringIO())
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Register a secret and attach the filter
        register_secret("super-secret-value-should-not-leak")
        attach_redaction_filter(logger)
        
        # Emit a log message containing the secret
        logger.info("Token: super-secret-value-should-not-leak")
        
        # Verify the secret is redacted in the output
        output = handler.stream.getvalue()
        assert "super-secret-value-should-not-leak" not in output
        assert "***REDACTED***" in output
```

## Compatibility considerations

- New tests use existing patterns; no changes to existing test methods.

## Security considerations

- No security impact. This is a behavioral change test for REQ-006.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_logger.py -v`
- Verify both new tests pass.
- Static analysis: `uv run ruff check tests/shared/test_logger.py`, `uv run mypy tests/shared/test_logger.py`.

## Completion criteria

- Tests verify `attach_redaction_filter()` attaches `_RedactionFilter`.
- Tests verify the attached filter redacts registered secrets.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/logger.py` source code — covered in previous row (REQ-006).
- Testing the redaction behavior on `http_transport.py` or `tool_transport_invoker.py` — covered in subsequent rows.
- Any MCP server business logic unrelated to the logger helper.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add unit tests for attach_redaction_filter helper | Completed | 20260917-191200 | 20260917-191200 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-191200 | 20260917-191200 |  |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-191200 | 20260917-191200 |  |

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
- **Requirement ID**: REQ-006, REQ-010
- **Source issue**: issues/20260914-103224_mcpagent06_http-retry-backoff-safe-diagnostics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-124248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_logger.py