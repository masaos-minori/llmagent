## Goal

Remove stale coverage omit entry referencing deleted `scripts/db/migrate.py` from `pyproject.toml`.

## Scope

**In-Scope:**
- Remove `"scripts/db/migrate.py"` line from `[tool.coverage.run].omit` in `pyproject.toml`
- Ensure no trailing comma issues after removal

**Out-of-Scope:**
- Any other coverage configuration changes
- Changes beyond the single line removal

## Assumptions

1. The file `scripts/db/migrate.py` was intentionally deleted and will not be restored
2. No other part of the project depends on this omit entry existing

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether any CI pipeline or documentation references this specific omit entry | Check CI configs and docs | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `pyproject.toml:118` — remove line `"scripts/db/migrate.py",`

- **Blast Radius:**
  - Very low churn — single line deletion in one config file
  - Very low risk since changes are purely configurational

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

No design decisions required. Straightforward config cleanup.

## Implementation

### Target files
- `pyproject.toml`

### Procedure
1. Phase 1: Verify `scripts/db/migrate.py` does not exist in repo
2. Phase 2: Remove the stale omit entry
3. Phase 3: Verify with coverage

### Method
Edit pyproject.toml to remove the stale line and fix trailing comma if needed.

### Details
1. Verify `scripts/db/migrate.py` does not exist:
   ```bash
   ls scripts/db/migrate.py 2>&1 || echo "File does not exist"
   ```

2. Edit `pyproject.toml`:
   ```toml
   # Before:
   omit = [
       ...
       "scripts/db/migrate.py",
   ]
   
   # After:
   omit = [
       ...
   ]
   ```

3. Fix trailing comma if needed — ensure the last item before `]` has no trailing comma.

## Compatibility considerations

N/A — this is a config cleanup only

## Security considerations

N/A — this is a test configuration change only

## Rollback considerations

- Simple revert: restore original pyproject.toml from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `pyproject.toml` | Config validation | `uv run coverage report` | Coverage runs without errors |

## Out of scope

- Any other coverage configuration changes
- Changes beyond the single line removal

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260726_46_issue.md
- Source requirement: requires/20260726-120050_require.md
- Source plan: plans/20260726-181211_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: pyproject.toml
