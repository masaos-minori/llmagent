## Goal
Narrow the broad `except Exception` handler in `tools/check_all_docstrings.py:62` to `(OSError, UnicodeDecodeError)` to satisfy ruff's BLE001 rule while preserving correct behavior for all expected failure modes from `Path.read_text()`.

## Scope
**In-Scope**:
- Modify `tools/check_all_docstrings.py` line 62: `except Exception as e:` → `except (OSError, UnicodeDecodeError) as e:`
- Verify ruff BLE001 passes
- Verify existing tests pass

**Out-of-Scope**:
- Any other BLE001 violations in the codebase
- Behavioral changes to the tool
- New test coverage

## Assumptions
- `Path.read_text()` only raises `OSError` (and subclasses like PermissionError, FileNotFoundError) or `UnicodeDecodeError` — confirmed by Python docs
- No other code paths in this function could raise different exception types that need handling
- The existing behavior (append error message, return early) is correct and does not need adjustment

## Design decisions
- Narrow to `(OSError, UnicodeDecodeError)` rather than adding a stub `# noqa: BLE001`: narrowing eliminates the lint violation permanently without suppressing it
- Do not add additional exception types beyond what `Path.read_text()` can raise per Python documentation

## Alternatives considered
- Adding `# noqa: BLE001` comment: suppresses the warning but leaves the overly broad handler in place; rejected because narrowing is trivial and more correct
- Catching `Exception` with explicit re-raise of unexpected types: adds unnecessary complexity for no benefit given `Path.read_text()`'s documented exception contract

## Implementation

### Target file
`tools/check_all_docstrings.py`

### Procedure
1. Open `tools/check_all_docstrings.py`
2. Locate line 62 containing `except Exception as e:`
3. Replace with `except (OSError, UnicodeDecodeError) as e:`
4. Save the file

### Method
Direct source edit — single-line replacement.

### Details
```python
# Before:
except Exception as e:

# After:
except (OSError, UnicodeDecodeError) as e:
```

## Compatibility considerations
- `OSError` and `UnicodeDecodeError` are built-in exception types available since Python 2.6; no compatibility concern
- Behavior is identical: both handlers append an error message and return early

## Security considerations
- Narrowing the exception handler improves security posture by preventing accidental swallowing of unexpected exceptions (e.g., `KeyboardInterrupt`, `SystemExit`)

## Rollback considerations
- Revert to original `except Exception as e:` if the narrowed handler causes a regression in any test or runtime scenario

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_all_docstrings.py | Static lint check | `uv run ruff check --select=BLE001 tools/check_all_docstrings.py` | Clean (no errors) |
| tools/check_all_docstrings.py | Regression test | `uv run pytest` | All existing tests pass |

## Out of scope
- Fixing BLE001 violations in other files (separate plan items)
- Adding new test cases for the narrowed handler
- Modifying any other exception handlers in the codebase

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260815-011925_ble001_check_all_docstrings.md
- Source requirement: requires/20260815-064046_require.md
- Source plan: plans/20260815-073549_plan.md
- Source implementation procedure: N/A
- Generated at: 20260815-075208
- Related target files: tools/check_all_docstrings.py
