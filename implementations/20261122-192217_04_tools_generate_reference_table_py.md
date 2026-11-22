## Goal

Register an agent-config-key generator type in the existing reference-table tool (REQ-002 - emitted as a guarded generated block), rendering the validator's single-source mapping and covered by `--check` (AC-5 - table in exactly one place).

## Scope
**Release unit**: RU-1 generator-and-generated-block

One file is modified: the generator tool. It reads `scripts/agent/production_config_validator.py` (`_REMOVED_KEY_REPLACEMENTS` (new), defined by sibling procedure seq 02); the destination document is handled by sibling procedure seq 06.

## Assumptions
- `DOMAIN_GENERATORS` has no agent-config-key type today (verified); the existing `agent` type is the class/function table and is not reused for this.
- The tool may import the validator mapping via `tests/conftest.py`'s `sys.path` handling, as it already reads `scripts/db/config.py`.
- The tool is under the `check_module_size_tools_baseline.txt` exemption, so adding one generator entry does not trigger a size finding.
- Overlap: none for this file with other Frozen Plans.

## Design decisions
- One generator entry (single source read from the validator) rather than a new standalone tool: existing generator infrastructure already owns config tables and `--check` (design D1).
- Register the new type in `DOMAIN_GENERATORS` so `--check` covers it; `--check` already runs in CI (`ci.yml` line 35).

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
| 1 | Add the generator entry per Procedure/Method/Details | Pending | — | — | RU-1: validate together with seq 06 |
| 2 | Add tests in the companion test file per Validation plan | Pending | — | — | Companion: `tests/tools/test_generate_reference_table.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `--check` | Pending | — | — | |

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
