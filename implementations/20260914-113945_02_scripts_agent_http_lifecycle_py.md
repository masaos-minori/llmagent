## Goal

Update the import statement in `scripts/agent/http_lifecycle.py` to reference the renamed
module `http_lifecycle_stderr_log_manager.py` instead of the old `http_lifecycle_stderr_log`.
Per REQ-002, REQ-003.

## Scope

- Modify exactly one file: `scripts/agent/http_lifecycle.py`
- Update a single import line: `from .http_lifecycle_stderr_log import StderrLogManager`
  → `from .http_lifecycle_stderr_log_manager import StderrLogManager`
- No behavioral change expected — only import path correction

## Assumptions

- The file `http_lifecycle_stderr_log_manager.py` has been renamed before this edit (Phase 1)
- Only one import site exists for this module; confirmed via grep search
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Single-line edit: replace the import path string only
- Preserve all surrounding code unchanged

## Alternatives considered

- Using an IDE refactoring tool: rejected — manual edit is simpler for a single import change
- Searching for additional import sites: already confirmed zero additional sites exist

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. **Locate the import statement** in `http_lifecycle.py`:
   - Current: line 43: `from .http_lifecycle_stderr_log import StderrLogManager`

2. **Replace the import path**:
   - Change `.http_lifecycle_stderr_log` → `.http_lifecycle_stderr_log_manager`

### Method

1. Read `http_lifecycle.py` to locate the exact import line
2. Edit the import path in the import statement
3. Verify no remaining references to the old module name: `rg "http_lifecycle_stderr_log[^_]" scripts/agent/http_lifecycle.py`

### Details

**Step 1 — Locate the import:**

Current content at line 43:
```python
from .http_lifecycle_stderr_log import StderrLogManager
```

**Step 2 — Replace the import path:**

After edit:
```python
from .http_lifecycle_stderr_log_manager import StderrLogManager
```

## Compatibility considerations

- Backward compatible during transition: both old and new module paths must coexist briefly
  until the rename is complete
- After rename completes, only the new import path works

## Security considerations

N/A: import path update, no security-sensitive operations.

## Rollback considerations

- Revert the import edit to restore original import path
- No data loss risk — only import path change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Import verification — confirm new import resolves | `python -c "from agent.http_lifecycle_stderr_log_manager import StderrLogManager"` | Clean (no ImportError) |
| scripts/agent/http_lifecycle.py | Type check — verify mypy passes after import update | `uv run mypy scripts/agent/http_lifecycle.py` | Clean (no errors) |
| scripts/agent/http_lifecycle.py | Static check — verify no remaining references to old module name | `rg "http_lifecycle_stderr_log[^_]" scripts/agent/http_lifecycle.py` | Zero matches |

## Completion criteria

- [ ] Import statement updated from `.http_lifecycle_stderr_log` to `.http_lifecycle_stderr_log_manager`
- [ ] No remaining references to old module name in `http_lifecycle.py`
- [ ] mypy passes on `scripts/agent/http_lifecycle.py`
- [ ] Import resolves without error

## Out of scope

- Renaming the source file (separate row)
- Updating test imports (verified clean — no direct references found)
- Adding new imports or removing unused ones

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260913-160819_missing_stderr_log_manager_file.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-222010_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-113945
- **Related target files**: scripts/agent/http_lifecycle.py
