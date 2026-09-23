## Goal

Update stale reference to `models_config.py` that should point to `github_models_config.py` in `docs/04_mcp_06_04_major-default-values.md`.

## Scope

- **In-Scope**: Updating 1 stale reference (line 21) in `docs/04_mcp_06_04_major-default-values.md`
- **Out-of-Scope**: Renaming `github_models_config.py` to `models_config.py`, modifying import structures, changing public/runtime interfaces, database schema changes

## Assumptions

- `github_models_config.py` exists in `scripts/mcp_servers/github/` and contains the expected definitions (exception classes, `DEFAULT_PER_PAGE` constant, `GitHubConfig` dataclass)
- The stale reference is the only one in this file

## Design decisions

- The stale reference uses the incorrect filename pattern (`models_config.py`) and refers to the same actual file (`github_models_config.py`)
- No import structure changes needed since this is a documentation reference

## Alternatives considered

- Renaming `github_models_config.py` to `models_config.py`: rejected because it would break existing imports and is out of scope

## Implementation

### Target file

`docs/04_mcp_06_04_major-default-values.md`

### Procedure

1. Verify `github_models_config.py` exists and contains expected definitions
2. Update line 21: `models_config.py` → `github_models_config.py`
3. Run `uv run python tools/check_docs_consistency.py --domain mcp` and verify warnings are reduced
4. Verify zero stale `models_config.py` references remain via `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/`

### Method

Use Edit tool to replace the exact string in the specified line.

### Details

#### REQ-003: Line 21

**Before:**
```markdown
| GitHub `default_per_page` | 10 (module constant `DEFAULT_PER_PAGE`, `models_config.py`) | — | Hardcoded. `config/github_mcp_server.toml::default_per_page` was removed on 2026-07-13 (unused dead setting. Details: [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md)) |
```

**After:**
```markdown
| GitHub `default_per_page` | 10 (module constant `DEFAULT_PER_PAGE`, `github_models_config.py`) | — | Hardcoded. `config/github_mcp_server.toml::default_per_page` was removed on 2026-07-13 (unused dead setting. Details: [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md)) |
```

## Compatibility considerations

- This change only affects documentation references; no runtime behavior changes
- The referenced file `github_models_config.py` must exist and contain the expected definitions

## Security considerations

- No security implications; this is a documentation reference fix

## Rollback considerations

- Revert the string replacement to restore the original stale reference
- No code changes to revert

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_04_major-default-values.md` | Document consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Stale reference warnings reduced |
| `docs/04_mcp_06_04_major-default-values.md` | Manual verification | `grep -n 'models_config\.py' docs/04_mcp_06_04_major-default-values.md` | Zero matches |

## Completion criteria

- [ ] Line 21 no longer contains `models_config.py` reference
- [ ] Line 21 now correctly references `github_models_config.py`
- [ ] `check_docs_consistency.py --domain mcp` shows reduced warnings
- [ ] `grep -rn 'models_config\.py' docs/04_mcp_*/ scripts/mcp_servers/github/` returns zero matches

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
| 2 | Update line 21 in `docs/04_mcp_06_04_major-default-values.md` | Completed | — | — |  |
| 3 | Run `check_docs_consistency.py --domain mcp` and verify warnings are reduced | Completed | — | — |  |
| 4 | Verify zero stale `models_config.py` references remain | Completed | — | — |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260923-100002_p003_github_mcp_file_path_inconsistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-154518_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-155331
- **Related target files**: docs/04_mcp_06_04_major-default-values.md