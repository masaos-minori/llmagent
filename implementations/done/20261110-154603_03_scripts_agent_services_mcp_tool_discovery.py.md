## Goal

Make tool-definition mismatch and every other unified finding in `McpToolDiscoveryService` always FATAL by removing `_is_strict` and the WARNING severity, and passing `strict=True` to the definition check (REQ-001 strict-only startup).

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/services/mcp_tool_discovery.py` and its companion `tests/agent/services/test_mcp_tool_discovery.py`.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- `_unified_status()` is used by `_build_drift_findings`, `_build_write_classification_findings` and `_check_tool_definitions_finding`; after the change it has no branch, so it is removed and `StartupCheckStatus.FATAL` is used directly (or kept as a one-line constant-returning method if a cleaner diff results; pick one and keep the call sites uniform).
- Malformed-capability findings are built in `mcp_tool_discovery_fetch.py`/`mcp_tool_discovery_registry.py` (not targets) and are escalated per server `required` flag by `_escalate_unreachable_findings`; they do not read `tool_definitions_strict`. A stale mention of strict mode in `mcp_tool_discovery_registry.py:31` docstring is left (not a target); noted as an observation.
- The companion test file also has `SecurityProfile` parameters (lines 32, 101, 107, 985-1010, 1023-1063, 1748); they are removed here for AC-07 (the `_make_ctx(security_profile=...)` helper and the parametrized profile test, which has the single value `PRODUCTION`).

## Design decisions

- Single severity: FATAL. `_check_tool_definitions` (imported from `tool_validation.py`) is called as `_check_tool_definitions(self._ctx, strict=True)`; `tool_validation.py` is unchanged.
- The module docstring paragraphs that describe `is_fatal = strict` are rewritten to describe always-FATAL; duplicate-tool findings remain "always FATAL" and are no longer an exception to the scheme.

## Alternatives considered

Keeping `_is_strict` returning `True` was rejected (dead optionality). Leaving the docstring as is was rejected because it documents a mode that no longer exists (Plan Problem statement).

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
1. Delete `_is_strict` (line 155) and `_unified_status` (line 159) from `McpToolDiscoveryService`.
2. In `_build_drift_findings` (line 171) and `_build_write_classification_findings` (line 192) pass `StartupCheckStatus.FATAL` to `_unified_findings`.
3. In `_check_tool_definitions_finding` (line 202) set `status = StartupCheckStatus.FATAL`, call `_check_tool_definitions(self._ctx, strict=True)`, and update its docstring (drop "unified severity" / "strict-mode" wording).
4. Rewrite the module docstring lines 36-43 (duplicate handling and "Unified severity scheme") and the line-17 phrase "one WARNING/FATAL finding" only where it refers to strict mode.

### Method
- Edit by symbol; `StartupCheckStatus` is already imported (used by `_escalate_unreachable_findings`).
- `rg -n "_is_strict|_unified_status|tool_definitions_strict|is_fatal = strict" scripts/agent/services/mcp_tool_discovery.py` must return nothing afterwards.

### Details
- Do not change `_escalate_unreachable_findings`: its FATAL-for-required, WARNING-otherwise rule is the ADR-004 server-mandatoriness behavior, a different axis from strictness and out of scope (server mandatoriness decision).
- `_unified_findings` helper signature stays.

### Companion test files
- `tests/agent/services/test_mcp_tool_discovery.py`
  - Procedure: In `_make_ctx` (line 101) drop the `security_profile` and `tool_definitions_strict` parameters and assignments (lines 101-108); remove the `strict`/`expected` parametrization (lines 119-145) in favor of a FATAL-only case; remove WARNING-expectation parameters at lines 1970-2116 and the `ctx.cfg.tool.tool_definitions_strict = ...` assignments (lines 1058, 1700, 1750, 1796, 1873, 1947, 2009, 2066, 2116); delete the profile-equivalence test (lines 985-1010) and the `SecurityProfile` import (line 32).
  - Validation: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

## Compatibility considerations

Behavior change only for a config that set `tool_definitions_strict = false`, which the production validator already rejected; the shipped config sets it true.

## Security considerations

Removes the WARNING downgrade of drift, write-classification mismatch and tool-definition mismatch findings; no new permissive path.

## Rollback considerations

`git revert`; ships in the same release unit as the config key removal.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v` (posture-gate test has its own Plan row).
- `uv run ruff format`/`ruff check` on both files; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- No strict toggle or `_unified_status` remains in the source.
- Every drift, write-classification and tool-definition finding is FATAL; the test file asserts this and has no `SecurityProfile` reference.

## Out of Scope

- `mcp_tool_discovery_fetch.py`, `mcp_tool_discovery_registry.py`, `tool_validation.py`.
- Server `required`-based escalation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `_is_strict`/`_unified_status`, use FATAL, pass `strict=True`, rewrite the docstrings | Completed | 20261110-164000 | 20261110-170211 | rg check returns nothing |
| 2 | Update the companion test: FATAL-only expectations, remove strict and `SecurityProfile` plumbing | Completed | 20261110-164000 | 20261110-170211 | 3 WARNING-expectation tests resolved: the two duplicated `test_unreachable_non_required_server_with_{fail_fast,degraded}_returns_warning` cases (identical configs, mode names were profile artifacts) were merged into one `test_unreachable_non_required_server_tool_definition_check_is_fatal` asserting FATAL tool-def finding + preserved escalation WARNING (mandatoriness axis, out of scope); `test_malformed_entry_does_not_exclude_other_valid_entries` now asserts FATAL — `_validate_tools_response` marks a server with a malformed `/v1/tools` body unreachable, so always-strict raises the tool-def finding (Plan row: "Drop non-strict (WARNING) cases; mismatch is always FATAL") |
| 3 | Run ruff, mypy and the discovery tests | Completed | 20261110-170211 | 20261110-170211 | ruff/ruff-check pass; mypy clean on this file; `test_mcp_tool_discovery.py` 82 passed; posture-gate file keeps 1 allowed red (`test_a_required_tool_of_a_posture_rejected_server_is_a_fatal_finding`, mismatch finding count) owned by the posture-gate document |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`, `tests/agent/services/test_mcp_tool_discovery.py`
