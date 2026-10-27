## Goal

Add regression tests to `tests/agent/services/test_config_reload.py` that pin the all-or-nothing behavior this Plan introduces: an invalid section leaves every live section, direct field, and the `ctx.conv` field unchanged while `_sync_services` is never reached; removed-server MCP cleanup does not run on failure; and a fully valid reload still applies everything. The tests drive the real `apply_config_dict` through the existing `svc` / `svc_with_ctx` fixtures so the atomicity is pinned end-to-end.

## Scope

- **In-Scope** (`tests/agent/services/test_config_reload.py`, existing file extended):
  - One new test class covering AC-001, AC-003, AC-004, and AC-002.
  - Four test methods mapping to T-001..T-004.
- **Out-of-Scope**:
  - Any change to `scripts/agent/services/config_reload.py` (row 01) or `scripts/agent/services/config_section_reload.py` (row 02).
  - The hot-reload doc (row 04).
  - Modifying the existing `TestApplyConfig` cases beyond extending the happy-path coverage required by T-004.

## Assumptions

- The `agent` package is importable under the test runner (existing tests import `agent.config_dataclasses` and `agent.services.config_reload`), so the new module imports cleanly.
- `pytest-asyncio` is configured if any async path is exercised; the cases here are synchronous through `apply_config_dict`.
- The `svc` and `svc_with_ctx` fixtures build a real `AgentConfig` over a `MagicMock` `ctx` and already mock `_classify_mcp_server_changes`, so tests only need to supply `new_cfg` payloads and, where needed, mock `_sync_services` and the lifecycle cleanup.
- An invalid `tool` value makes a registry validator raise, which `config_section_reload.py` wraps into `ConfigReloadValidationError` during the candidate phase.

## Design decisions

- **Reuse the existing fixtures.** Each test takes the `svc` or `svc_with_ctx` fixture rather than building a fresh service, matching the file's established pattern and keeping setup DRY.
- **Snapshot before, compare after.** For the unchanged-state assertions, deep-copy the relevant section before the call and assert equality after, so a partial apply is caught by a concrete value comparison.
- **Mock the side effects to prove ordering.** Patch `_sync_services` and `lifecycle.cleanup_server_resources` so "not called" is an exact assertion rather than a inference.
- **One class, four methods.** Each acceptance criterion maps to one method; the shared fixtures keep the setup minimal.

## Alternatives considered

- **A separate new test file.** Rejected: the plan targets this file specifically, and its fixtures are the canonical way to build a `ConfigReloadService` for these tests.

## Implementation

### Target file

`tests/agent/services/test_config_reload.py` (existing; new test class appended)

### Procedure

1. Open `tests/agent/services/test_config_reload.py` and locate the existing `svc` and `svc_with_ctx` fixtures (both construct a real `AgentConfig` over a `MagicMock` `ctx` and mock `_classify_mcp_server_changes`) and the `TestApplyConfig` class.
2. Append a new test class `TestConfigReloadAtomicity` (new) after `TestApplyConfig`.
3. Add `test_invalid_tool_leaves_live_config_unchanged` (new) [T-001]: take `svc_with_ctx`, snapshot the `llm` section, call `apply_config_dict` with a payload of valid `llm` + `rag` changes and an invalid `tool` value, assert it raises `ConfigReloadValidationError`, assert the live sections still equal the snapshot, and assert `_sync_services` was not called (assign a `MagicMock` to `svc._sync_services` first).
4. Add `test_direct_fields_unchanged_on_later_failure` (new) [T-002]: send a payload that sets `allowed_tools`, `masked_fields`, `system_prompt_tool` together with a later-failing section, and assert the direct fields and `ctx.conv.system_prompt_content` are unchanged from their pre-call values.
5. Add `test_mcp_cleanup_not_run_on_validation_failure` (new) [T-003]: assign a `MagicMock` to `svc.ctx.services_required.lifecycle.cleanup_server_resources`, send a payload that removes an MCP server plus an invalid section, and assert the cleanup mock was not called and the outcome `needs_restart` is empty.
6. Add `test_valid_reload_applies_everything` (new) [T-004]: send a fully valid payload and assert every section, direct field, the `system_prompt_tool` conv update, and services are applied, with the outcome categories populated.
7. Run the regression gate (`uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py tests/agent/commands/test_agent_cmd_config.py`) and confirm AC-005 (no validator/registry change) holds.

### Imports

Declare at the top of the file, in addition to the existing imports: the standard-library `copy` helper `deepcopy` for snapshotting section values; `unittest.mock` `patch` (or direct `MagicMock` assignment) for mocking `_sync_services` and the lifecycle cleanup; the `pytest` `raises` context manager; and the `agent.services.exceptions.ConfigReloadValidationError` and `agent.services.models.ConfigReloadRequest` classes. Do NOT emit literal import statements in this procedure — describe them as above in the written file.

### Method

The new class mirrors `TestApplyConfig`: it takes the existing fixtures, supplies `new_cfg` payloads, and asserts on live state and mocked side effects. Illustrative reference skeleton for T-001 (adapt; do not copy verbatim; imports are declared at the file top per the Imports note):

```
import copy

import pytest


class TestConfigReloadAtomicity:

    def test_invalid_tool_leaves_live_config_unchanged(self, svc_with_ctx):
        svc, ctx = svc_with_ctx
        svc._sync_services = MagicMock()
        before_llm = copy.deepcopy(ctx.cfg.llm)
        payload = {
            "llm": {"llm_temperature": 0.2},
            "rag": {"embed_url": "http://localhost:8080/embed"},
            "tool": {"llm_max_tokens": -1},
        }
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(payload)
        assert ctx.cfg.llm == before_llm
        svc._sync_services.assert_not_called()

    def test_direct_fields_unchanged_on_later_failure(self, svc_with_ctx):
        svc, ctx = svc_with_ctx
        before_allowed = list(ctx.cfg.tool.allowed_tools)
        before_system = ctx.conv.system_prompt_content
        payload = {
            "allowed_tools": ["a", "b"],
            "system_prompt_tool": "new system prompt",
            "tool": {"llm_max_tokens": -1},
        }
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(payload)
        assert list(ctx.cfg.tool.allowed_tools) == before_allowed
        assert ctx.conv.system_prompt_content == before_system

    def test_mcp_cleanup_not_run_on_validation_failure(self, svc_with_ctx):
        svc, ctx = svc_with_ctx
        ctx.services_required.lifecycle.cleanup_server_resources = MagicMock()
        payload = {
            "mcp_servers": {"removed": {"endpoint": "http://x"}},
            "tool": {"llm_max_tokens": -1},
        }
        outcome = svc.apply_config_dict(payload)
        ctx.services_required.lifecycle.cleanup_server_resources.assert_not_called()
        assert outcome.needs_restart == []

    def test_valid_reload_applies_everything(self, svc_with_ctx):
        svc, ctx = svc_with_ctx
        outcome = svc.apply_config_dict(
            {"llm": {"llm_temperature": 0.2}, "rag": {"embed_url": "http://y"}}
        )
        assert ctx.cfg.llm.llm_temperature == 0.2
        assert outcome.applied
```

The three failure-path tests assert both the raised `ConfigReloadValidationError` and that no live state changed and no side effect ran; the happy-path test asserts the sections were applied and the outcome categories are populated.

### Details

- **`REQ-001` / `REQ-003` / `AC-001` / `AC-003` (T-001, T-002):** the failure-path tests assert `ConfigReloadValidationError` is raised and every live section, direct field, and the `ctx.conv` field equal their pre-call snapshots; the failure message still names the failing field via the existing validator wrapping.
- **`REQ-004` / `AC-004` (T-003):** the MCP test asserts `cleanup_server_resources` is not called and `needs_restart` is empty on a payload that also contains an invalid section.
- **`REQ-007` / `AC-002` (T-004):** the happy-path test asserts a fully valid payload applies every section, direct field, and conv update with outcome categories populated.
- **`AC-005`:** the tests add no validator or registry entry; existing reload tests pass or are updated with explicit justification.

## Compatibility considerations

- Purely additive test class; no existing test or source file is modified, so the existing error-path and classification suites keep passing.

## Security considerations

- Test-only additions; the invalid payloads exercise validator failures in-process. No new input surface or secret handling.

## Rollback considerations

- Remove the appended test class (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/services/test_config_reload.py` | New atomicity cases | `uv run pytest tests/agent/services/test_config_reload.py` | T-001..T-004 pass |
| Existing behavior | Regression (unchanged) | `uv run pytest tests/agent/services/test_config_reload_classification.py tests/agent/commands/test_agent_cmd_config.py` | Pass unchanged |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- The new TestConfigReloadAtomicity class has four passing tests covering AC-001, AC-002, AC-003, AC-004; the regression gate passes unchanged; `mypy` / `ruff` pass.

## Out of Scope

- Source reordering (`scripts/agent/services/config_reload.py`, row 01; `scripts/agent/services/config_section_reload.py`, row 02).
- The hot-reload doc (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Prepare/apply split (row 02) | Pending | — | — | Dependency |
| 2 | Two-phase reorder (row 01) | Pending | — | — | Dependency |
| 3 | Regression tests (this row) | In Progress | — | — | REQ-001, REQ-003, REQ-004, REQ-007 |
| 4 | Hot-reload doc (row 04) | Pending | — | — | REQ-001, REQ-003 |
| 5 | Run validation sequence | Pending | — | — | pytest/mypy/ruff |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261026-224903_config001_make-config-reload-atomic.md`
- **Source plan**: `plans/20261027-073638_config001_make-config-reload-atomic.md`
- **Generated at**: 20261027-113958
- **Related target files**: `tests/agent/services/test_config_reload.py`
