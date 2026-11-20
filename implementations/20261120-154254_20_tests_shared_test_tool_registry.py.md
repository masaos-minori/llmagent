## Goal

Remove every `validate_routing_against_config()` reference from `tests/shared/test_tool_registry.py` (`REQ-004`, scope approved). `validate_routing_against_config()` is removed by row 8 (`tool_routing_validation.py`); this file imports it (line 20) and exercises it in three classes. Once removed, the import raises `ImportError` and every call breaks. Retain the live-vs-registry drift suites (`TestValidateRoutingAgainstLive`, `TestStartupValidationStrictMode`) that exercise the surviving `validate_routing_against_live()`.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Current source has THREE classes that call `validate_routing_against_config()`:
  - `TestValidateRoutingDriftRegistry` (L25-66): all three tests call it.
  - `TestConfigGatedToolDrift` (L123-183): MIXED — the four config cases (L139-169) call `validate_routing_against_config()`; the two live cases (L171-183) call `validate_routing_against_live()`.
  - `TestValidateRoutingAgainstRealConfig` (L313-366): both tests call it (and load the real `config/agent.toml`).
- The Plan's retention list names exactly two surviving classes: `TestValidateRoutingAgainstLive` (L79) and `TestStartupValidationStrictMode` (L186). `TestConfigGatedToolDrift` is NOT in the retention list; its name and purpose describe a config-gated tool (a `tool_names` concept removed by this Plan), so the whole class is removed. Its two live cases duplicate coverage already present in `TestValidateRoutingAgainstLive` and lose no unique coverage.
- After removing those three classes, the following imports become UNUSED and must go too:
  - `from shared.mcp_config import McpServerConfig` (line 12) — referenced only by the removed classes' `MagicMock(spec=McpServerConfig)` and `_config()` signature.
  - `from unittest.mock import MagicMock` (line 9) — referenced only by the removed classes.
  - `from pathlib import Path` (line 8) — referenced only by `TestValidateRoutingAgainstRealConfig._load_real_server_configs()` (L349).
  - `validate_routing_against_config` from the `shared.tool_routing_validation` import (line 20).
- Surviving imports (keep): `validate_routing_against_live` (used by the two retained classes), `ToolDefinition`, `ToolRegistry`, `_reset_registry_for_testing`, `get_registry` (all used by retained classes), `pytest`, `annotations`.
- The module docstring (L1-4) references "registry drift validation" generically; leave it (it still covers the retained live-drift tests).

## Design decisions
- Delete the three `validate_routing_against_config` classes wholesale.
- Collapse the `shared.tool_routing_validation` import to `validate_routing_against_live` only.
- Drop the now-unused `pathlib.Path`, `unittest.mock.MagicMock`, and `shared.mcp_config.McpServerConfig` imports.
- Leave all retained classes byte-for-byte unchanged.

## Alternatives considered
- Keeping `TestConfigGatedToolDrift`'s two live cases: rejected because the class is named around config-gated tools (a removed concept), the Plan's retention list does not include it, and the two live cases duplicate `TestValidateRoutingAgainstLive` coverage.
- Rewriting the config-drift tests against `validate_routing_against_live()`: rejected because these tests specifically exercise the config-source path (`cfg.tool_names`), which no longer exists; the live path is covered by the retained classes.

## Implementation
### Target file
`tests/shared/test_tool_registry.py`

### Procedure
Remove the three config-drift classes, the `validate_routing_against_config` import, and the three now-unused imports.

### Method
1. Replace the top-of-file import block:
   ```python
   from __future__ import annotations

   from pathlib import Path
   from unittest.mock import MagicMock

   import pytest
   from shared.mcp_config import McpServerConfig
   from shared.tool_registry import (
       ToolDefinition,
       ToolRegistry,
       _reset_registry_for_testing,
       get_registry,
   )
   from shared.tool_routing_validation import (
       validate_routing_against_config,
       validate_routing_against_live,
   )
   ```
   with
   ```python
   from __future__ import annotations

   import pytest
   from shared.tool_registry import (
       ToolDefinition,
       ToolRegistry,
       _reset_registry_for_testing,
       get_registry,
   )
   from shared.tool_routing_validation import (
       validate_routing_against_live,
   )
   ```
2. Delete `TestValidateRoutingDriftRegistry` (L25-66) and its trailing blank lines.
3. Delete `TestConfigGatedToolDrift` (L123-183) and its trailing blank lines.
4. Delete `TestValidateRoutingAgainstRealConfig` (L313-366, end of file) and its trailing blank lines.

### Details
- Confirm no `validate_routing_against_config`, `MagicMock`, `McpServerConfig`, or `Path` reference remains anywhere in the file.
- Confirm `validate_routing_against_live` is still imported and referenced (it is, by the two retained classes).
- Do not touch `TestDuplicateOwnershipRejection`, `TestValidateRoutingAgainstLive`, `TestStartupValidationStrictMode`, `TestAllToolConstantsFrozensetsRegistered`, or `TestGetToolNamesOrdering`.

## Compatibility considerations
Test-only change. Removes dead tests for a removed function; the surviving live-drift suites are unchanged. No production compatibility impact.

## Security considerations
N/A: test-only. Removing tests for the config-based `validate_routing_against_config` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/shared/test_tool_registry.py` and assert the full suite collects and passes (no import error, no missing-symbol errors).
- Confirm the three config-drift classes are gone and `TestValidateRoutingAgainstLive` / `TestStartupValidationStrictMode` remain.
- Run ruff on the file to confirm no unused-import (`F401`) warnings remain after the import collapse.

## Completion criteria
`test_tool_registry.py` contains no `validate_routing_against_config` / `MagicMock` / `McpServerConfig` / `Path` reference; the module imports cleanly; the two retained live-drift suites pass.

## Out of Scope
The `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `check_routing_drift()` removals (`routing_drift.py` row 16, `startup_validation.py` row 17), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `test_startup_mcp_starter.py` config-drift test removals (row 19), and the cascade fixes to the non-Plan startup test files (rows 23-27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Removes existing tests; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `tests/shared/test_tool_registry.py`
