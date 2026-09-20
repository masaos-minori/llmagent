# Implementation Procedure: Review config_dataclasses.py — default consolidation status

## Goal

Verify whether `scripts/agent/config_dataclasses.py` needs any adjustments as a result of REQ-003 (consolidate default values). Current evidence shows defaults are already consolidated into dataclass field definitions.

## Scope

Review only — no modification targets confirmed. This document exists because the Plan lists `config_dataclasses.py` as a secondary target file (REQ-003), but adversarial verification found no changes needed.

## Assumptions

- The defaults consolidation strategy from the Plan applies: move defaults from `_extract_*_fields` extractors to their respective dataclass field defaults where domain-appropriate.
- For cross-domain defaults (approval-related), keep them in `constants.py` as `_DEFAULT_*` tables.
- All 9 dataclasses already have `__post_init__` methods that can absorb inline validation from REQ-004.

## Design decisions

1. **No changes required**: Adversarial verification against current source confirms that all 9 dataclasses already have defaults consolidated into field definitions. The `_extract_*_fields` → dict → spread anti-pattern removal in `config_builders.py` does not require changes here.
2. **Validation migration**: `ApprovalConfig.__post_init__` already calls `_v_app_tier(self)` which validates tier values — no additional validation needed.
3. **Default sources**: `constants.py` is the canonical source for 6 `_DEFAULT_*` tables; dataclass field defaults are the source for domain-specific defaults.

## Alternatives considered

1. **Move more defaults to `constants.py`**: Would centralize all defaults but would violate the design decision that domain-specific defaults belong in dataclass field definitions.
2. **Remove `__post_init__` validators**: Would simplify the dataclass but would lose validation guarantees.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

No modifications required. The following sections confirm each dataclass's default state.

### Method

#### Verification of each dataclass

**LLMConfig (lines 130–155)**: All defaults already in field definitions. No changes needed.

**RAGConfig (lines 158–173)**: All defaults already in field definitions. No changes needed.

**ToolConfig (lines 176–234)**: All defaults already in field definitions. Includes `_DEFAULT_PLAN_BLOCKED_TOOLS` reference. No changes needed.

**MemoryConfig (lines 237–273)**: All defaults already in field definitions. No changes needed.

**MCPConfig (lines 276–289)**: Defaults already in field definitions. No changes needed.

**ApprovalConfig (lines 292–334)**: All defaults already in field definitions. Includes `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_PROTECTED_PATHS`, `_DEFAULT_SHELL_SAFE_PREFIXES`, `_DEFAULT_RESOURCE_KEYS`, `_DEFAULT_DRY_RUN_TOOLS` references. No changes needed.

**ObservabilityConfig (lines 337–348)**: Defaults already in field definitions. No changes needed.

**DiagnosticsConfig (lines 351–364)**: Defaults already in field definitions. No changes needed.

**MessageRoleConfig (lines 368–373)**: Defaults already in field definitions. No changes needed.

**AgentConfig (lines 398–437)**: Composite config with nested defaults. No changes needed.

## Compatibility considerations

- No changes means no compatibility impact.
- Public API boundary remains unchanged.

## Security considerations

- No changes means no security impact.

## Rollback considerations

- No rollback needed since no changes are made.

## Validation plan

N/A — no changes to validate.

## Completion criteria

- [x] Verified all 9 dataclasses have defaults consolidated into field definitions
- [x] Verified `__post_init__` methods exist for all dataclasses requiring validation
- [x] Confirmed no additional defaults need to be moved from `config_builders.py` extractors

## Out of scope

- Modifying `scripts/agent/config_builders.py` (covered by separate procedure)
- Modifying `scripts/agent/constants.py` (canonical source already established)
- Adding new validators or changing existing ones

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify default consolidation status for config_dataclasses.py | Completed | — | 20260920-122128 | Verified all 9 dataclasses
| 2 | Add or update tests per Validation plan | N/A | — | — | No changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | N/A | — | — | No changes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No changes |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260920-104548_refactor_001_config_builders_extract_fields_anti_pattern.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-112141_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-114755
- **Related target files**: scripts/agent/config_dataclasses.py
