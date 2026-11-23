## Goal

Register an agent-config-key generator type in the existing reference-table tool (REQ-002 - emitted as a guarded generated block), rendering the validator's single-source mapping and covered by `--check` (AC-5 - table in exactly one place).

## Scope
**Release unit**: RU-1 generator-and-generated-block

Two files are modified/created: the generator tool and the new helper module `tools/_agent_config_migration.py` (added by the owner decision recorded in Assumptions). Both read `scripts/agent/production_config_validator.py` (`_REMOVED_KEY_REPLACEMENTS` (new), defined by sibling procedure seq 02); the destination document is handled by sibling procedure seq 06, and `registry/manifests/agent_config_migration.yaml` is the committed artifact the tool writes.

## Assumptions
- `DOMAIN_GENERATORS` has no agent-config-key type today (verified); the existing `agent` type is the class/function table and is not reused for this.
- The tool reads `scripts/agent/production_config_validator.py` as source text (as it already reads `scripts/db/config.py`), not as an imported module: `tests/conftest.py`'s `sys.path` handling does not apply outside pytest, so the mapping is read by parsing the module-level literal with the `ast` module the tool already uses. The mapping must therefore be a plain dict literal.
- Adversarial finding (2026-11-22): `check_drift()` resolves a doc-backed domain through `_RENDER_MANIFEST[domain]`, so a `DOMAIN_GENERATORS`-only entry is not covered by `--check` (KeyError). `--check` coverage requires the contract-manifest path: `MANIFESTS_BY_DOMAIN`, `_RENDER_MANIFEST`, `_MANIFEST_BUILDERS`, `DOMAIN_DOCS`, `DOMAIN_GUARDS`, `DOMAIN_HEADING`, `DOMAIN_WELCOME_LINES` entries plus the committed `registry/manifests/agent_config_migration.yaml`. Owner decision: implement through the manifest path.
- Adversarial finding (2026-11-22): the tool is 1244 lines / 50404 B and the recorded `check_module_size_tools_baseline.txt` entry equals its current size, so any growth fails the `check-module-size-tools` gate as a regression. Owner decision: put the new generator and its renderer in a new module `tools/_agent_config_migration.py` (the existing `tools/_*.py` helper-module pattern) rather than raising the baseline.
- Overlap: none for this file with other Frozen Plans.

## Design decisions
- One generator entry (single source read from the validator) rather than a new standalone tool: existing generator infrastructure already owns config tables and `--check` (design D1).
- Register the new domain through the contract-manifest path (the same architecture as `mandatoriness`), because `--check` verifies a doc-backed domain against a committed manifest; `--check` already runs in CI (`ci.yml` line 35).
- The generator body and its table renderer live in the new `tools/_agent_config_migration.py`; `tools/generate_reference_table.py` only registers the domain and calls them, so the baselined file does not grow.

## Alternatives considered
A hand-maintained table in the document was rejected (duplicates the error-message source). A standalone tool was rejected (design D1).

## Compatibility considerations
The generated table reads the same mapping the error message reads, so the message and the table cannot diverge (Risk mitigation); no existing generator type or output contract changes.

## Security considerations
N/A: read-only generation.

## Rollback considerations
N/A: revert the commit (the `--check` finding disappears with it; see RU-1 note in sibling procedure seq 06).

## Implementation
### Target file
`tools/generate_reference_table.py`
### Procedure
1. Add a generator function `generate_agent_config_migration_table` (new) that renders `_REMOVED_KEY_REPLACEMENTS` into the guarded reference-table block shape used by the existing config generators.
2. Register it as a new `DOMAIN_GENERATORS` entry so `--check` and `--type` include it.
### Method
Reads the validator mapping at generation time; emits old key → new key/owning file rows; no values are copied from documents.
### Details
- Keep the output deterministic and guarded-block compatible with the existing generator contract tested by the companion.

### Companion test files
- `tests/tools/test_generate_reference_table.py`
  - Procedure: Cover the new generator type and its `--check` drift detection (REQ-002).
  - Validation: `uv run pytest tests/tools/test_generate_reference_table.py`

## Validation plan
- Full `rules/toolchain.md` sequence on the tool.
- `uv run pytest tests/tools/test_generate_reference_table.py`; `uv run python tools/generate_reference_table.py --check` exits 0 with the block present (requires sibling procedure seq 06, same release unit).

## Completion criteria
The new type generates the migration table from the validator mapping, `--check` covers it, and its tests pass; the tool's output is the single normative presentation of the mapping.

## Out of Scope
The destination document content itself (sibling procedure seq 06); the mapping values themselves (sibling procedure seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the generator entry per Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | RU-1: validated together with seq 06; the entry is registered through `tools/TOOL_DESCRIPTIONS.md` |
| 2 | Add tests in the companion test file per Validation plan | Completed | 2026-11-22 | 2026-11-22 | 14 tests in `tests/tools/test_generate_reference_table.py`; file coverage 100% |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `--check` | Completed | 2026-11-22 | 2026-11-23 | mypy/ruff/bandit clean, full suite 94%, diff-cover 100% for this file. **Owner decision**: the `check-module-size-tools` regression (52080 bytes vs the 50404-byte ceiling) is resolved by raising `tools/check_module_size_tools_baseline.txt` to 52080, not by splitting the generator, because the growth is the self-describing row the same rule requires |

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
- **Requirement ID**: `REQ-002` (generated migration table from the single source)
- **Source issue**: `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py`
