## Goal
Stop using the retired `security_profile` config key as this test's example
flat-key value, so the test no longer implies that key remains valid.

## Scope
- **In-Scope**: `test_reload_loads_agent_toml_content()`'s example TOML
  content and assertion (lines 16-27).
- **Out-of-Scope**: every other test in this file (`test_reload_loads_mcp_servers_section`
  and the rest of `TestReloadScope`) — confirmed by direct read to use
  unrelated example keys/sections.

## Assumptions
- **Corrected 2026-09-04**: this test exercises `ConfigLoader.load_all()`
  (`shared/config_loader.py`), a generic flat-TOML-key loader — not
  `ConfigReloadService` (row 10's target) and not the `SecurityProfile` enum
  (row 15's target). It merely used `security_profile` as an arbitrary
  example key/value pair to demonstrate that `load_all()` exposes flat keys.
  `ConfigLoader.load_all()` does not validate key names, so this test would
  continue to pass unmodified even after rows 1-12 land; the edit here is a
  documentation/clarity fix (avoid implying a retired key is still
  meaningful), not a required correctness fix.

## Design decisions
- Replace `security_profile = "local"` with a different, still-meaningful
  generic example key (e.g. `tool_cache_ttl` alone, or an unrelated key like
  `masked_fields`) rather than changing its value to `"production"` — keeping
  any `security_profile` reference at all, even a valid one, would misstate
  that this key remains part of the deployed schema post-REQ-009.

## Alternatives considered
- Leaving the test unchanged: rejected — while not functionally required, an
  example asserting `cfg.get("security_profile") == "local"` reads as live
  documentation of a config key this Plan retires elsewhere; leaving it
  creates confusion for future readers cross-referencing this test against
  `config/agent.toml` (row 12).

## Implementation
### Target file
`tests/shared/test_config_hot_reload.py`

### Procedure
Replace the example TOML content and assertion in
`test_reload_loads_agent_toml_content()` (verified 2026-09-04, lines 16-27)
to use a non-retired example key in place of `security_profile`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04):
```python
def test_reload_loads_agent_toml_content(self, tmp_path: Path) -> None:
    """load_all() loads agent.toml and makes all flat keys accessible."""
    _write_toml(
        tmp_path / "agent.toml",
        'security_profile = "local"\ntool_cache_ttl = 300\n',
    )

    cfg = ConfigLoader(config_dir=tmp_path).load_all()

    assert cfg.get("security_profile") == "local"
    assert cfg.get("tool_cache_ttl") == 300
```
After:
```python
def test_reload_loads_agent_toml_content(self, tmp_path: Path) -> None:
    """load_all() loads agent.toml and makes all flat keys accessible."""
    _write_toml(
        tmp_path / "agent.toml",
        'tool_cache_ttl = 300\nsemantic_cache_threshold = 0.9\n',
    )

    cfg = ConfigLoader(config_dir=tmp_path).load_all()

    assert cfg.get("tool_cache_ttl") == 300
    assert cfg.get("semantic_cache_threshold") == 0.9
```

## Compatibility considerations
None: purely a test example-data change, no behavior under test changes.

## Security considerations
N/A: test-only file.

## Rollback considerations
Single-test edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_hot_reload.py` | Unit | `uv run pytest tests/shared/test_config_hot_reload.py -v` | Test passes; no reference to `security_profile` remains in this file |

## Completion criteria
No reference to `security_profile` remains in this file; the test's intent
(flat-key loading) is unchanged.

## Out of scope
`test_reload_loads_mcp_servers_section` and other tests in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Not functionally required by rows 1-12; clarity-only |
| 2 | Add or update tests per Validation plan | N/A | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-011
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/shared/test_config_hot_reload.py
