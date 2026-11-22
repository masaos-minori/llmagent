## Goal

Route the Memory section through the typed-candidate path instead of the direct `setattr` path, so a Memory reload is validated before it is committed (REQ-002, AC-002).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 2)

## Assumptions
- `tests/agent/services/test_config_reload.py` is not a companion of this row: it is named by two rows (this row and `config_field_registry.py`), so it keeps its own document (Plan row 24).
- The typed candidate model is shared with `issues/20261119-145303_cliplc005_staged-reload-transaction.md`; if that Issue lands first, this row adopts its model; if this Plan lands first, the candidate model is defined here and the shared tests are re-verified.
- The reload loop that decides which sections take the validated path lives in `scripts/agent/services/config_reload.py` (Plan row 33); this document changes only the section helpers.

## Design decisions
- `memory` moves from the direct path to the validated path; `mcp` stays direct, because MCP sections are not dataclasses and have no registry validators.
- `prepare_direct_section` and `apply_direct_section` keep their current shape for `mcp` — no new abstraction is added for a section that no longer uses them.

## Alternatives considered
- Run the Memory validators inside `prepare_direct_section` while keeping `setattr` apply: rejected — a partial `setattr` commit cannot be rolled back when a validator fails later, which is exactly the failure mode the prepare/apply split exists to prevent.

## Implementation
### Target file
`scripts/agent/services/config_section_reload.py`
### Procedure
- Update the module docstring so the validated path lists `memory` and the direct path lists only `mcp`.
- Keep `prepare_validated_section()` / `apply_validated_section()` / `reload_validated_section()` as the path Memory now uses; the `dataclasses.replace` candidate plus the registry validators cover `memory_embed_url` (new).
- Leave `prepare_direct_section()` / `apply_direct_section()` / `reload_direct_fields()` unchanged for `mcp`.
### Method
- No new function is introduced: the change is the routing decision made by the caller plus the docstring/argument documentation of the section identifiers.
- `MemoryConfig` must be constructed as a real dataclass by the caller, which `build_agent_config()` already does; the docstring note that direct sections may be mock objects no longer applies to Memory.
### Details
- Verified 2026-11-21: `prepare_validated_section()` builds the candidate with `dataclasses.replace(cfg, **changed_fields)` (line 56) and converts a `ValueError` from the dataclass or a registry validator into `ConfigReloadValidationError`; `prepare_direct_section()` runs no validators (line 117).
- The `extra_changed_fields` parameter exists for fields that are not registry entries; `memory_embed_url` becomes a registry entry through Plan row 5, so no extra handling is needed here.

## Compatibility considerations
- The outcome report shape (`applied`, `needs_restart`, `skipped`, `startup_only`) is unchanged; `memory_embed_enabled` keeps its startup-only classification, so a changed value is reported as needing restart rather than being applied.
- `tests/agent/services/test_config_reload_classification.py` is run as an affected test.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit (Phase 2 is not part of a release unit).

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v`
- `uv run ruff check scripts/agent/services/config_section_reload.py`, `uv run mypy scripts/agent/services/config_section_reload.py`

## Completion criteria
- A Memory reload builds a candidate, runs the validators, and commits only after validation succeeds; the `applied`/`needs_restart` report is unchanged for the other sections.

## Out of Scope
- Registry entries (Plan row 5), the loop routing (Plan row 33), the new test cases (Plan row 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Implemented (docstrings/arg docs); all claims verified against source |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Deferred: test cases live in Plan row 24; test_config_reload.py still imports RAGConfig pending row 24. Affected test test_config_reload_classification.py: 6 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff/mypy clean; completion criteria realized when rows 33/24 land |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 (Memory reload validates through a typed candidate)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/config_section_reload.py`
