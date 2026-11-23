## Goal

Hold the removed-key → replacement mapping as the single source in the validator (REQ-002 - single-source migration mapping) and make each key in `_REMOVED_PRODUCTION_KEYS` a fatal error that names its replacement (REQ-003 - per-key migration error).

## Scope
**Release unit**: N/A: not part of a release unit

One file is modified: the production validator. The companion test file adds the per-key assertions.

## Assumptions
- The per-key message keeps the `Unknown config keys` prefix and names the replacement (design D3, corrected by Step 3a on 2026-11-22), because the pinned assertions pass mapped keys through the validation path: `tests/agent/test_production_config_validator.py` lines 188-265 and 467, 494, `tests/shared/test_shared_boundary_conditions.py` line 179, `tests/integration/test_production_security_regression.py` line 50.
- Overlap with the Frozen plan mcpdl003 on this file judged compatible: that plan extends the valid-key table; this row adds the removed-key message. No sequencing dependency.
- ADR-002 governs the unknown-key rejection; this row adds guidance to the existing fatal path, not a policy change. If the implementer finds the message change to be an ADR decision change, stop and request the approval record.

## Design decisions
- Module-level constant `_REMOVED_KEY_REPLACEMENTS` (new) maps every key in `_REMOVED_PRODUCTION_KEYS` (line 66) to its replacement (new key or owning file); it is the single source read by both the error message here and the generator in sibling procedure seq 04.
- The mapping stays in the `agent` layer; `tools/` is outside the `.importlinter` contract graph and `tests/conftest.py` puts `scripts/` and `tools/` on `sys.path`, so the generator can import it as it already reads `scripts/db/config.py`.

## Alternatives considered
A single combined message with a migration suffix was rejected (AC-4 requires a specific per-key message). A hand-maintained mapping outside the validator was rejected: it would duplicate the single source.

## Compatibility considerations
No public-contract change beyond error text. Consumers (`scripts/agent/config_builders.py`, `scripts/agent/startup_validation.py`, 8 test modules) do not assert the full message text beyond the prefix, so the format is consumer-safe. Module is 14050 B, below the 24576 B split gate.

## Security considerations
N/A: message content only; no trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
1. Define `_REMOVED_KEY_REPLACEMENTS` (new) as the module-level mapping covering all keys in `_REMOVED_PRODUCTION_KEYS`.
2. In `_check_unknown_production_keys` (lines 263-274), emit the per-key fatal message for mapped keys; keep the generic `Unknown config keys: {list}` path unchanged for unmapped keys.
### Method
Per-key error format per corrected design D3: `Unknown config keys: <key> — replaced by <new key or owning file>`. The prefix-preserving form keeps every existing message-substring assertion valid.
### Details
- Replacement values reflect the landed agentcfg003 semantics (producer-declared tier, `config/tool_catalog.toml` ownership), corrected by Step 3a on 2026-11-22: the Issue's Background contains no migration mapping, so the values are derived from the landed sources — the validator comment at lines 62-65 (the removed per-tool maps have no compatibility reader), `agent/config_dataclasses.py` `ApprovalConfig` docstring (REQ-005), `agent/tool_approval.py` lines 65-71 (REQ-009), `agent/tool_policy.py` `classify_risk` docstring (REQ-004/REQ-011), and ADR-003 amendment (2026-11-21). Owner confirmed the derived mapping on 2026-11-22: `tool_safety_tiers` → per-tool `agent_safety_tier` in `config/tool_catalog.toml`; `approval_risk_rules` → the declared `agent_safety_tier` as the single risk source (no config replacement key); `approval_resource_keys` → per-tool `resource_scope_keys` in `config/tool_catalog.toml`; `approval_dry_run_tools` → per-tool `preview_capability` in `config/tool_catalog.toml`.

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: Add assertions that the error names the replacement for each mapped key (REQ-003, AC-4); do not alter the existing pinned assertions.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py`

## Validation plan
- `uv run ruff format`, `uv run ruff check --fix`, `uv run mypy`, `uv run bandit` on the target.
- `uv run pytest tests/agent/test_production_config_validator.py`; before finalizing the message, also run `tests/shared/test_shared_boundary_conditions.py` and `tests/integration/test_production_security_regression.py` (Risk mitigation).

## Completion criteria
Every mapped key produces a fatal per-key error naming the replacement; unmapped keys keep the generic message; all pinned assertions plus the new per-key assertions pass; the mapping is importable by the seq 04 generator.

## Out of Scope
No change to `config/agent.toml`; no change to the valid-key table (mcpdl003's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the mapping constant and the per-key fatal message per Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | mapping constant + per-key message with the Unknown config keys prefix; values derived from landed agentcfg003 sources (owner confirmed 2026-11-22) |
| 2 | Add per-key assertions in the companion test file per Validation plan | Completed | 2026-11-22 | 2026-11-22 | Companion: `tests/agent/test_production_config_validator.py` 5 tests added; existing pinned assertions unchanged and still passing |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. the three pinned test files | Completed | 2026-11-22 | 2026-11-22 | ruff/mypy/bandit/lint-imports clean; target + 3 pinned test files pass; full suite passed on re-run (first run reported a single non-reproduced pytest failure) |

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
- **Requirement ID**: `REQ-002` (single-source mapping), `REQ-003` (per-key migration error)
- **Source issue**: `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`