# ruff BLE001: tools/check_all_docstrings.py line 62 catches all exceptions

## Priority
Medium

## Summary
`tools/check_all_docstrings.py:62` uses `except Exception as e:` which triggers
ruff BLE001 (catching all exceptions without specific handling). This is a false
positive — the broad catch is intentional because `Path.read_text()` can raise
various OS-level errors (PermissionError, FileNotFoundError, etc.) and the code
handles all of them uniformly by appending a read-error message.

## Reason for Change
The broad exception handler is deliberate: `Path.read_text()` can raise multiple
OS-level errors and there is no meaningful distinction between them at this level.
However, ruff flags this as a potential bug because catching all exceptions can
mask unexpected errors.

## Target Files
- `tools/check_all_docstrings.py:62`

## Current Code
```python
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        issues.append(f"read error: {e}")
        return issues
```

## Options
1. Add `# noqa: BLE001` suppression with em-dash justification (per `rules/coding.md`
   §Suppression governance)
2. Narrow to specific exception types: `except (OSError, PermissionError) as e:`
3. Use `except OSError as e:` (covers most OS-level errors including PermissionError)

## Acceptance Criteria
- Pre-commit hook passes without BLE001 errors on this file
- Exception handling remains correct for all OS-level errors from `Path.read_text()`

## Notes
This is a pre-existing issue unrelated to any recent feature changes. The broad
exception handler has been in place since the file was created.
