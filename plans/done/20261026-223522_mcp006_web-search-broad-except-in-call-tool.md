## Goal
Improve exception type capture in `call_tool` endpoint: replace broad `except Exception` with specific exception types and ensure audit log captures the actual exception type.

## Priority
Medium

## Scope
- **In-Scope**: Replace `except Exception:` with specific exception types in `call_tool`; update audit log to capture actual exception type
- **Out-of-Scope**: Changes to the audit log format itself; changes to how `WebSearchUpstreamError` subclasses are handled
- **Dependencies**: N/A: none

## Background
The `call_tool` endpoint in `web_search_server.py` (lines 244-310) handles tool dispatch with specific exception handlers:

```python
except WebSearchUpstreamError as e:
    ...
    raise
except BrowserAuthorizationError:
    ...
    raise
except Exception:
    outcome = "error"
    error_type = "unexpected_error"
    latency_ms = (time.perf_counter() - t0) * 1000
    raise
```

The `finally` block (lines 298-310) always fires and logs the audit entry regardless of whether an exception was raised.

## Problem
The `except Exception` clause at line 293 catches ALL non-specific exceptions, including:
1. `RuntimeError` — could indicate configuration errors, missing dependencies, or unexpected state
2. `ValueError` — could indicate malformed input or data corruption
3. `TypeError` — could indicate type mismatches in the dispatch table
4. `ImportError` — could indicate missing dependencies
5. Any other unexpected exception

While the exception is re-raised (so the HTTP response is still correct), the `error_type` is always `"unexpected_error"` regardless of the actual exception type. This means:
1. The audit log loses information about the actual failure mode.
2. Monitoring/alerting systems cannot distinguish between different types of failures.
3. Debugging requires tracing through the stack trace rather than reading the audit log.

## Reason for Change
The broad `except Exception` clause masks the actual exception type, making it impossible to distinguish between different failure modes in the audit log. This reduces observability and makes debugging harder.

## Implementation Intent
Replace the broad `except Exception` with specific exception types that should be caught, or remove the catch entirely and let the exception propagate naturally. If catching is necessary, use a more specific exception type.

## Requirements
- `REQ-001`: Audit log captures the actual exception type, not just `"unexpected_error"`
- `REQ-002`: Specific exception types are handled differently in the audit log
- `REQ-003`: No silent swallowing of exceptions

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Replace `except Exception:` with specific exception types; update audit log | REQ-001, REQ-002 | Confirmed: `except Exception` at line 293 sets `error_type = "unexpected_error"` for all non-specific exceptions (checked in Step 3) | Unit test for exception type capture | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/mcp_servers/web_search/test_web_search_server.py | Verify existing exception handling patterns | REQ-001 |

## Acceptance Criteria
- Audit log captures the actual exception type, not just `"unexpected_error"` (REQ-001)
- Specific exception types are handled differently in the audit log (REQ-002)
- No silent swallowing of exceptions (REQ-003)

## Tests
- Unit test: verify specific exception types are captured in audit log (REQ-001)
- Integration test: verify audit log distinguishes between different failure modes (REQ-002)
- Regression test: ensure existing exception handling behavior is preserved (REQ-003)

## Documentation Impact
Update `call_tool` docstring to document the exception handling strategy.

## Assumptions
- The `finally` block should continue to fire for all cases (including exceptions) to ensure audit logging
- The `error_type` variable should be set to the actual exception class name (e.g., `"RuntimeError"`, `"ValueError"`) instead of `"unexpected_error"`
- The `except Exception` clause should be replaced with specific exception types that are known to occur in the dispatch path

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should the `finally` block skip audit logging when an exception is raised (since the specific handler already logged it)? | Need to check if specific handlers also log audit entries | Review web_search_server.py audit logic | False |
| UNK-02 | Is there a risk of double-audit entries when both the `except` handler and `finally` block fire? | Need to verify audit log deduplication | Check audit_log implementation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Replace `except Exception:` with `except (RuntimeError, ValueError, TypeError, ImportError):` and set `error_type` to the actual exception class name using `type(e).__name__`
- **Rationale**: Using `type(e).__name__` provides more granular error classification in the audit log without requiring separate handlers for each exception type.
- **Alternative considered**: Removing the `except Exception` clause entirely — this would let all exceptions propagate naturally but would lose the `latency_ms` calculation for error cases.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/web_search/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/web_search/test_web_search_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Replace `except Exception:` with `except Exception as e:` and set `error_type = type(e).__name__` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/web_search/web_search_server.py)
   - [ ] Update `call_tool` docstring to document the exception handling strategy (Requirement ID: REQ-001; File Path: scripts/mcp_servers/web_search/web_search_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/web_search/web_search_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Unit test | uv run pytest tests/mcp_servers/web_search/test_web_search_server.py -v | Test passes; exception type captured in audit log |
| scripts/mcp_servers/web_search/web_search_server.py | Lint check | uv run ruff check scripts/mcp_servers/web_search/web_search_server.py | Clean (no findings) |
| scripts/mcp_servers/web_search/web_search_server.py | Type check | uv run mypy scripts/mcp_servers/web_search/web_search_server.py | Clean (no type errors) |

## Risks
- **Risk**: Replacing `except Exception:` with specific exception types may miss some exceptions → **Mitigation**: Keep `except Exception:` as a fallback after specific handlers, but set `error_type` to the actual exception class name
- **Risk**: Using `type(e).__name__` may expose internal implementation details in the audit log → **Mitigation**: Map common exception types to user-friendly names (e.g., `"RuntimeError"` → `"internal_error"`)

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — improve exception type capture | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add unit test and run checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-220730_mcp006-web-search-broad-except-in-call-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-223522
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/web_search/web_search_server.py | Phase 2 | Exception type captured | Unit test for exception type capture | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/web_search/web_search_server.py | Phase 2 | Different failure modes distinguished | Integration test for failure modes | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/web_search/web_search_server.py | Phase 3 | No silent swallowing | Regression test for exception handling | Needs confirmation |
