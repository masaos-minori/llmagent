## Goal

Make every registry validator compose the declared type rule before its range rule, and give the 18
registry entries that have no validator a validator, so reload validates the same values startup
validates (REQ-001, type-then-range composition; REQ-010, registry completeness).

## Scope
**Release unit**: R2-typed-registry

## Assumptions
- The type rule comes from `scripts/shared/config_field_types.py` (row 1); this module composes it
  with the existing range check rather than re-implementing it.
- Verified against current source: `config_validators.py` already defines
  `validate_memory_retention_days` (`config_validators.py:210`) and `validate_memory_max_pinned`
  (`config_validators.py:215`), but `config_field_registry.py` does not reference them, so those two
  entries are wired, not created.
- `memory_min_importance` is not a registry entry (`config_field_registry.py:64-100`), so it is out
  of scope here; the Plan's `Newly rejected inputs` list was corrected for this.

## Design decisions
- A validator takes the section dataclass and the field path; the type check runs on the raw payload
  value before the range check, so a wrong-typed value never reaches a range comparison.
- New validators are named `validate_<section>_<field>` to match the existing convention.

## Alternatives considered
- Validating types in the registry layer instead of in the validator — rejected: the registry holds
  metadata only, and the range rules already live here.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`

### Procedure
Compose the declared type rule before the range rule in every validator, and add the missing
validators for the 18 entries with `validator_fn=None`.

### Method
- Add `validate_context_compress_turns` (new), `validate_llm_url` (new),
  `validate_llm_stream_retry_on_heartbeat_timeout` (new),
  `validate_llm_stream_retry_on_malformed_chunk` (new), `validate_serial_tool_calls` (new),
  `validate_plan_blocked_tools` (new), `validate_approval_protected_paths` (new),
  `validate_approval_high_risk_branches` (new), `validate_approval_shell_safe_prefixes` (new),
  `validate_approval_github_allowed_repos` (new), `validate_gitops_push_blocked` (new),
  `validate_approval_medium_preview_fallback` (new), `validate_memory_local_only` (new),
  `validate_use_memory_layer` (new), `validate_memory_embed_enabled` (new),
  `validate_memory_embed_url` (new).
- Existing range-only validators (`validate_llm_temperature`, `validate_llm_max_tokens`,
  `validate_allowed_tools`, `validate_disabled_tools`, `validate_tool_policy_mode`) gain the type
  rule ahead of the range rule.

### Details
- Every raised message names the field and the rule and excludes the raw value; the current
  `got {value!r}` wording in `config_validators.py:67-73` is replaced.
- List-valued fields use the shared `strict_str_list` rule with the `allow_empty` flag the registry
  declares (row 4).

## Compatibility considerations
- Blast radius: the registry maps every entry into this module, so a stricter validator changes what
  reload accepts. The Plan's `Newly rejected inputs` list is the published review surface.
- The acceptance of `memory_local_only=1` and `context_compress_turns='77'` was confirmed by a probe
  during Plan analysis, not by an existing test assertion; the newly rejected inputs are covered by
  the parity tests (row 27), and row 34 retargets the reload tests that pin current accept behavior.

## Security considerations
- `approval_protected_paths`, `approval_github_allowed_repos`, and `memory_embed_url` can carry
  paths and tokens; error text must not echo them.

## Rollback considerations
- Revert the Phase 2 commit; validators are stateless.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_parity.py tests/agent/services/test_config_reload.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- No registry entry has `validator_fn=None`, and every validator rejects a wrong-typed value before
  evaluating its range.

## Out of Scope
- The registry wiring itself (row 4) and the `allow_empty` values (UNK-05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-154000 | 20261125-163000 | every existing validator composes the shared strict primitive before its range helper; 16 new validators added; field path is the bare config key name so both paths raise identical text (AC-1) |
| 2 | Add or update tests per Validation plan | Completed | 20261125-154000 | 20261125-163000 | rows 27, 34 row 27 parity file (100 passed) plus TestValidatorTypeRuleBeforeRange in tests/agent/test_config_dataclasses.py covers the startup-only validators |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-154000 | 20261125-163000 | R2 unit gate: full suite 14588 passed 5 skipped, diff-cover 100 percent, integration 146 passed 1 skipped, lint-imports 6 kept, generate_reference_table --check no drift, check_docs_structure passed, ruff and mypy clean |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-010 (registry completeness); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_validators.py`