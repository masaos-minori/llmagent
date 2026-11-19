## Goal

Add `validate_allowed_root` (new) and `validate_allowed_tools` (new) to the reload-side validator module so the four security-relevant fields have validators with the startup rules (REQ-001: invalid approval values rejected on reload; REQ-002: `allowed_tools` type check with empty list valid).

## Scope
**Release unit**: hot-reload-validation

- In scope: two new module-level validator functions in this file; `validate_tool_safety_tiers` / `validate_approval_risk_rules` (`config_validators.py:211-231`) stay byte-unchanged (REQ-003: no signature change).

## Assumptions
- `validate_allowed_root` raises `ValueError`, not `ConfigReloadValidationError`: `prepare_validated_section` converts any `ValueError` from a validator into `ConfigReloadValidationError` (`config_section_reload.py:56-67`), matching how `validate_approval_risk_rules` already signals.
- Startup enforces non-empty `allowed_root` as a hard rule (`config_section_builders.py:303-306`); the absolute-path wording there and in `production_config_validator.py:284-291` is advisory. Per the Plan's frozen row (`validate_allowed_root(cfg: ApprovalConfig)`, non-empty, `os.path.isabs`), reload enforces both — stricter than startup in that one dimension, compatible with the live production value `allowed_root = "/opt/llm"` (`config/agent.toml:236`). Recorded in the Plan's Assumptions.
- `ApprovalConfig` / `ToolConfig` are already imported under `TYPE_CHECKING` (`config_validators.py:19-26`); annotations are strings via `from __future__ import annotations`, so no runtime import change is needed for the parameter types.
- `ToolConfig.allowed_tools` is a real dataclass field (`config_dataclasses.py:217`), so the candidate passed by `prepare_validated_section` carries the new value.

## Design decisions
- `validate_allowed_tools` checks `isinstance(value, list)` and that every entry is `str`; an empty list is valid (Plan DT-02 Option A: empty is the fail-closed setting startup accepts).
- Error messages name the field and the offending value, following the existing `validate_approval_risk_rules` / `validate_tool_safety_tiers` message style.

## Alternatives considered
- Accept non-absolute `allowed_root`: rejected — the frozen row and the source Issue state non-empty absolute path, and the live value is absolute.
- Call `ProductionConfigValidator` instead: rejected — its tier completeness checks are production-profile/startup-only (Plan Known limitation, UNK-03).

## Implementation
### Target file
`scripts/agent/services/config_validators.py`

### Procedure
1. Add a module-level `import os` to the existing import block (after `from __future__ import annotations`, before `from collections.abc import Mapping`).
2. Add `validate_allowed_root` (new) next to `validate_approval_risk_rules` / `validate_tool_safety_tiers` (`:211-231`): raise `ValueError` when `not cfg.allowed_root.strip()` or `not os.path.isabs(cfg.allowed_root)`.
3. Add `validate_allowed_tools` (new) near the existing `tool`-section validators: raise `ValueError` when `cfg.allowed_tools` is not a `list` or any entry is not a `str`.
4. Leave every existing validator unchanged; do not touch the module docstring's stated contract.

### Method
- Signatures follow the existing section-dataclass shape: `def validate_allowed_root(cfg: ApprovalConfig) -> None` and `def validate_allowed_tools(cfg: ToolConfig) -> None` — the same shape `prepare_validated_section` invokes with `validator(replaced)`.
- Non-empty check mirrors `config_section_builders.py:303-306` (`not allowed_root.strip()`); the message states that an empty value would disable the path jail.

### Details
- Do not validate `allowed_tools` entry membership against the tool registry: unknown names are already handled by `apply_policy` fail-closed semantics (Plan REQ-002 scope is type only).
- Do not re-run tier/risk validation inside these new functions: `ApprovalConfig.__post_init__` (`config_dataclasses.py:316-319`) already runs `validate_approval_risk_rules` / `validate_tool_safety_tiers` on the candidate built by `dataclasses.replace`.

## Compatibility considerations
- New functions only; no existing validator, import, or signature changes — `config_dataclasses.py` (the only other importer) is unaffected.
- The functions are inert until the seq 01 document wires them into `CONFIG_FIELD_REGISTRY` and the seq 03 document moves `approval` to the validated path.

## Security considerations
- These validators are the reload-side gate for the path jail (`allowed_root`) and tool visibility (`allowed_tools`); a rejection aborts the whole reload before any live mutation (`config_reload.py` candidate phase).

## Rollback considerations
- N/A: revert the commit (single release-unit commit with seq 01/03/04/06/07).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| New validator rejections | `uv run pytest tests/agent/services/test_config_reload.py -q` | The five rejection tests (seq 06 document) pass once wiring (seq 01/03) lands |
| Static gates | `rules/toolchain.md` sequence (`uv run python tools/run_validation_gates.py --full`) | ruff / mypy clean on the new functions |

## Completion criteria
- Both new validators exist with the frozen signatures and raise `ValueError` on their invalid inputs; an empty `allowed_tools` list passes; all existing validators are byte-unchanged; the suite and static gates pass.

## Out of Scope
- Wiring into the registry (seq 01 document); the reload loop move (seq 03 document); production-profile completeness checks (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `import os` and the two new validator functions | Completed | 20261119-104925 | 20261119-104950 | Lands with the release unit; seq 06 tests are written first Step 2 stale check clean; Step 3a: signatures, ApprovalConfig post-init, registry/consumer checks verified against current source; file clean at baseline Changed: scripts/agent/services/config_validators.py (import os, validate_allowed_tools, validate_allowed_root). Direct check: empty list ok; None/non-str rejected; empty/blank/relative root rejected, /opt/llm ok |
| 2 | Run the new rejection tests after seq 01/03 wiring lands | Completed | 20261119-112102 | 20261119-112102 | Pre-wiring they fail by design (Plan Phase 1) Rejection tests pass after wiring (seq 01/03): test_config_reload.py 69 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-112102 | 20261119-112102 | End of unit: full suite 12907 passed, 7 skipped, 1 unrelated failure (test_check_repo_path_equivalence: Hypothesis property test on PurePosixPath, passes alone 9/9 and in the git MCP module under xdist 418/418); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass; ruff/mypy/lint-imports/bandit clean |

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
- **Requirement ID**: REQ-001 (invalid approval values rejected on reload), REQ-002 (`allowed_tools` type check), REQ-003 (no signature changes)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `scripts/agent/services/config_validators.py`