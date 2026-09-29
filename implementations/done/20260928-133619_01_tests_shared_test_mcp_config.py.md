## Goal

Add a unit test to `TestRequiredDefault` in `tests/shared/test_mcp_config.py` that asserts `McpServerConfig.required` defaults to `True` for unspecified criticality values and explicitly ties that default to ADR-004 Decision #12/INV-14 (REQ-001, REQ-003).

## Scope

Adds one method to the existing `TestRequiredDefault` class. Reads `scripts/shared/mcp_config.py` (the `required` contract) as verification context only. References `docs/00_governance/governance_03_issue-and-uncertainty-management.md` CI-016 and `docs/10_adr/ADR-004-environment-failure-handling-policy.md` INV-14 as traceability context only — neither is modified here.

## Assumptions

- The `TestRequiredDefault` class already exists at lines 267-287 with two methods covering the default-`True` behavior; this row adds the explicit INV-14 connection on top, not a duplicate of those scenarios.
- `McpServerConfig.required` defaults to `True` when the caller omits it (`scripts/shared/mcp_config.py:104`); `_build_mcp_servers` applies the same default via `_build_single_server` (`:317`).
- pytest is available via `uv run`.

## Design decisions

- Append the new method to the existing `TestRequiredDefault` class rather than introducing a new class, keeping coverage of one invariant co-located with its baseline assertions.
- Use a single direct-construction assertion (`cfg.required is True`) plus a docstring that names ADR-004 Decision #12/INV-14, so the invariant is both asserted and traceable.
- Mirror the existing style (`auth_token="test-token"` placeholder, `-> None` return annotation, four-space indentation).

## Alternatives considered

- Separate `TestInv14SafeDefault` class: rejected — fragments coverage of one invariant across two classes and diverges from the existing single-class layout.
- Parametrized over transport/startup mode: rejected — the safe-default applies regardless of transport/startup mode (per the Plan's Assumptions), so parametrization covers no distinct scenario.
- Full routing test through `scripts/agent/services/mcp_tool_discovery.py`: out of scope for this row (see Out of scope); REQ-002 routing is optional per the issue's "and/or".

## Implementation

### Target file

`tests/shared/test_mcp_config.py`

### Procedure

1. Open `tests/shared/test_mcp_config.py` and locate the existing `TestRequiredDefault` class (lines 267-287).
2. Add one method inside `TestRequiredDefault`, immediately after `test_required_default_true_from_toml_absent_key` (before the class closes at line 287).
3. Implement the method to construct an `McpServerConfig` without passing `required` and assert `cfg.required is True`, with a docstring citing ADR-004 Decision #12/INV-14.
4. Save the file.

### Method

```python
    def test_required_default_reflects_adr004_inv14(self) -> None:
        """ADR-004 Decision #12/INV-14: unspecified criticality must default to required.

        An undefined/undeterminable component criticality must never be assumed
        non-required; the safe default is `required=True`.
        """
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.required is True
```

### Details

- Keep four-space indentation inside the class body; match the construction pattern of `test_required_default_true_on_direct_construction` (lines 268-272).
- Do not import anything new — `McpServerConfig` and `TransportType` are already imported and used by sibling methods.
- The method name is unique within the class; it does not collide with the two existing methods.

## Compatibility considerations

- Adds a test method only; no production code, no new dependencies, no API change.
- Does not alter or rename existing `TestRequiredDefault` methods.

## Security considerations

- Uses `auth_token="test-token"` placeholder, matching existing test fixtures; never a real credential.
- Asserts fail-closed behavior (`required=True`), reinforcing the safety net rather than weakening it.

## Rollback considerations

- Revert is limited to removing the added method; existing methods and imports are untouched.

## Validation plan

- Run the targeted test: `uv run pytest tests/shared/test_mcp_config.py::TestRequiredDefault::test_required_default_reflects_adr004_inv14 -v`.
- Run the full suite once per `rules/toolchain.md`: `uv run pytest`.

## Completion criteria

- The new method exists inside `TestRequiredDefault`, asserts `cfg.required is True` for an omitted `required`, and its docstring references ADR-004 Decision #12/INV-14.
- The targeted test and the full suite pass with no regression.

## Out of scope

- Production behavior of `McpServerConfig.required` (unchanged).
- Routing assertions under `scripts/agent/services/mcp_tool_discovery.py` (REQ-002) — optional per the issue; not added here.
- Updates to `docs/10_adr/ADR-004-environment-failure-handling-policy.md` and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — handled by their own rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260929-130305 | Method test_required_default_reflects_adr004_inv14 added inside TestRequiredDefault; asserts cfg.required is True for omitted required. |
| 2 | Add or update tests per Validation plan | Completed | — | 20260929-130305 | Targeted test passes. Full suite: 8001 passed / 2 skipped-fail unrelated. mypy: 8 pre-existing errors, zero new regressions. ruff format/check clean. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260929-130305 | stale_detector reported 3 mismatches — all FALSE POSITIVES verified independently (TestRequiredDefault@267, _build_single_server@271 exist; TestInv14SafeDefault is a rejected-alternative name). 2 full-suite failures (test_orchestrator::test_original_config_restored_even_on_error, test_eventbus_ack_endpoint::test_ack_event_principal_ownership_validation) are PRE-EXISTING/unrelated to this test-only change. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260929-130305 | N/A: no docs/00_index.md task-scope mapping for tests/shared/test_mcp_config.py (pure test addition). |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260927-211347_ci016_add-unit-test-for-adr-004-undefined-criticality-safe-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-094534_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-133619
- **Related target files**: tests/shared/test_mcp_config.py