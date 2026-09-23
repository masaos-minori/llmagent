## Goal

Update stale reference to `models_config.py` in comment within `scripts/mcp_servers/github/github_models.py`.

## Scope

- **In-Scope**: Updating 1 stale reference (line 7) in `scripts/mcp_servers/github/github_models.py`
- **Out-of-Scope**: Renaming `github_models_config.py` to `models_config.py`, modifying import structures, changing public/runtime interfaces, database schema changes

## Assumptions

- `github_models_config.py` exists in `scripts/mcp_servers/github/` and contains the expected definitions (exception classes, `DEFAULT_PER_PAGE` constant, `GitHubConfig` dataclass)
- The stale reference is the only one in this file
- The comment describes the module's exports and should be updated to reflect the correct filename

## Design decisions

- The stale reference uses the incorrect filename pattern (`models_config.py`) and refers to the same actual file (`github_models_config.py`)
- No import structure changes needed since this is a comment update only

## Alternatives considered

- Renaming `github_models_config.py` to `models_config.py`: rejected because it would break existing imports and is out of scope

## Implementation

### Target file

`scripts/mcp_servers/github/github_models.py`

### Procedure

1. Verify `github_models_config.py` exists and contains expected definitions
2. Update line 7: `models_config.py` → `github_models_config.py` in the comment
3. Verify zero stale `models_config.py` references remain via `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/`

### Method

Use Edit tool to replace the exact string in the specified line.

### Details

#### REQ-004: Line 7

**Before:**
```python
  models_config.py        — GitHubConfig dataclass, domain exceptions, DEFAULT_PER_PAGE
```

**After:**
```python
  github_models_config.py — GitHubConfig dataclass, domain exceptions, DEFAULT_PER_PAGE
```

## Compatibility considerations

- This change only affects a comment; no runtime behavior changes
- The referenced file `github_models_config.py` must exist and contain the expected definitions

## Security considerations

- No security implications; this is a comment update

## Rollback considerations

- Revert the string replacement to restore the original stale comment
- No code changes to revert

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_models.py` | Comment accuracy verification | `grep -n 'models_config\.py' scripts/mcp_servers/github/github_models.py` | Zero matches |
| `scripts/mcp_servers/github/github_models.py` | Syntax check | `python -m py_compile scripts/mcp_servers/github/github_models.py` | No syntax errors |

## Completion criteria

- [ ] Line 7 no longer contains `models_config.py` reference
- [ ] Line 7 now correctly references `github_models_config.py`
- [ ] `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/` returns zero matches
- [ ] Python syntax check passes

## Out of scope

- Renaming `github_models_config.py` to `models_config.py`
- Modifying import structures
- Changing public/runtime interfaces
- Database schema changes
- Other files not listed in Implementation Target Files

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `github_models_config.py` exists and contains expected definitions | Completed | — | — |  |
| 2 | Update line 7 in `scripts/mcp_servers/github/github_models.py` | Completed | — | — |  |
| 3 | Verify zero stale `models_config.py` references remain | Completed | — | — |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260923-100002_p003_github_mcp_file_path_inconsistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-154518_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-155331
- **Related target files**: scripts/mcp_servers/github/github_models.py