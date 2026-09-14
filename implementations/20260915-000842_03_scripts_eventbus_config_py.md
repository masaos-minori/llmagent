# Implementation Procedure: Verify EventBus Config Loading Mechanism (Read-Only Reference)

## Goal

Document the current state of `scripts/eventbus/config.py` as evidence for CI-001 reconciliation. This is a read-only verification step — no modifications to this file are required.

## Scope

- Read-only inspection of `scripts/eventbus/config.py`
- Confirm tomllib-based config loading mechanism
- Verify local invariant enforcement documented in docstring

## Assumptions

- Current implementation reflects intended design (not a temporary workaround)
- The local invariant approach is sufficient mitigation for CI-001

## Design decisions

- No changes to this file — documentation only
- Evidence gathered here supports ADR-002 CI-001 Known Deviation entry

## Alternatives considered

### Alternative A: Modify config.py to use ConfigLoader

**Reason for rejection:** This would violate the `.importlinter eventbus-is-isolated` contract. The local invariant approach is the approved resolution for CI-001.

## Implementation

### Target file

`scripts/eventbus/config.py` (read-only)

### Procedure

1. Verify config.py imports tomllib (line 6)
2. Verify load_config() uses tomllib.load() directly (lines 163-230)
3. Verify load_config() docstring documents the local invariant (line 164)
4. Verify callers in app.py pass get_config_path()'s return value
5. Run regression test: `pytest tests/eventbus/test_eventbus_config.py`

### Method

Read-only inspection and test execution.

### Details

#### Step 1: Verify tomllib import

Line 6 confirms:
```python
import tomllib
```

No ConfigLoader import exists in this module.

#### Step 2: Verify load_config() implementation

Lines 163-230 show load_config() uses tomllib.load() directly:
```python
def load_config(path: Path | None = None) -> EventBusConfig:
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)
```

Key observations:
- No ConfigLoader.restrict_to() call
- Direct file access via Path.open()
- Manual validation of known keys, required keys, and types
- Per-role token validation (at least one must be configured)

#### Step 3: Verify local invariant documentation

Line 164 docstring states:
```
Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant.
```

This confirms the local invariant approach: trust callers to pass the correct path, validated by a regression test.

#### Step 4: Verify caller in app.py

Check that app.py calls load_config(get_config_path()):
```python
from scripts.eventbus.config import get_config_path, load_config
config = load_config(get_config_path())
```

#### Step 5: Run regression test

Run:
```bash
pytest tests/eventbus/test_eventbus_config.py
```

Expected: All tests pass, confirming the local invariant is enforced.

## Compatibility considerations

- Existing consumers of EventBus rely on the current config loading mechanism
- Changing to ConfigLoader would break the `.importlinter eventbus-is-isolated` contract
- The local invariant approach is compatible with the existing architecture

## Security considerations

- CI-001 represents a known security gap (EventBus can potentially access configs outside its scope)
- The local invariant mitigates but does not fully eliminate the risk
- Operators should be aware of this limitation during deployment
- The loopback-only binding check (line 66-70) provides an additional security layer

## Rollback considerations

- No code changes — no rollback needed
- If the local invariant is later found insufficient, revert the Status field in ADR-002 CI-001 to "open"

## Validation plan

1. Confirm config.py still uses tomllib (no regression back to ConfigLoader)
2. Confirm regression test in `tests/eventbus/test_eventbus_config.py` still passes
3. Confirm app.py caller still passes get_config_path()'s return value
4. Cross-check with ADR-002 CI-001 Known Deviation entry

## Completion criteria

- [ ] config.py confirmed to use tomllib (not ConfigLoader)
- [ ] load_config() docstring confirms local invariant
- [ ] Regression test passes
- [ ] Caller in app.py verified

## Out of scope

- Modifying config.py to use ConfigLoader
- Adding new validation logic
- Changing the local invariant approach
- Updating other files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify tomllib import | Pending | — | — | |
| 2 | Verify load_config() implementation | Pending | — | — | |
| 3 | Verify local invariant documentation | Pending | — | — | |
| 4 | Verify caller in app.py | Pending | — | — | |
| 5 | Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (config isolation enforcement)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-000842
- **Related target files**: scripts/eventbus/config.py
