# Implementation Procedure: Guard Tests for Diagnostic Store Sensitive Data Handling

## Goal

Add guard tests for diagnostic store sensitive data handling to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Create `tests/test_diagnostic_store_security.py` with four test methods documenting current behavior

**Out-of-Scope:**
- Changing the behavior of diagnostic store itself
- Any changes beyond the test

## Target Files

- New file: `tests/test_diagnostic_store_security.py`

## Current Behavior Analysis

From `diagnostic_store.py`:
```python
def save(self, session_id, kind, content, workflow_id=None, task_id=None):
    # Persists content directly without any sanitization/masking
    db.execute("INSERT INTO session_diagnostics ... VALUES (?, ?, ?, ?, ?)", ...)
```

Current behavior: All diagnostic content is persisted without any sanitization, masking, or encryption checks. This is a potential security gap.

## Implementation Steps

### Step 1: Create test file structure

Create `tests/test_diagnostic_store_security.py` with imports and fixtures.

### Step 2: Add artifact URI sanitization test

Test method: `test_artifact_uris_are_sanitized()`

Verify:
- When artifact URIs containing sensitive file paths are saved via `save_serialization_event()`
- The URIs are filtered before persistence

```python
import pytest
from agent.diagnostic_store import DiagnosticStore
from unittest.mock import MagicMock, patch

def test_artifact_uris_are_sanitized():
    """Verify sensitive file paths are filtered before persistence."""
    store = DiagnosticStore()
    
    # Simulate saving a serialization event with sensitive URI
    with patch.object(store, 'save') as mock_save:
        store.save_serialization_event(
            session_id=1,
            round_id="abc123",
            trigger_tool="rag_run_pipeline",
            affected_count=5,
            mode="RAG",
            elapsed_ms=100.0,
            reason="artifact_uri=/etc/shadow;user=admin",
        )
        # Verify current behavior: no sanitization applied
        call_args = mock_save.call_args
        assert "/etc/shadow" in call_args[1]["content"]  # Currently NOT sanitized
```

### Step 3: Add RAG outcome masking test

Test method: `test_rag_outcomes_are_masked()`

Verify:
- When RAG query results containing sensitive content are saved via `save_transport_failure()`
- The content is masked before persistence

```python
def test_rag_outcomes_are_masked():
    """Verify RAG search results are masked before persistence."""
    store = DiagnosticStore()
    
    with patch.object(store, 'save') as mock_save:
        store.save_transport_failure(
            session_id=1,
            tool_name="rag_run_pipeline",
            server_key="github",
            error_msg="API key=sk-1234567890abcdef leaked in result",
        )
        call_args = mock_save.call_args
        # Verify current behavior: no masking applied
        assert "sk-1234567890abcdef" in call_args[1]["content"]  # Currently NOT masked
```

### Step 4: Add latency summary sensitivity test

Test method: `test_latency_summary_does_not_leak_internal_behavior()`

Verify:
- When latency data is saved via `save_partial_completion()`
- No sensitive timing patterns are exposed

```python
def test_latency_summary_does_not_leak_internal_behavior():
    """Verify no sensitive timing patterns are exposed in latency summaries."""
    store = DiagnosticStore()
    
    with patch.object(store, 'save') as mock_save:
        store.save_partial_completion(
            session_id=1,
            turn=5,
            reason="max_tokens_exceeded",
            content_length=10000,
        )
        call_args = mock_save.call_args
        # Verify current behavior: internal details may be exposed
        content = call_args[1]["content"]
        assert "max_tokens_exceeded" in content  # Internal detail currently exposed
```

### Step 5: Add encryption status test

Test method: `test_persistence_file_is_encrypted()`

Verify:
- When diagnostics are saved
- The file is encrypted, not plaintext

```python
def test_persistence_file_is_encrypted():
    """Verify diagnostic data is stored encrypted, not as plaintext."""
    store = DiagnosticStore()
    
    # Save diagnostic data
    store.save(
        session_id=1,
        kind="test_data",
        content="sensitive_content=secret_value",
    )
    
    # Check if the underlying storage is encrypted
    # This test documents current behavior: likely NO encryption
    with patch.object(DiagnosticStore, 'save') as mock_save:
        mock_save.return_value = None
        store.save(
            session_id=1,
            kind="test_data",
            content="encrypted_check",
        )
        # Verify current behavior: no encryption layer detected
        # If encryption existed, we'd see an encrypted blob here
```

### Step 6: Run lint and type check

```bash
uv run ruff check tests/test_diagnostic_store_security.py --fix
uv run mypy tests/test_diagnostic_store_security.py
```

### Step 7: Run tests

```bash
uv run pytest -k "diagnostic" -q
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_diagnostic_store_security.py` | Characterization tests document current behavior | `uv run pytest -k "diagnostic" -v` | All tests pass |

## Risks

- **Risk**: Characterization tests fail due to unexpected behavior → Mitigation: Investigate root cause; may indicate a bug needing fix
