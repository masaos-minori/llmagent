## Goal

Remove the strict-key reads from `_build_tool_config` and make an empty `allowed_root` a load error in `_build_approval_config` (REQ-001 strict keys removed, REQ-003 `allowed_root` required).

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/config_section_builders.py` only; builder tests are the Plan row for `tests/agent/test_config_builders.py`.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- The same `allowed_root` condition is also reported by `production_config_validator.py` (own row). The builder check protects the paths that bypass the validator (builders called from the reload path); both use the same rule: not a non-blank string.
- `ConfigReloadValidationError` is already imported in this module (`agent.services.exceptions`) and is the error the other builders raise.

## Design decisions

- Reject in the builder, not in `ApprovalConfig.__post_init__`: direct `ApprovalConfig(...)` constructions in tests and defaults stay valid, and the error names the key.

## Alternatives considered

Defaulting an absent `allowed_root` to a fixed path was rejected: the Plan requires failing, and a default would hide a missing setting.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
1. In `_build_tool_config` (line 179) delete the `tool_definitions_strict=` and `routing_drift_strict=` arguments (lines 185-190).
2. In `_build_approval_config` (line 283) after `allowed_root = _get_str_or_default(cfg, "allowed_root")` (line 304) raise `ConfigReloadValidationError` when `not allowed_root.strip()`.

### Method
- Message example: `allowed_root is empty or absent; an empty value would disable the path jail`; no config values in the message.
- `rg -n "_strict" scripts/agent/config_section_builders.py` must return nothing afterwards.

### Details
- `_build_model(ToolConfig, ...)` would raise on an unknown keyword once the dataclass fields are gone, which is why the arguments must go in the same change.
- The raise happens before `_build_model(ApprovalConfig, ...)` so no partially built object escapes.

## Compatibility considerations

A config without a non-blank `allowed_root` fails to build; the shipped `config/agent.toml` sets it (`/opt/llm`). Test fixtures that relied on the empty default are covered by their own Plan rows (`tests/agent/_config_test_defaults.py` and others).

## Security considerations

Closes the empty-`allowed_root` allow-all hole at config build (ADR-004 Decision Group 1).

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py tests/agent/services/test_config_reload.py -v`.
- `uv run ruff format`/`ruff check` on the file; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- No strict key is read; `_build_approval_config` raises for an empty, blank, or absent `allowed_root`.

## Out of Scope

- Validator and dataclass edits (own rows); disk-existence checks of `allowed_root`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the two strict arguments from `_build_tool_config` | Completed | 20261110-171000 | 20261110-171000 | rg clean |
| 2 | Add the `allowed_root` rejection to `_build_approval_config` | Completed | 20261110-171000 | 20261110-171000 | Raise precedes `_build_model`; message per Method |
| 3 | Run ruff, mypy and the builder/reload tests (after the fixtures rows land) | In Progress | 20261110-171000 | — | ruff/mypy pass on this file; builder/reload tests deferred to the fixture rows (own documents) and the end-of-batch gate |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/config_section_builders.py`
