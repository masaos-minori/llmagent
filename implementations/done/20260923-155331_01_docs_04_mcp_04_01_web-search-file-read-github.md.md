## Goal

Update stale references to `models_config.py` that should point to `github_models_config.py` in `docs/04_mcp_04_01_web-search-file-read-github.md`.

## Scope

- **In-Scope**: Updating 2 stale references (line 163 and line 173) in `docs/04_mcp_04_01_web-search-file-read-github.md`
- **Out-of-Scope**: Renaming `github_models_config.py` to `models_config.py`, modifying import structures, changing public/runtime interfaces, database schema changes

## Assumptions

- `github_models_config.py` exists in `scripts/mcp_servers/github/` and contains the expected definitions (exception classes, `DEFAULT_PER_PAGE` constant, `GitHubConfig` dataclass)
- The two stale references are the only ones in this file

## Design decisions

- All stale references use the same incorrect filename pattern (`models_config.py`) and refer to the same actual file (`github_models_config.py`)
- Fixing only one would leave the others inconsistent — all 4 references must be updated together
- No import structure changes needed since `github_models.py` already re-exports from `github_models_config.py`

## Alternatives considered

- Renaming `github_models_config.py` to `models_config.py`: rejected because it would break existing imports and is out of scope
- Adding a symlink or alias: rejected because it adds unnecessary complexity and doesn't solve the root cause

## Implementation

### Target file

`docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Verify `github_models_config.py` exists and contains expected definitions
2. Update line 163: `models_config.py` → `github_models_config.py`
3. Update line 173: `scripts/mcp_servers/github/models_config.py` → `scripts/mcp_servers/github/github_models_config.py`
4. Run `uv run python tools/check_docs_consistency.py --domain mcp` and verify warnings are reduced
5. Verify zero stale `models_config.py` references remain via `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/`

### Method

Use Edit tool to replace the exact strings in the specified lines.

### Details

#### REQ-001: Line 163

**Before:**
```markdown
...actual default count for listing endpoints is module constant `DEFAULT_PER_PAGE = 10` (`models_config.py`) which each request model references directly (not configurable)...
```

**After:**
```markdown
...actual default count for listing endpoints is module constant `DEFAULT_PER_PAGE = 10` (`github_models_config.py`) which each request model references directly (not configurable)...
```

#### REQ-002: Line 173

**Before:**
```markdown
**Domain Exceptions** (defined in `scripts/mcp_servers/github/models_config.py`, re-exported in `github_models.py`): ...
```

**After:**
```markdown
**Domain Exceptions** (defined in `scripts/mcp_servers/github/github_models_config.py`, re-exported in `github_models.py`): ...
```

## Compatibility considerations

- This change only affects documentation references; no runtime behavior changes
- The referenced file `github_models_config.py` must exist and contain the expected definitions

## Security considerations

- No security implications; this is a documentation reference fix

## Rollback considerations

- Revert the two string replacements to restore the original stale references
- No code changes to revert

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_04_01_web-search-file-read-github.md` | Document consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Stale reference warnings reduced |
| `docs/04_mcp_04_01_web-search-file-read-github.md` | Manual verification | `grep -n 'models_config\.py' docs/04_mcp_04_01_web-search-file-read-github.md` | Zero matches |

## Completion criteria

- [ ] Line 163 no longer contains `models_config.py` reference
- [ ] Line 173 no longer contains `models_config.py` reference
- [ ] Both lines now correctly reference `github_models_config.py`
- [ ] `check_docs_consistency.py --domain mcp` shows reduced warnings
- [ ] `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/` returns zero matches

## Out of scope

- Renaming `github_models_config.py` to `models_config.py`
- Modifying import structures
- Changing public/runtime interfaces
- Database schema changes
- Other files not listed in Implementation Target Files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `github_models_config.py` exists and contains expected definitions | Completed | — | — |  |
| 2 | Update line 163 in `docs/04_mcp_04_01_web-search-file-read-github.md` | Completed | — | — |  |
| 3 | Update line 173 in `docs/04_mcp_04_01_web-search-file-read-github.md` | Completed | — | — |  |
| 4 | Run `check_docs_consistency.py --domain mcp` and verify warnings are reduced | Completed | — | — |  |
| 5 | Verify zero stale `models_config.py` references remain | Completed | — | — |  |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260923-100002_p003_github_mcp_file_path_inconsistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-154518_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-155331
- **Related target files**: docs/04_mcp_04_01_web-search-file-read-github.md