## Goal

Move the `embed_url` field-registry entry from the `rag` section to the `memory` section under the new key name, so the reload path classifies the endpoint as a Memory setting (REQ-001, REQ-002, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/services/test_config_reload.py` is not a companion of this row: it is named by two rows (this row and `config_section_reload.py`), so it keeps its own document (Plan row 24).
- The registry entry keeps its live-reloadable flag (`True`); only the section path and key name change.

## Design decisions
- The entry key becomes `memory_embed_url`, matching the dataclass field name, because the registry maps the key the user writes in the owning file to the section that owns it (the Plan's Design D4).
- The Memory section's existing entries (`memory_retention_days`, `memory_max_pinned`, `memory_local_only`, `use_memory_layer`, `memory_embed_enabled`) are left in place; only the endpoint entry is added, so the startup-only classification for `memory_embed_enabled` is untouched.

## Alternatives considered
- Keep the key name `embed_url` under `memory`: rejected — AC-006 requires the old key location to be rejected as an unknown key, and a key named `embed_url` inside the Memory section would keep the ambiguous name the Problem is about.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`
### Procedure
- Replace `ConfigFieldRegistry("embed_url", "rag", True)` (line 71) with the entry for `memory_embed_url` (new) in the `memory` section, keeping the live-reloadable flag.
- Remove the `rag` section identifier from the registry's documented section list if the module lists it.
### Method
- One registry entry change; no change to the registry dataclass or to the lookup helpers.
### Details
- Verified 2026-11-21: the `memory` section entries exist at lines 103-107, so the new entry joins an existing section and no new section handling is required.
- `tests/agent/services/test_config_reload.py` asserts the exact set of `memory`-section entries by filtering `entry.section_path == "memory"`; that assertion gains the new key and is updated by Plan row 24, not here.

## Compatibility considerations
- The reload loop that iterates the validated sections lives in `scripts/agent/services/config_reload.py` (Plan row 33); this document must not change it.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -v`
- `uv run ruff check scripts/agent/services/config_field_registry.py`, `uv run mypy scripts/agent/services/config_field_registry.py`

## Completion criteria
- The endpoint key resolves to the `memory` section; no registry entry maps a key to `rag`.

## Out of Scope
- Typed-candidate construction for the Memory section (Plan row 6) and the reload loop routing (Plan row 33).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model REQ-002 validates through is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - assertions live in Plan row 24 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

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
- **Requirement ID**: REQ-001, REQ-002 (field-registry mapping for the Memory-owned key)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/config_field_registry.py`
