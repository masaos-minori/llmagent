## Goal

- Give the generator its own regression tests for every new derivation: gate/`check_type` (new) mapping, schema rejection, route derivation, source declarations, single mandatoriness drift-check, stamp-less version handling, removed `disposition`, and the recursive symbol scan with the size-bounded document split (`REQ-001` to `REQ-005`, `REQ-008` to `REQ-012`, `REQ-015`; `AC-001`, `AC-002`, `AC-003`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-013`).

## Scope
**Release unit**: manifest-contract-revision, route-role-source, reference-completeness

## Assumptions

- Existing fixtures mirror synthetic sources (16 tests), so new cases must build their own fixtures rather than read the committed manifests.
- The fixture at line 163 supplies `_ROUTE_ROLE_MAP` source text; row 04 removes that constant, so this fixture is replaced by route-module fixtures.

## Design decisions

- Characterization first: keep the existing suites green and add cases for the new behavior, so a regression in either direction is visible.
- Assert derived facts against their sources (same rule the generator follows): `sources` against builder bodies, route entries against decorator fixtures, gate values against matrix fixtures.

## Alternatives considered

- Assert against the committed manifests only: rejected - the committed artifact is the thing that can go stale, so the tests must exercise the builders.

## Implementation
### Target file
`tests/tools/test_generate_reference_table.py`
### Procedure
1. Add `TestInvariantCoverage` (new): `T-001` `test_gate_reads_gate_column` (new) and `T-002` `test_check_type_reads_type_column` (new), built on a fixture matrix table whose Gate and Type cells hold different values.
2. Add `TestManifestSchema` (new): `T-003` `test_gate_rejects_a_type_column_value` (new) (a Type-column value written into `gate` fails `build_manifest` validation) and `T-004` `test_parameterized_route_path_is_accepted` (new) (`/dlq/{event_id}/requeue` with its `method` validates).
3. Add `TestRouteRoleEntries` (new): `T-005` `test_entries_come_from_decorators_and_role_dependency` (new) over `tmp_path` route-module fixtures holding `@router.<method>("<path>")` decorators and `Depends(require_role(Role.X))` arguments; `T-006` `test_unregistered_route_entry_is_rejected` (new), which also covers `ManifestError` on a route function with no `require_role` dependency and on a decorator path that is not a string literal.
4. Add `TestManifestSources` (new): `T-009` `test_declared_sources_match_builder_reads` (new), asserting for every manifest that each declared path is read (or contains a read file) and every file a builder opens is covered by a declaration; replace the `_ROUTE_ROLE_MAP` source-text fixture at line 163 with route-module fixtures.
5. Add `TestMandatorinessClassification` (new): `T-010` `test_mandatoriness_is_drift_checked_once` (new), counting how many times `component_mandatoriness` is drift-checked in one `--check` run.
6. Add `TestSymbolEntries` (new): `T-011` `test_recursive_scan_covers_agent_subpackages` (new) (the four `scripts/agent/` subpackages are covered, `scripts/agent/memory/` is not) and `T-015` `test_generated_agent_index_stays_within_the_document_ceiling` (new), asserting the rendered subpackage document stays under `tools/check_docs_structure.py` `MAX_SIZE` and that the two agent documents together hold every `agent_api` entry exactly once.
7. Add `TestHealthContracts` (new): `T-014` `test_disposition_is_not_a_generator_constant` (new) - built entries carry no `disposition` key and the module holds no such constant.
8. Keep the existing stamp-less assertion for `db_schema_versions`: the eventbus row records `unversioned` and no `PRAGMA user_version` branch exists (`AC-008`).

### Method
- Fixture-driven unit tests over the builder functions; `tmp_path` source trees for route and symbol scans; schema rejection cases validate a built entry against `schemas/contract_manifest.json`.

### Details
- Test names and their files are fixed by the Plan's Tests section: this file owns `T-001` to `T-006`, `T-009` to `T-011`, `T-014`, `T-015`; `T-007` and `T-008` belong to `tests/eventbus/test_eventbus_route_registry.py` (row 11), `T-012` to row 12, `T-013` to row 13.
- Row 11 owns the production-app parity test; this file stays limited to generator-internal behavior.
- Existing fixture inventory (16 tests) keeps covering the RAG, MCP, deployment, config-ownership and mandatoriness builders unchanged.

## Compatibility considerations

- Test-only file: no production import changes. It reads the generator's helpers through the existing import surface.

## Security considerations

- N/A: synthetic fixtures only; no real token or principal value appears in a test.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_generate_reference_table.py -v` — T-001 to T-006, T-009 to T-011, T-014, T-015 pass (unit: new generator cases)
- `uv run pytest tests/ -n logical` — no failure (regression: whole suite)
- `diff-cover --fail-under=90` — new lines covered (diff coverage: coverage gate)

## Completion criteria

- Every new derivation has a named test, and each AC in the goal maps to at least one passing case.

## Out of Scope

- Production-app route parity (row 11).
- Any change to the code under test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add T-001 to T-006, T-009 to T-011, T-014, T-015 | Pending | — | — | fixture-driven unit tests |
| 2 | Run `uv run pytest tests/tools/test_generate_reference_table.py -v` | Pending | — | — | targeted |
| 3 | Run `uv run pytest tests/ -n logical` (`rules/toolchain.md`) | Pending | — | — | full suite |

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
- **Requirement ID**: `REQ-001` (invariant_coverage.gate carries the Gate-column value of the matrix row), `REQ-002` (the gate vocabulary is enumerated in the manifest schema, so a value outside it fails manifest validation and the CI drift gate), `REQ-003` (the matrix Type-column value is recorded in its own enumerated field (check_type), with a name that matches the column's meaning), `REQ-004` (eventbus_route_roles entries are derived from the registered FastAPI routes and the require_role dependency of each route function), `REQ-005` (the schema route pattern accepts registered parameterized paths such as /dlq/{event_id}/requeue), `REQ-008` (health_contracts carries no generator-constant disposition), `REQ-009` (every manifest's sources list names exactly the files and directories its builder reads), `REQ-010` (component_mandatoriness has one bound-or-unbound classification and its drift check runs once per --check), `REQ-011` (db_schema_versions version handling matches the current stamp-less fingerprint model), `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tests/tools/test_generate_reference_table.py`
