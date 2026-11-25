## Goal

Give the field registry the declared type and emptiness rule for every entry, and make the reload
path read only hot-reloadable entries so startup-only fields cannot be applied (REQ-001, declared
type; REQ-003, startup-only separation; REQ-010, registry completeness).

## Scope
**Release unit**: R2-typed-registry

## Assumptions
- Verified against current source: `registry_for` (`config_field_registry.py:103-105`) filters only
  on `section_path` and ignores `hot_reloadable`; the table has 33 entries, 18 without a validator.
- `tests/agent/test_config_effective_snapshot.py` pins the registered-field inventory; adding
  `field_type` (new) and `allow_empty` must keep that contract valid or be re-measured (UNK-04).
- The validator references added here are the functions row 3 creates or already defines.

## Design decisions
- `field_type` (new) is a `FieldRule` from `scripts/shared/config_field_types.py`, so the registry declares
  the rule the validator composes; there is no second source of the type rule.
- `allow_empty` is a per-entry flag resolved in this row (UNK-05), and the parity test pins the
  chosen value for each entry.

## Alternatives considered
- Keeping `validator_fn` as the only field and inferring the type from the dataclass — rejected: the
  dataclass is built after validation, so the type rule must be declared before it.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
Add `field_type` (new) and `allow_empty` to `ConfigFieldRegistry`, filter `registry_for` to
`hot_reloadable=True`, add `startup_only_for(section)`, and wire the validators the registry does not
import today.

### Method
- `startup_only_for` (new) returns the entries with `hot_reloadable=False` for a section.
- `registry_for` keeps its signature and adds the `hot_reloadable` filter.
- Every entry declares `field_type` (new); the 18 entries without a validator now reference the row 3
  functions, including `validate_memory_retention_days` and `validate_memory_max_pinned`.

### Details
- The startup-only entries the Plan names are `context_token_limit`, `context_char_limit`,
  `context_compress_turns`, `gitops_push_blocked`, `approval_medium_preview_fallback`,
  `use_memory_layer`, `memory_embed_enabled`; `startup_only_for` (new) must return exactly those.
- `CONFIG_FIELD_REGISTRY` stays the name the generated ownership manifest reads
  (`tools/generate_reference_table.py`, `CONFIG_FIELD_REGISTRY_SRC`).

## Compatibility considerations
- `registry/manifests/config_ownership.yaml` is generated from this module and is regenerated in
  row 45, not hand-edited.
- `tests/agent/services/test_config_reload.py` gains a new test class
  `TestConfigFieldRegistrySectionCategorization` (new); it does not exist today.

## Security considerations
- No configuration value is logged or echoed by the registry.

## Rollback considerations
- Revert the Phase 2 commit; the registry is a static table.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_parity.py tests/agent/services/test_config_reload.py tests/agent/test_config_effective_snapshot.py -q`
- `uv run python tools/generate_reference_table.py --check --manifests`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- Every entry declares a type and a validator, `registry_for` returns only hot-reloadable entries,
  and the ownership manifest regenerates without drift.

## Out of Scope
- The validator bodies (row 3).
- The reload candidate phase (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-154000 | 20261125-163000 | UNK-05 decides `allow_empty` here field_type and allow_empty added; all 33 entries carry a validator; registry_for filters hot_reloadable; startup_only_for added |
| 2 | Add or update tests per Validation plan | Completed | 20261125-154000 | 20261125-163000 | rows 27, 34 TestConfigFieldRegistrySectionCategorization in tests/agent/services/test_config_reload.py (4 tests) plus row 27 parity table pins allow_empty |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-154000 | 20261125-163000 | manifests regenerated earlier in R2: registry/manifests/config_ownership.yaml plus agent_api.yaml and the generated subpackage doc; --check reports no drift |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-003 (startup-only fields stay pending), REQ-010 (registry completeness); AC-1, AC-2, AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_field_registry.py`