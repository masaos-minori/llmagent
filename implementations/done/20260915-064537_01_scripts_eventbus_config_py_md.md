# Implementation Procedure: Migrate EventBus Configuration Loading to ConfigLoader

## Goal

Replace `scripts/eventbus/config.py`'s direct `tomllib.load()` call with `ConfigLoader`-based loading, preserving all of EventBus's existing fail-closed validation behavior (cross-field checks, required-token checks, etc.) rather than replacing it with `ConfigLoader`'s defaults.

## Scope

- Modify `scripts/eventbus/config.py`: replace `tomllib.load()` with `ConfigLoader`-based loading
- Preserve all existing validation logic in `__post_init__` and `load_config()`
- No change to EventBus's actual validation policy or supported configuration keys

## Assumptions

- `ConfigLoader.restrict_to(*filenames)` sets process-level file access restrictions by filename (not process name) — confirmed by `config_loader.py:40-49`
- `ConfigLoader.load(*names)` accepts config file *names* (not paths) and resolves them against `_config_dir` — confirmed by `config_loader.py:58-66`
- EventBus's validation logic in `__post_init__` and `load_config()` must be preserved exactly — confirmed by `config.py:99-146` (__post_init__) and `config.py:217-279` (load_config)
- `ConfigLoader._REQUIRED_CONFIG_FILES` is hardcoded to `("agent.toml",)` — confirmed by `config_loader.py:30`
- **Correction**: `tomllib.load()` call is at line 221 (procedure originally claimed ~166)
- **Correction**: `ConfigLoader.load()` cannot replace `tomllib.load()` directly because `ConfigLoader.load()` takes file names resolved against `_config_dir`, not arbitrary file paths like `get_config_path()` returns
- **Correction**: `ConfigLoader.restrict_to()` takes filenames, not a process name parameter
- A separate implementation procedure is needed to relax the `.importlinter` `eventbus-is-isolated` contract before this migration can proceed

## Design decisions

### Decision A: Preserve EventBus's validation logic alongside ConfigLoader usage

**Reason:** EventBus has unique validation requirements (cross-field checks, required-token checks) that differ from `ConfigLoader`'s defaults. Replacing the validation logic would silently relax existing checks, violating REQ-002.

### Alternative A: Replace EventBus's validation with `ConfigLoader`'s built-in validation

**Reason for rejection:** Would break REQ-002 — EventBus's validation behavior must be preserved exactly. The `ConfigLoader` default validation is insufficient for EventBus's fail-closed requirements.

### Decision B: Relax `.importlinter` `eventbus-is-isolated` contract before migration

**Reason:** Both issues touch `restrict_to()` initialization requirements. If both are implemented in the same session, coordination ensures consistent behavior. The `.importlinter` contract currently forbids EventBus from importing `shared`, which blocks the ConfigLoader migration entirely.

### Alternative B: Document an exception in `ADR-002` instead of relaxing the contract

**Reason for rejection:** `plans/20260914-184302_plan.md` explicitly decided to relax the contract rather than document an exception. This plan supersedes the local-invariant approach recorded in `ADR-002` (lines 363-375) and `ADR-013` (Decision Details #8).

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

#### Step 1: Analyze current state of `config.py`

Read the current implementation to understand:
- How `tomllib.load()` is called (line 166)
- What configuration files are loaded
- What validation logic exists in `__post_init__` (lines 60-94)
- What validation logic exists in `load_config()` (lines 163-230)

#### Step 2: Relax `.importlinter` `eventbus-is-isolated` contract

Before implementing the migration, the `.importlinter` contract must be relaxed to allow EventBus to import from `shared`. Two approaches:

A. Narrow the `forbidden_modules` list to exclude `shared`:
```ini
[importlinter:contract:eventbus-is-isolated]
name = eventbus must not import from agent, mcp_servers, rag, db
type = forbidden
source_modules =
    eventbus
forbidden_modules =
    agent
    mcp_servers
    rag
    db
```

B. Add a scoped exception allowing only `shared.config_loader.ConfigLoader`:
```ini
[importlinter:contract:eventbus-is-isolated]
name = eventbus must not import from agent, mcp_servers, rag, db, or shared
type = forbidden
source_modules =
    eventbus
forbidden_modules =
    agent
    mcp_servers
    rag
    db
    shared
exemptions =
    scripts/eventbus/config.py -> scripts/shared/config_loader.py
```

Approach A is preferred (narrower change) unless there's a reason to keep the broader prohibition.

After updating the contract, verify with:
```bash
PYTHONPATH=scripts uv run lint-imports
```

Expected: `eventbus-is-isolated` reports no violations after the change.

#### Step 3: Import `ConfigLoader`

Add import statement at the top of the file:
```python
from shared.config_loader import ConfigLoader
```

Verify this does not violate the updated `.importlinter` contract.

#### Step 4: Replace `tomllib.load()` call with `ConfigLoader`-based loading

Current code (around line 221):
```python
with p.open("rb") as f:
    data = tomllib.load(f)
```

After change — since `ConfigLoader.load()` takes file names (not paths), we need a different approach. Options:

Option A: Use `ConfigLoader` with explicit config directory:
```python
loader = ConfigLoader(config_dir=p.parent)
data = loader.load(p.name)
```

Option B: Keep direct `tomllib.load()` but add `ConfigLoader.restrict_to()` guard:
```python
# At process startup (before any config is loaded):
ConfigLoader.restrict_to("eventbus.toml")

# In load_config():
if ConfigLoader._allowed_files is not None:
    basename = Path(p).name
    if basename not in ConfigLoader._allowed_files:
        raise ValueError(f"This process is not permitted to load '{basename}'.")
with p.open("rb") as f:
    data = tomllib.load(f)
```

Option C: Create a thin wrapper that delegates to `ConfigLoader`'s internal methods while accepting a path:
```python
def _load_config_from_path(path: Path) -> dict[str, Any]:
    """Load config from an arbitrary path using ConfigLoader's internal logic."""
    loader = ConfigLoader(config_dir=path.parent)
    return loader.load(path.name)
```

Recommended: Option C — it preserves `ConfigLoader`'s meta-key filtering, TOML/JSON support, and error handling while accepting an arbitrary path.

#### Step 5: Preserve `__post_init__` validation logic

Ensure the `__post_init__` method (lines 99-146) remains unchanged. This contains EventBus-specific validation that must not be replaced by `ConfigLoader`'s defaults.

#### Step 6: Preserve `load_config()` validation logic

Ensure the `load_config()` function (lines 217-279) remains unchanged. This contains EventBus-specific validation that must not be replaced by `ConfigLoader`'s defaults.

#### Step 7: Initialize `restrict_to()` appropriately

If `ConfigLoader.restrict_to()` needs to be initialized for the EventBus process before production config loading, add the appropriate call. Example:
```python
ConfigLoader.restrict_to("eventbus.toml")
```

This should be called once at process startup, before any config is loaded.

#### Step 8: Remove unused `tomllib` import

Remove the `import tomllib` statement (line 6) if it is no longer used elsewhere in the file. Note: if Option C above is chosen, `tomllib` may still be needed internally by `ConfigLoader._load_single()`, so check whether `ConfigLoader` already imports it.

#### Step 9: Run static analysis

```bash
uv run ruff check scripts/eventbus/config.py
uv run mypy scripts/eventbus/config.py
```

Expected: No new errors introduced.

#### Step 10: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_config.py -v
```

Expected: All existing tests pass.

### Method

Create a thin wrapper around `ConfigLoader` that accepts an arbitrary file path (preserving `get_config_path()` behavior), relax the `.importlinter` contract, and preserve all existing EventBus validation logic.

### Details

#### Verification checklist

- [x] Adversarial verification completed — procedure corrected on findings
- [ ] `.importlinter` `eventbus-is-isolated` contract relaxed to permit `shared` import
- [ ] `ConfigLoader` import added without violating updated `.importlinter` contract
- [ ] `tomllib.load()` replaced with `ConfigLoader`-based loading (via thin wrapper accepting arbitrary path)
- [ ] `__post_init__` validation logic preserved exactly
- [ ] `load_config()` validation logic preserved exactly
- [ ] `restrict_to()` initialized appropriately for EventBus process
- [ ] Unused `tomllib` import handled (may remain if `ConfigLoader` uses it internally)
- [ ] Static analysis passes without new errors
- [ ] Existing tests pass

## Compatibility considerations

- **Breaking change risk**: Low — `ConfigLoader.load()` should return the same config structure as `tomllib.load()`
- **Downstream consumers**: None expected — the public API surface (`load_config()`) remains unchanged
- **Migration path**: None required — the change is internal to the configuration loading layer

## Security considerations

- **Positive impact**: EventBus will now benefit from `ConfigLoader`'s process-level file-access restriction (`restrict_to()`)
- **Risk**: If `ConfigLoader`'s default validation is less strict than EventBus's current validation, this could introduce security regressions
- **Mitigation**: Preserve EventBus's existing validation logic exactly; do not rely on `ConfigLoader`'s defaults

## Rollback considerations

- Revert to original `tomllib.load()` call
- Restore `import tomllib` if removed
- Remove `ConfigLoader` import if added
- Remove `restrict_to()` call if added

## Validation plan

1. **Static analysis**: Confirm no new lint/type errors introduced
2. **Test execution**: Confirm all existing tests in `tests/eventbus/test_eventbus_config.py` pass
3. **Acceptance criteria verification**:
   - [ ] AC-1: `scripts/eventbus/config.py` loads its configuration via `ConfigLoader`, not `tomllib.load()` directly
   - [ ] AC-2: Every existing EventBus configuration validation error case still produces an equivalent error after migration
   - [ ] AC-3: EventBus configuration loading is now covered by the same process-isolation guarantee (`restrict_to()`) as other processes, or the exception is explicitly documented in `ADR-002` if EventBus cannot use it for a confirmed technical reason
   - [ ] AC-4: `.importlinter` `eventbus-is-isolated` contract relaxed to permit `shared` import

## Completion criteria

- [x] Adversarial verification completed — procedure corrected on findings
- [ ] `.importlinter` `eventbus-is-isolated` contract relaxed to permit `shared` import
- [ ] `ConfigLoader` import added without violating updated `.importlinter` contract
- [ ] `tomllib.load()` replaced with `ConfigLoader`-based loading (via thin wrapper accepting arbitrary path)
- [ ] `__post_init__` validation logic preserved exactly
- [ ] `load_config()` validation logic preserved exactly
- [ ] `restrict_to()` initialized appropriately for EventBus process
- [ ] Unused `tomllib` import handled (may remain if `ConfigLoader` uses it internally)
- [ ] Static analysis passes without new errors
- [ ] All existing tests pass

## Out of scope

- Modifying `ConfigLoader` itself (separate procedure per row)
- Adding new validation rules beyond what currently exists
- Changing EventBus's actual validation policy or supported configuration keys
- Updating CI-001 governance entry (separate procedure per row)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relax .importlinter eventbus-is-isolated contract | Completed | 20260915-220400 | 20260915-220400 | Contract relaxed to permit shared import |
| 2 | Import ConfigLoader | Completed | 20260915-220400 | 20260915-220400 | Added from shared.config_loader import ConfigLoader |
| 3 | Replace tomllib.load() with ConfigLoader-based loading | Completed | 20260915-220328 | 20260915-220328 | Adversarial verification: 1) tomllib.load() at line 221 (procedure claimed ~166); 2) ConfigLoader.load() takes filenames not paths; 3) restrict_to() takes filenames not process_name; 4) No separate procedure for .importlinter relaxation |
| 4 | Preserve __post_init__ validation | Completed | 20260915-220400 | 20260915-220400 | Unchanged |
| 5 | Preserve load_config() validation | Completed | 20260915-220400 | 20260915-220400 | Unchanged |
| 6 | Initialize restrict_to() for EventBus | Completed | 20260915-220400 | 20260915-220400 | ConfigLoader.restrict_to("eventbus.toml") called at startup |
| 7 | Handle unused tomllib import | Completed | 20260915-220400 | 20260915-220400 | Removed (ConfigLoader uses it internally) |
| 8 | Run static analysis | Completed | 20260915-220400 | 20260915-220400 | ruff check OK, mypy OK, bandit no high findings |
| 9 | Run existing tests | Completed | 20260915-220400 | 20260915-220400 | 31/31 config tests pass |

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
- **Requirement ID**: REQ-001 (replace tomllib.load() with ConfigLoader-based loading), REQ-002 (preserve existing validation behavior), REQ-003 (confirm restrict_to() initialization)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064537
- **Related target files**: scripts/eventbus/config.py