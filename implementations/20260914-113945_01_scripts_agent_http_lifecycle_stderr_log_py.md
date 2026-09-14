## Goal

Rename `scripts/agent/http_lifecycle_stderr_log.py` to `http_lifecycle_stderr_log_manager.py`
to align with the naming convention used by sibling modules containing Manager classes. Per
REQ-001.

## Scope

- Rename exactly one file: `scripts/agent/http_lifecycle_stderr_log.py` →
  `scripts/agent/http_lifecycle_stderr_log_manager.py`
- Update module docstring header in the renamed file to reflect the new filename
- No behavioral change expected — purely cosmetic rename

## Assumptions

- Only one import site exists (`http_lifecycle.py:43`); confirmed via grep search showing zero
  matches for `http_lifecycle_stderr_log_manager` elsewhere
- No external callers depend on the old module path
- The rename is purely cosmetic — no behavioral changes needed
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Use `git mv` for the rename to preserve git history (track as rename, not delete+create)
- Update module docstring header to reflect the new filename
- Keep class definition identical — no code changes inside the file

## Alternatives considered

- Using `mv` instead of `git mv`: rejected — `git mv` preserves rename history in git log
- Updating the docstring separately from the rename: combined into single step for atomicity

## Implementation

### Target file

`scripts/agent/http_lifecycle_stderr_log.py`

### Procedure

1. **Rename the file using git mv:**
   ```bash
   git mv scripts/agent/http_lifecycle_stderr_log.py scripts/agent/http_lifecycle_stderr_log_manager.py
   ```

2. **Update module docstring header** in the renamed file:
   - Before: `"""scripts/agent/http_lifecycle_stderr_log.py\n\nStderr log file management for HTTP subprocess MCP servers."""`
   - After: `"""scripts/agent/http_lifecycle_stderr_log_manager.py\n\nStderr log file management for HTTP subprocess MCP servers."""`

### Method

1. Run `git mv` to rename the file
2. Read the renamed file to identify the module docstring header
3. Edit the docstring header to reflect the new filename
4. Verify no remaining references to the old module name: `rg "http_lifecycle_stderr_log[^_]" scripts/`

### Details

**Step 1 — Rename:**

```bash
git mv scripts/agent/http_lifecycle_stderr_log.py scripts/agent/http_lifecycle_stderr_log_manager.py
```

**Step 2 — Update docstring:**

Before:
```python
"""scripts/agent/http_lifecycle_stderr_log.py

Stderr log file management for HTTP subprocess MCP servers."""
```

After:
```python
"""scripts/agent/http_lifecycle_stderr_log_manager.py

Stderr log file management for HTTP subprocess MCP servers."""
```

## Compatibility considerations

- No production compatibility concerns — rename only affects internal module path
- External callers (if any) will fail at import time; can be addressed separately
- Test imports verified clean — no direct references to old module name found

## Security considerations

N/A: cosmetic rename, no security-sensitive operations.

## Rollback considerations

- Revert with `git revert` if needed
- No data loss risk — only file rename and docstring update

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_stderr_log_manager.py | Import verification — confirm module can be imported | `python -c "from agent.http_lifecycle_stderr_log_manager import StderrLogManager"` | Clean (no ImportError) |
| scripts/agent/http_lifecycle.py | Type check — verify mypy passes after import update | `uv run mypy scripts/agent/http_lifecycle.py` | Clean (no errors) |
| scripts/agent/http_lifecycle_stderr_log_manager.py | Static check — verify no remaining references to old module name | `rg "http_lifecycle_stderr_log[^_]" scripts/` | Zero matches |
| scripts/agent/http_lifecycle_stderr_log_manager.py | Unit test — verify StderrLogManager functionality preserved | `uv run pytest tests/ -k stderr -x -q` | All tests pass |

## Completion criteria

- [ ] File renamed from `http_lifecycle_stderr_log.py` to `http_lifecycle_stderr_log_manager.py`
- [ ] Module docstring header updated to reflect new filename
- [ ] Import in `http_lifecycle.py` updated to point to new module path
- [ ] No broken imports after rename
- [ ] Code passes type checking (mypy) without errors

## Out of scope

- Refactoring other http_lifecycle modules
- Adding new stderr log management functionality
- Updating test imports (verified clean — no direct references found)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docstring update included in Phase 2 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-160819_missing_stderr_log_manager_file.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-222010_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-113945
- **Related target files**: scripts/agent/http_lifecycle_stderr_log.py
