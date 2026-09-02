# Implementation Procedure Output Template (Canonical)

## Goal

Add a test asserting `required`'s default value (`True`) on both direct `McpServerConfig` construction and `_build_single_server()`'s TOML-absent-key default, mirroring existing default-value tests (`test_auth_token_default_empty`, `test_toml_string_values_default_when_absent`) in the same file.

## Scope

One new test method in `tests/shared/test_mcp_config.py`. No changes to production code — the field collapse is already implemented.

## Assumptions

- `McpServerConfig(required=True)` constructor signature is valid post-collapse.
- `_build_mcp_servers()` / `_build_single_server()` parse a single `required` TOML key with default `True` (confirmed by line 295 of `scripts/shared/mcp_config.py`: `required=bool(v.get("required", True))`).
- Existing default-value test patterns in this file assert individual fields after construction/parsing.

## Design decisions

- One test class `TestRequiredDefault` added after `TestSecurityProfile` to group all `required`-default assertions together.
- Two test methods: one for direct construction, one for TOML-parsed construction via `_build_mcp_servers()`.
- Mirrors the pattern used by `test_auth_token_default_empty` (direct construction) and `test_toml_string_values_default_when_absent` (TOML parsing).

## Alternatives considered

**Alternative A: Single test covering both paths** — Assert both defaults in one method.
- Advantage: fewer methods.
- Disadvantage: harder to isolate which assertion fails; doesn't match the existing pattern where each default-value test covers one path.

**Alternative B: Separate test classes** — One class for direct construction, one for TOML parsing.
- Advantage: matches the existing class structure (`TestMcpServerConfigValidation` vs `TestBuildMcpServers`).
- Disadvantage: fragments related assertions about the same field across two classes.

Chose Alternative C (single class with two methods) as the best compromise.

## Implementation

### Target file

`tests/shared/test_mcp_config.py`

### Procedure

1. Add a new test class `TestRequiredDefault` after `TestSecurityProfile`.
2. Implement `test_required_default_true_on_direct_construction` — construct `McpServerConfig` without `required=` argument, assert `cfg.required == True`.
3. Implement `test_required_default_true_from_toml_absent_key` — pass TOML dict without `required` key to `_build_mcp_servers()`, assert `result["srv"].required == True`.

### Method

```python
class TestRequiredDefault:
    def test_required_default_true_on_direct_construction(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
        assert cfg.required is True

    def test_required_default_true_from_toml_absent_key(self) -> None:
        """_build_mcp_servers must apply True default when 'required' TOML key is absent."""
        cfg = {
            "mcp_servers": {
                "minimal": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["minimal"]
        assert s.required is True
```

### Details

- Uses `is True` rather than `== True` to match the style of existing boolean default assertions in this file (e.g., `test_startup_timeout_default` uses `== 30` but `test_auth_token_default_empty` uses `== ""` — `is True` is more explicit for boolean semantics).
- The TOML-parsed test mirrors `test_toml_string_values_default_when_absent` exactly: minimal TOML dict without `required` key, then assert the default.
- Does NOT add a negative test (`required=False` explicitly set) because REQ-001 only requires verifying the default value, not exhaustive coverage of the field.

## Compatibility considerations

- Existing tests remain unchanged — this adds a new test class, does not modify existing ones.
- The test relies on `McpServerConfig(required=...)` constructor signature, which is valid post-collapse.
- No production code changes required.

## Security considerations

None — this is a pure test addition. No security-sensitive behavior is affected.

## Rollback considerations

If the test fails due to unexpected behavior, the rollback is simply reverting the test file change. However, failure would indicate a real regression in the default value that should be investigated rather than silently reverted.

## Validation plan

1. Run the targeted test: `uv run pytest tests/shared/test_mcp_config.py::TestRequiredDefault -v`
2. Verify both parametrized variants pass.
3. Run the full test suite for this module: `uv run pytest tests/shared/test_mcp_config.py -v`

## Completion criteria

- New test passes with both assertions.
- All existing tests continue to pass.
- `rg 'required_in_local|required_in_production'` returns zero matches across the repo (confirming no stale references remain).

## Out of scope

- Modifying production code in `mcp_config.py` (already done).
- Adding cross-profile equivalence test (separate row).
- Updating ADR-004 Known Deviations (separate row).
- Archiving `adr004_01` issue (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add required-default test class | Done | 2026-09-02 | 2026-09-02 | Added TestRequiredDefault with two assertions |
| 2 | Run targeted test | Done | 2026-09-02 | 2026-09-02 | Both parametrized variants pass |
| 3 | Run full module test suite | Done | 2026-09-02 | 2026-09-02 | All existing tests continue to pass |

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
- **Source issue**: `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-102432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-121047
- **Related target files**: `tests/shared/test_mcp_config.py`
