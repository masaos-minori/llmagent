# Implementation Procedure: `tests/shared/test_component_mandatoriness.py`

## Goal

Test-first coverage for the mandatoriness loader: round-trip of the 10 approved entries, typed-error fixtures, and deny-all/unknown/conflict cases (plan Tests New; REQ-003 contract lock; plan Phase 1 "Done when: loader round-trips the 10 approved entries; typed-error fixtures pass").

## Scope

- New test module `tests/shared/test_component_mandatoriness.py` (new), written before the loader (row 2) lands — red until row 2 merges.
- Fixtures live in this file (synthetic YAML strings/tmp files); the live-repo registry file is read as a characterization input.

## Assumptions

- API surface under test is row 2's design: `load_component_mandatoriness` (new), `get_classification` (new), `check_required_agreement` (new), `ComponentClassification` (new), `UnknownComponentError` (new), `ClassificationConflictError` (new) (all (new) symbols created by row 2).
- Registry entry vocabulary is row 1's; if row 1 changes shape these tests change with it (single design source).

## Design decisions

- Live-file test: `load_component_mandatoriness()` with no argument returns exactly 10 entries, all `classification == "required"`, ids equal to the `agent_08_04` server list — this pins plan AC-2's "exactly the 10 approved servers".
- Synthetic malformed inputs via `tmp_path` YAML: missing field, unknown classification value, duplicate `component_id` (new), unparsable YAML → loader raises (each asserted with the error type and the component id in the message, pinning REQ-008-style observability).
- Conflict fixture: registry `required` + `config_required=False` → `ClassificationConflictError` (new); unknown id → `UnknownComponentError` (new).

## Alternatives considered

- Testing through the startup pipeline instead — rejected: Phase 1 must be independently testable (plan Phase 1 statement); pipeline-level fixtures are row 23/24's scope.

## Implementation

### Target file

`tests/shared/test_component_mandatoriness.py` (new)

### Procedure

1. Imports: `pytest`, `tmp_path`, loader symbols from `shared.component_mandatoriness` (`sys.path`/conftest convention as in sibling `tests/shared/` modules).
2. `test_live_registry_round_trips_ten_approved_entries` (new): asserts the 10 ids, all-required, and every REQ-002 field non-empty.
3. `test_unknown_component_raises_typed_error` (new).
4. `test_classification_conflict_raises_typed_error` (new): message names component id, approved classification, config value.
5. `test_malformed_entry_variants_rejected` (new) parametrized over: missing key, empty classification, duplicate id, unknown classification string.
6. `test_frozen_map_rejects_mutation` (new): the returned mapping is not dict-mutable (REQ-003 "frozen classification map").

### Method

Standard pytest with `pytest.raises(..., match=...)`; synthetic registries written to `tmp_path` then loaded by explicit path.

### Details

- Deny-all fixture belongs to the registry consumer side (row 11's constructor tests already pin `frozenset()` deny-all); here "deny-all" means an empty `entries` list loads to an empty map rather than an error — assert that explicitly since row 5's pipeline treats a missing file (not an empty map) as fatal.

## Compatibility considerations

- New file only; red-until-row-2 is expected in the Phase 1 window (test-first ordering, same convention as the other batches this cycle).

## Security considerations

- N/A: tests only.

## Rollback considerations

- Delete the file (single commit revert).

## Validation plan

- `uv run pytest tests/shared/test_component_mandatoriness.py` green after row 2 lands; `uv run ruff check tests`, mypy per `rules/toolchain.md` test conventions.

## Completion criteria

- All six tests pass against row 2's loader; mutation of the returned map raises; the live registry satisfies AC-2's inventory exactly.

## Out of Scope

- Loader implementation (row 2), pipeline fatal fixtures (row 23), checker tests (row 8's registered discovery).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the test module (red) per Procedure | Pending | — | — | Lands before row 2 |
| 2 | Green after row 2 merges | Pending | — | — | |
| 3 | Run `uv run pytest tests/shared` + gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Row 2 (loader) must merge for these tests to pass | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (loader contract: frozen map, typed errors); supports AC-2
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tests/shared/test_component_mandatoriness.py` (new)
