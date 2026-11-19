## Goal

Add the five rejection tests (written first, RED against current code) and convert the approval fixtures from `MagicMock` to real `ApprovalConfig` instances in this suite (REQ-001: invalid tier/risk/root rejections; REQ-002: `allowed_tools` type rejection; REQ-006: approval values keep applying through the validated path).

## Scope
**Release unit**: hot-reload-validation

- In scope: new test methods and fixture changes in this file only (Plan Phase 1 + Phase 2 fixture conversion).

## Assumptions
- Phase 1 ordering: the rejection tests fail (`ConfigReloadValidationError` not raised) until the seq 01/02/03 wiring lands; the Plan's Release units entry validates Phase 1+2 as one unit.
- Fixture conversion is forced by `dataclasses.replace` on the live section: `prepare_validated_section` calls it whenever an approval field changed (`config_section_reload.py:54-56`), and `replace` raises `TypeError` on a `MagicMock` — the same reason this suite already builds real `LLMConfig` / `ToolConfig` fixtures (`test_config_reload.py:33-46`).
- `ApprovalConfig` defaults are constructible with an empty `allowed_root` (no `__post_init__` root check at construction; `config_dataclasses.py:310,316-319`), so fixture construction stays simple.

## Design decisions
- Rejection tests assert all three of: `ConfigReloadValidationError` raised, the previous live value unchanged, and (for one test) an unchanged approval section survives an unrelated invalid reload (Plan Tests section).
- The two existing dual-branch tests keep their structure; after the change they pass through their `except ConfigReloadValidationError` branch (`:663-712`), preserving the observable fail-closed assertion.

## Alternatives considered
- Rewrite the dual-branch tests into pure rejection tests: rejected — the Plan keeps their accept-branch structure as the record of the old behavior, and the rejection branch already carries the new contract.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`

### Procedure
1. Phase 1 (before any code change): add to the class that owns the `svc_with_ctx` fixture five tests — `test_invalid_tool_safety_tier_rejected` (new), `test_invalid_approval_risk_level_rejected` (new), `test_empty_allowed_root_rejected` (new), `test_non_absolute_allowed_root_rejected` (new), `test_non_string_allowed_tools_entry_rejected` (new) — each: set a valid live value, call `svc.apply_config_dict` with the invalid new value, assert `ConfigReloadValidationError`, assert the live value is unchanged. `allowed_root` invalid inputs: `""` and `"/relative/path"`; `allowed_tools`: `["read_file", 42]`.
2. Add one cross-section test — `test_unchanged_approval_survives_unrelated_invalid_reload` (new): an invalid `tool_safety_tiers` value aborts the reload while a separately changed, valid `tool`-section value is also not applied (candidate-phase abort, AC-001).
3. Phase 2 (after seq 01/02/03 land): convert fixtures — in the module fixture builder replace `ctx.cfg.approval = MagicMock()` and its three attribute assignments (`:103-106`) with `ctx.cfg.approval = ApprovalConfig(tool_safety_tiers={}, require_approval_for=[], plan_mode_enabled=False)`; in `TestApprovalGitopsPushBlocked._make_svc` (`:718-744`) replace the `ctx.cfg.approval.*` attribute assignments with `ctx.cfg.approval = ApprovalConfig(gitops_push_blocked=gitops_push_blocked)`.
4. Run the file: the five new tests plus `test_reload_empty_allowed_tools_fails_closed` and `test_reload_empty_allowed_root_fails_closed` (`:663-712`) pass through their rejection branches; `TestApprovalGitopsPushBlocked` (`:746-786`) still asserts application of `gitops_push_blocked` (`startup_only` report unchanged).

### Method
- New tests reuse the existing `svc` / `svc_with_ctx` fixtures; no new fixture variants — the converted approval fixture serves both rejection and application tests.
- The registry assertions at `:912-1031` are membership/callability checks and need no edit; they stay green with the wiring.

### Details
- Keep imports local to test bodies as the file already does (`from agent.services.exceptions import ConfigReloadValidationError`); add `ApprovalConfig` to the existing dataclass import line at the top of the file.
- `test_reload_empty_allowed_root_fails_closed` keeps its `check_allowed_root` denial path in the (now unreachable) accept branch per the Plan's Regression bullet — do not delete the branch.

## Compatibility considerations
- These tests fail standalone between Phase 1 and the seq 01/02/03 landing — expected RED state inside the release unit, not a broken main.

## Security considerations
- The five tests are the regression lock for the reload gate on the four security-relevant fields.

## Rollback considerations
- N/A: revert the commit (tests land with the wiring in one unit).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Pre-wiring RED | `uv run pytest tests/agent/services/test_config_reload.py -q` (Phase 1) | Five new tests fail with no `ConfigReloadValidationError` |
| Post-wiring GREEN | `uv run pytest tests/agent/services/ -q` | New tests and converted tests pass |
| Gates | `rules/toolchain.md` sequence incl. diff-cover ≥ 90 % on the unit diff | Pass |

## Completion criteria
- All five rejection tests and the cross-section test pass; both dual-branch tests pass via their rejection branch; `gitops_push_blocked` application tests pass with real fixtures; no test still models `ctx.cfg.approval` as a `MagicMock` while applying approval fields.

## Out of Scope
- Fixture conversion of `tests/agent/commands/test_agent_cmd_config.py` (seq 07 document); any production-code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the five rejection tests and the cross-section test (Phase 1, expect RED pre-wiring) | Pending | — | — | Must be written before seq 02/01/03 edits |
| 2 | Convert approval fixtures to real `ApprovalConfig` (after seq 01-03 land) | Pending | — | — | REQ-006 fixture conversion |
| 3 | Run `tests/agent/services/` and confirm rejection branches | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (rejection tests), REQ-002 (`allowed_tools` type rejection), REQ-006 (fixture conversion keeps approval applying)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `tests/agent/services/test_config_reload.py`
