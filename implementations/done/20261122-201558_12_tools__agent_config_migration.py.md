## Goal

Read the validator's single-source migration mapping and render the agent-config migration table for the new contract-manifest domain (REQ-002), so `tools/generate_reference_table.py --check` can verify the generated block.

## Scope
**Release unit**: RU-1 generator-and-generated-block

New helper module. The domain registration itself lives in sibling procedure seq 04; the committed artifact is seq 13; the destination document is seq 06. Tests are the row's companion (`tests/tools/test_generate_reference_table.py`, plan row 5).

## Assumptions
- `_REMOVED_KEY_REPLACEMENTS` in `scripts/agent/production_config_validator.py` is a plain module-level dict literal, so `ast` parsing resolves it without importing the `agent` layer; the tool must not depend on `scripts/` being importable at run time.

## Design decisions
- Parse the mapping from source with `ast`, following the pattern the tool already uses for `scripts/db/config.py`, rather than importing the validator module.
- The module holds only the mapping read and the table render; the domain dictionaries stay in the tool so `--check`, `--type`, and `--manifests` keep one path.

## Alternatives considered
Putting the generator inside `tools/generate_reference_table.py` was rejected: its recorded baseline equals its current size (50404 B), so any growth fails the `check-module-size-tools` gate (owner decision, 2026-11-22).

## Compatibility considerations
No existing generator domain or output contract changes; the new domain is additive. The module is read-only over `scripts/` source text, so it does not import the `agent` layer and keeps no runtime dependency on `scripts/` being importable.

## Security considerations
N/A: static source read, no execution of the parsed code.

## Rollback considerations
N/A: revert the commit.

## Implementation
### Target file
`tools/_agent_config_migration.py` (new)
### Procedure
1. Read `_REMOVED_KEY_REPLACEMENTS` by parsing the module-level dict literal with `ast`.
2. Render the manifest entries and the table markdown for the `agent_config_migration` domain.
### Method
Deterministic output: rows in the order the mapping declares them, values read from the mapping only, no values copied from documents.
### Details
- Called from `tools/generate_reference_table.py` through `_MANIFEST_BUILDERS` and `_table_from_entries`.

### Companion test files
- `tests/tools/test_generate_reference_table.py`
  - Procedure: Cover the mapping read and the table rendering for the new domain (REQ-002).
  - Validation: `uv run pytest tests/tools/test_generate_reference_table.py`

## Validation plan
- `routing.md` Tools sequence on the new module.
- `uv run python tools/generate_reference_table.py --manifests` writes the committed manifest (sibling procedure seq 13).

## Completion criteria
The module renders the table from the validator mapping, `--check` passes against the committed manifest, and its tests pass.

## Out of Scope
The domain registration (seq 04), the committed manifest (seq 13), the destination document (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the module per Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-23 | RU-1 with seq 04. The mapping is read as source text with `ast` (fail closed: non-dict literal, non-string key/value, duplicate key, or unparseable source raise `ManifestError`), so the module never imports the `agent` layer |
| 2 | Add tests in the companion test file per Validation plan | Completed | 2026-11-22 | 2026-11-23 | `TestAgentConfigMigration` in `tests/tools/test_generate_reference_table.py`: mapping read from source text, manifest-path registration, `--check` covering the domain |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `--check` | Completed | 2026-11-22 | 2026-11-23 | mypy/ruff/bandit clean, `lint-imports` contracts kept; `generate_reference_table.py --check` reports no drift; file coverage 93.6% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docs work is seq 06 |

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
- **Requirement ID**: `REQ-002` (single-source mapping rendered through the generator)
- **Source issue**: `issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-201558
- **Related target files**: `tools/_agent_config_migration.py`, `tests/tools/test_generate_reference_table.py`
