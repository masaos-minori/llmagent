## Goal

- Make every field the generator writes into a manifest come from the source that defines it: the Gate and Type matrix cells, the FastAPI route decorators and their `require_role` dependencies, the files each builder actually reads, the real `scripts/agent/` tree, and no generator-constant fact (`REQ-001`, `REQ-003`, `REQ-004`, `REQ-008`, `REQ-009`, `REQ-010`, `REQ-011`, `REQ-012`; `AC-001`, `AC-002`, `AC-003`, `AC-006`, `AC-007`, `AC-008`, `AC-009`).

## Scope
**Release unit**: manifest-contract-revision, route-role-source, reference-completeness

## Assumptions

- `ASM-01`: the registered EventBus HTTP surface is exactly 9 routes, each gated by `Depends(require_role(Role.X))`.
- `ASM-03`: the `PRAGMA user_version` fallback is dead - no `PRAGMA user_version` statement exists in `scripts/eventbus/schema.sql` or `scripts/db/schema_sql.py`.
- `ASM-05`: `_ROUTE_ROLE_MAP` has no live consumer outside this generator and one synthetic fixture, so deleting its read breaks no runtime path.
- `ASM-06`: memory symbols stay in `memory_api` and are not duplicated into `agent_api` when the scan becomes recursive.
- The regenerated manifests and guarded blocks land in the same commit as these edits (row 18-28, row 15, 16, 30); `--check` cannot pass with only half of the change.

## Design decisions

- `D-01`: unpack the matrix row so each field matches its column - `gate` takes the Gate cell (index 4), a new `check_type` (new) takes the Type cell (index 2); `cited`, `cadence`, `expected_evidence` and `exception` keep parsing the Verification Status cell.
- `D-03`: route roles come from what enforces them - derive `{route, method, roles}` from the route modules, and fail closed with `ManifestError` on an un-gated or unreadable route instead of guessing.
- `D-07`: sources state what is read, and the stamp-less fingerprint model has no version-stamping fallback.
- `D-08`: one classification per manifest - `component_mandatoriness` stays only in `MANIFESTS_BY_DOMAIN`.
- `D-09`, `D-14`: recursive symbol scan with the memory boundary preserved, and the agent index split across two generated documents so each stays under 32768 B.
- Reuse `tools/check_adr_invariant_matrix.py` in-process (existing import of `_matrix_rows`, `_split_row`, `_read_lines`): one parsing implementation for the matrix.

## Alternatives considered

- Keep `_ROUTE_ROLE_MAP` and validate it against the registered routes: rejected by `D-03` - a constant that neither enforces nor feeds anything is the defect the issue names.
- Add matrix-side gate-vocabulary validation to `tools/check_adr_invariant_matrix.py`: out of scope (the sibling matrix-checks issue owns that file, `D-02`).
- Render all 371 `agent_api` entries into `docs/23_agent/agent_13_reference-api-generated.md`: measured 54781 B against `MAX_SIZE = 32768`, rejected by `D-14`.
- Derive `disposition` by parsing ADR-004 prose: rejected by the owner (`D-13`).

## Implementation
### Target file
`tools/generate_reference_table.py`
### Procedure
1. `_invariant_coverage_entries` (lines 727-775): unpack the six cells as invariant, statement, `check_type` (new), timing, `gate`, status; write `gate` from the Gate cell and add `check_type` (new) from the Type cell; leave the Verification Status parsing untouched.
2. `_route_role_entries` (lines 570-597): replace the `_ROUTE_ROLE_MAP` read with a scan of the seven `scripts/eventbus/*_route.py` modules - read each `@router.<method>("<path>")` decorator and that function's `Depends(require_role(Role.X))` argument through the existing `_module_ast` helper, and emit `{route, method, roles}` sorted by route.
3. Raise `ManifestError` when a route function has no `require_role` dependency, when the decorator path is not a string literal, or when a route module cannot be parsed: no entry is emitted for a route whose role cannot be read.
4. `_MANIFEST_SOURCES` (lines 460-476): the `eventbus_route_roles` entry names the seven route modules the new derivation reads.
5. In the same dict: the `db_schema_versions` entry becomes the db config module, `config/agent.toml`, and `scripts/eventbus/schema.sql`, dropping the `schema_sql` module entry no builder reads; the `mcp_endpoints` entry adds the `scripts/mcp_servers` tree its builder scans. The other eight declarations already match their traced read sets and stay as they are (`REQ-009`).
6. `_db_schema_version_entries` (lines 558-568): delete the `_PRAGMA_USER_VERSION_RE` search (line 562) and its regex constant (line 73); the eventbus row records `unversioned` from the stamp-less model.
7. `_health_contract_entries` (lines 673-712): remove the constant `disposition: fail-fast` entry field and the ADR citation comment that justified the constant.
8. `UNBOUND_MANIFESTS` (lines 487-492): remove `component_mandatoriness` so `_run_check` (lines 985-999) drift-checks it once through `MANIFESTS_BY_DOMAIN["mandatoriness"]`.
9. `_symbol_entries` (lines 329-363): scan `source_dir.rglob("*.py")` and keep the leading-underscore skip; add a per-manifest exclusion so `agent_api` skips `scripts/agent/memory/`.
10. Add the second agent document to the generator output set: `REFERENCE_DOC_AGENT_SUBPACKAGES` (new) pointing at `docs/23_agent/agent_14_reference-api-subpackages-generated.md`, its guard pair `GUARD_START_AGENT_SUBPACKAGES` (new), its welcome line, heading, and manifest binding, so `--manifests` writes it and `--check` drift-checks it.
11. Render `agent_api` as two guarded blocks: top-level entries (the 171 entries whose `file` has no subpackage segment) into `agent_13_reference-api-generated.md`, subpackage entries (the remaining 200) into the new document.
12. `DOMAIN_WELCOME_LINES` (lines 436-442): state the scan each block was rendered from - top-level for `agent`, the four subpackages for the new document, and `registry/manifests/memory_api.yaml` for `memory`.

### Method
- Existing helpers only: `_module_ast`, `_assigned_value`, `_split_row`, `_matrix_rows`, `render_symbol_table`. No new third-party dependency, no new subprocess call.
- Fail-closed contract: every derivation raises `ManifestError` (already the module's failure type) rather than emitting a partial entry, so `--manifests`, `--check`, the `manifest-check` pre-commit hook and the CI `lint` job all report the same cause.
- Entry ordering stays byte-stable: sort keys are explicit in each builder, so regeneration is deterministic and `git diff` stays reviewable.
- No compatibility path is written for the old shapes: no `check_type` (new) fallback, no reading of `disposition`, no version-1 branch (`REQ-013`).

### Details
- Current defect measured 2026-11-19: `gate: Unit Test` in every test-gated entry of `registry/manifests/invariant_coverage.yaml`, because the unpack at line 751 assigns the Type cell to `gate` and discards the Gate cell (`_blocking`).
- 34 matrix rows carry Gate values `Blocking` (24), `Deployment Blocking` (6, `docs/10_adr/adr_01_index.md:185-190`) and `Non-Blocking` (4); Type values in use are `Unit Test`, `Startup Validation`, `Manual Review`, `Integration Test`, `Static Check`, `Unit/Integration Test`.
- 9 registered routes measured from the route-module decorators and `EXPECTED_ROUTES` (`tests/eventbus/test_eventbus_route_registry.py:25-35`); the committed manifest holds 10 keys including the four phantoms `/ack`, `/dlq/requeue`, `/events`, `/admin/*` and no `method` field.
- Symbol counts measured 2026-11-19 by running `_symbol_entries` per directory: `scripts/agent` top level 171, `workflow/` 34, `services/` 114, `commands/` 38, `shared/` 14, `memory/` 65 (excluded) - recursive total 371.
- Rendered block sizes measured 2026-11-19: commands 4926 B, shared 1987 B, workflow 5015 B, services 17213 B (29141 B together); `agent_13_reference-api-generated.md` adds 1065 B outside its block, so the new document lands near 30206 B against the 32768 B ceiling.
- Declared-versus-read sets measured 2026-11-19 by instrumenting `pathlib.Path.read_text` while `build_manifest` ran each builder: `mcp_endpoints` declares only `config/agent.toml` yet opens the `scripts/mcp_servers` tree; `db_schema_versions` declares `scripts/db/schema_sql.py`, which no builder opens, and omits `config/agent.toml`, which it does read. The other eight declarations matched their traced read sets.
- This file is baselined at 42762 B in `tools/check_module_size_tools_baseline.txt`; row 29 re-tightens the recorded size after the net change is known.

## Compatibility considerations

- Manifest consumers: `rg` for `registry/manifests` and `load_manifest` matches only this generator and its tests, so no runtime consumer sees the field changes (`D-10`).
- Coordinated with row 02 (envelope version 2) and row 03 (schema enums); the regenerated manifests (rows 18-28) and guarded blocks (rows 15, 16, 30) are part of the same commit.
- `deploy/deploy.sh` does not sync `tools/`: it syncs `scripts/`, `tests/`, `docs/`, `registry/` and `schemas/`; the generator change reaches production only through the regenerated manifests and docs.

## Security considerations

- Route-role entries become derived from the code that enforces them, so a route without a role dependency fails the manifest build instead of being silently absent from the manifest.
- No credential, token or principal value is written into a manifest: entries hold path templates, HTTP methods and role names only.

## Rollback considerations

- Revert the single commit; regeneration is deterministic from live sources, so the manifests and guarded blocks return to their previous bytes with no data migration.

## Validation plan

- `uv run ruff check tools/generate_reference_table.py && uv run mypy --no-namespace-packages tools/generate_reference_table.py` — no findings (lint/type: generator static gates)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — all pass, including T-001 to T-006, T-009 to T-011, T-014, T-015 (unit: generator unit tests)
- `uv run python tools/generate_reference_table.py --check` — No drift found (regeneration gate: manifest/source drift)
- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed manifests equal regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_consumer_authorization.py tests/eventbus/test_admin_topics_authorization.py -v` — all pass with no assertion edits (characterization: authorization behavior unchanged)

## Completion criteria

- `--check` reports no drift with the gate/`check_type` (new) mapping, the derived route entries, the corrected `sources`, the single mandatoriness check, and the recursive scan all in place.
- `rg "_ROUTE_ROLE_MAP\|PRAGMA user_version\|disposition" tools/generate_reference_table.py` returns no match.
- `AC-012`: the diff contains no alias, shim, tolerant fallback, or history-style comment.

## Out of Scope

- Editing `schemas/contract_manifest.json` (row 03) or `tools/_contract_manifests.py` (row 02).
- Deleting `_ROUTE_ROLE_MAP` from `scripts/eventbus/auth.py` (row 04).
- Changing EventBus authorization behavior or any role enforcement.
- Editing `tools/check_adr_invariant_matrix.py` (sibling matrix-checks issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the eight generator edits listed in Procedure | Completed | 20261119-232759 | 20261119-232759 | one commit with rows 02, 03 and the regenerated artifacts eight generator edits applied: route-role derivation reads the seven scripts/eventbus/*_route.py modules, Gate/Type column mapping, health disposition removal, agent_api split render, symbol/source-declaration edits; ruff+mypy clean; 27 targeted tests pass; --manifests rewrote 11 manifests and --check reports No drift found |
| 2 | Add the generator tests through row 10's document | Completed | 20261119-232759 | 20261119-232759 | T-001 to T-006, T-009 to T-011, T-014, T-015 eight generator edits applied: route-role derivation reads the seven scripts/eventbus/*_route.py modules, Gate/Type column mapping, health disposition removal, agent_api split render, symbol/source-declaration edits; ruff+mypy clean; 27 targeted tests pass; --manifests rewrote 11 manifests and --check reports No drift found |
| 3 | Run lint/type, targeted pytest, then the full validation sequence (`rules/toolchain.md`) | Completed | 20261119-232759 | 20261119-232759 | `--manifests` and `--check` pass only after rows 18-28 regenerate eight generator edits applied: route-role derivation reads the seven scripts/eventbus/*_route.py modules, Gate/Type column mapping, health disposition removal, agent_api split render, symbol/source-declaration edits; ruff+mypy clean; 27 targeted tests pass; --manifests rewrote 11 manifests and --check reports No drift found |
| 4 | Confirm the regenerated guarded blocks through rows 15, 16, 30 | Completed | 20261119-232759 | 20261119-232759 | documentation gates eight generator edits applied: route-role derivation reads the seven scripts/eventbus/*_route.py modules, Gate/Type column mapping, health disposition removal, agent_api split render, symbol/source-declaration edits; ruff+mypy clean; 27 targeted tests pass; --manifests rewrote 11 manifests and --check reports No drift found |

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
- **Requirement ID**: `REQ-001` (invariant_coverage.gate carries the Gate-column value of the matrix row), `REQ-003` (the matrix Type-column value is recorded in its own enumerated field (check_type), with a name that matches the column's meaning), `REQ-004` (eventbus_route_roles entries are derived from the registered FastAPI routes and the require_role dependency of each route function), `REQ-008` (health_contracts carries no generator-constant disposition), `REQ-009` (every manifest's sources list names exactly the files and directories its builder reads), `REQ-010` (component_mandatoriness has one bound-or-unbound classification and its drift check runs once per --check), `REQ-011` (db_schema_versions version handling matches the current stamp-less fingerprint model), `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tools/generate_reference_table.py`