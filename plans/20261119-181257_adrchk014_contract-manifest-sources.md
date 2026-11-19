## Goal
Make every contract manifest under `registry/manifests/` state only what its declared sources actually support: the `invariant_coverage` gate field carries the ADR matrix Gate-column value, the EventBus route-role manifest is derived from the registered FastAPI routes and their role dependencies, EventBus audit records and docstrings reference registered routes (or explicitly documented non-route identifiers), and each manifest's `sources` list names exactly the files its builder reads.

## Priority
Medium

## Scope
- **In-Scope**: Column-correct `gate`/`check_type` mapping for `invariant_coverage`; enumerated gate vocabulary in the manifest schema; route-role derivation from FastAPI decorators plus their `Depends(require_role(...))` arguments; removal of the unconsumed `_ROUTE_ROLE_MAP`; registered route paths in audit records and docstrings, with the two internal maintenance-loop identifiers documented as non-route; truthful `sources` declarations; single bound/unbound classification for `component_mandatoriness`; removal of the dead `PRAGMA user_version` fallback and the stale version description; recursive API-symbol scan so `agent_api` covers the `scripts/agent/` subpackages; removal of the hardcoded `health_contracts` `disposition`; coordinated envelope version bump; regeneration of all committed manifests and the affected guarded doc blocks; tests for each of the above.
- **Out-of-Scope**: Changing EventBus authorization behavior (role enforcement stays per-route `Depends(require_role(...))`); rebuilding the ADR matrix parsers or adding matrix-side vocabulary validation (the sibling matrix-checks issue owns that); ADR-016 Blocking-gate approval-record auditing; migration, alias, or shim paths for previously written manifest values; hand-editing any generated file; prose rewrites in EventBus contract documents that already use the registered paths.
- **Dependencies**: The two sibling issues that edit `scripts/eventbus/auth.py` and `scripts/eventbus/authz_ttl.py` are already closed, so no re-ordering is required. Sequencing-only note: the sibling issues `adrchk013` and `adrchk015` also regenerate `registry/manifests/invariant_coverage.yaml`; whichever lands first re-runs `tools/check_plan_target_overlaps.py` before editing.
  - **Depends on**: N/A: no blocking ordering dependency

## Background
`tools/generate_reference_table.py` is the sole generator of `registry/manifests/*.yaml` and of the guarded `AUTO-GENERATED` blocks that render from them (ADR-015 Contract Manifest Extension). CI enforces the chain in the `lint` job: `generate_reference_table.py --check`, then `--manifests`, then `git diff --exit-code registry/manifests/`; the same check runs as the `manifest-check` pre-commit hook. A manifest is therefore an authoritative, machine-checked reference: a field that does not correspond to its source, or a source list that does not match what the builder reads, silently propagates wrong facts into the committed artifacts and into CI's pass/fail signal.

## Problem
Verified against current source at head `5a1b99bb7` (baseline `uv run python tools/generate_reference_table.py --check` → "No drift found"):

- `invariant_coverage` stores the wrong column. `tools/generate_reference_table.py:751` unpacks `id_cell, _invariant_text, gate, timing, _blocking, status_cell` against the matrix header `| Invariant | Statement | Type | Timing | Gate | Verification Status |`, so `gate` receives the **Type** cell and the **Gate** cell is discarded. Measured in `registry/manifests/invariant_coverage.yaml` (34 entries): `gate` values are `Unit Test` 20, `Startup Validation` 5, `Manual Review` 3, `Integration Test` 3, `Static Check` 2, `Unit/Integration Test` 1; the Gate column values (`Blocking` 24, `Deployment Blocking` 6, `Non-Blocking` 4) appear nowhere in the manifest. The schema accepts any string: `schemas/contract_manifest.json:230` is `{"type":"string","minLength":1}` with no enum. `tools/check_adr_invariant_matrix.py` does not validate the Gate or Type vocabulary either (it checks cited test paths and Manual/Partial cadence fields).
- The route-role manifest is not derived from anything the runtime enforces. `_ROUTE_ROLE_MAP` (`scripts/eventbus/auth.py:78`) has no runtime consumer; authorization is applied per route through `Depends(require_role(Role.X))` (`scripts/eventbus/auth.py:300` and each route module's decorators). `registry/manifests/eventbus_route_roles.yaml` mirrors the map: 10 entries, role values correct, but four route keys do not exist (`/ack`, `/dlq/requeue`, `/events`, `/admin/*`). The registered set is 9 routes (`tests/eventbus/test_eventbus_route_registry.py:25-35` `EXPECTED_ROUTES`, all gated by `Depends(require_role(...))`).
- Audit records and a docstring name non-existent routes: `scripts/eventbus/dlq_route.py:80` `route="/dlq/requeue"` (registered path is `POST /dlq/{event_id}/requeue`, `dlq_route.py:50`); `scripts/eventbus/ack_route.py` `_do_ack` docstring says the helper is "shared by /ack and /events/{event_id}/ack"; `scripts/eventbus/authz_ttl.py:112` `route="/ttl_sweep"` and `scripts/eventbus/app.py:81` `route="/startup"` name internal maintenance-loop identifiers, not registered routes, and `docs/24_eventbus/eventbus_07_configuration-and-operations.md:97` records `route="/startup"` as an operator-facing contract.
- One manifest field is a generator constant: `health_contracts` `disposition: "fail-fast"` is hardcoded at `tools/generate_reference_table.py:712` with a comment citing ADR-004 Decision #14; no source is read for it, while `schemas/contract_manifest.json:211` describes it as the disposition "cited by the matrix rows".
- Classification and source declarations are inconsistent: `component_mandatoriness` is listed both in `MANIFESTS_BY_DOMAIN` (`tools/generate_reference_table.py:484`) and `UNBOUND_MANIFESTS` (line 491), so `_run_check` (line 989) runs its drift check twice. `_MANIFEST_SOURCES["db_schema_versions"]` (line 464) declares `scripts/db/schema_sql.py`, which no builder reads, and omits `config/agent.toml`, which `_db_path_entries` (line 221) does read. `_PRAGMA_USER_VERSION_RE` (line 73, used at line 562) is a fallback that never matches: neither `scripts/eventbus/schema.sql` nor `scripts/db/schema_sql.py` contains `PRAGMA user_version`. The schema description for that field (`schemas/contract_manifest.json:160-163`) still names `PRAGMA user_version` and `WORKFLOW_SCHEMA_VERSION`, the latter recorded as confirmed removed by `tools/check_compat_shims.py`. The `memory` welcome line (`tools/generate_reference_table.py:441`) names only source globs while the `agent` and `eventbus` lines (439, 440) name their manifest.
- The API reference is incomplete: `_symbol_entries` (lines 329-363) uses non-recursive `source_dir.glob("*.py")`, so `agent_api` holds 171 entries from `scripts/agent/` top level only; `scripts/agent/workflow/` (10 files, 34 symbols), `scripts/agent/services/` (28/114), `scripts/agent/commands/` (25/38) and `scripts/agent/shared/` (5/14) are omitted. `scripts/eventbus/` and `scripts/agent/memory/` have no subpackages, so those two manifests are unaffected.
- Acceptance-criterion 2 of the source issue is unmet today: nothing compares registered FastAPI routes with the manifest. `tests/tools/test_generate_reference_table.py` (16 tests) mirrors synthetic fixtures only (the `_ROUTE_ROLE_MAP` text at line 163 is a fixture); nothing under `tests/eventbus/` references route roles.
- One issue claim is already resolved: the committed `db_schema_versions.yaml` has 4 entries (rag/session/workflow `db_path` plus the eventbus `schema` entry with `version: unversioned`) and no workflow-schema-version rows, so the "phantom workflow schema version rows" claim is stale and that sub-task is skipped.

## Reason for Change
The manifest chain is the repository's only machine-checked record of contract facts, and CI compares regenerated manifests against the committed ones. Two sibling issues will rebuild the matrix parsers and the ADR graph semantics on top of the same `invariant_coverage` fields; leaving a mis-mapped column, an unenforced route list, and a constant-valued field in place makes those changes build on incorrect data.

## Implementation Intent
Keep the generator's existing parse-and-render pipeline, and fix what it reads and what it names: read the correct matrix cell for each field, derive route roles from the declarations that actually gate requests (FastAPI decorators plus their role dependency), declare only the files each builder reads, let the schema's enums reject the values that are not part of the current vocabulary, and regenerate every committed artifact instead of editing it. Enforcement behavior in `scripts/eventbus/` does not change.

## Requirements
- `REQ-001`: `invariant_coverage.gate` carries the Gate-column value of the matrix row; no Type-column value is stored under the name `gate`.
- `REQ-002`: the gate vocabulary is enumerated in the manifest schema, so a value outside it fails manifest validation and the CI drift gate.
- `REQ-003`: the matrix Type-column value is recorded in its own enumerated field (`check_type`), with a name that matches the column's meaning.
- `REQ-004`: `eventbus_route_roles` entries are derived from the registered FastAPI routes and the `require_role` dependency of each route function; no entry may name a route that is not registered.
- `REQ-005`: the schema route pattern accepts registered parameterized paths such as `/dlq/{event_id}/requeue`.
- `REQ-006`: a test asserts that every registered EventBus route (method, path, role) matches the committed manifest, and fails when the two diverge.
- `REQ-007`: audit records, docstrings, and the operator-facing documentation name either a registered route path or an identifier explicitly documented as a non-route internal loop.
- `REQ-008`: `health_contracts` carries no generator-constant `disposition`: the field is removed (ADR-004 Decision #14 remains the authority) or derived from a declared source.
- `REQ-009`: every manifest's `sources` list names exactly the files and directories its builder reads.
- `REQ-010`: `component_mandatoriness` has one bound-or-unbound classification and its drift check runs once per `--check`.
- `REQ-011`: `db_schema_versions` version handling matches the current stamp-less fingerprint model: no `PRAGMA user_version` fallback path, and the schema description names no removed version mechanism.
- `REQ-012`: `agent_api` covers the `scripts/agent/` subpackages (`workflow/`, `services/`, `commands/`, `shared/`) so the generated API reference is complete.
- `REQ-013`: generated artifacts change only by regeneration; no migration, alias, shim, or tolerant fallback is introduced for values written before this change.
- `REQ-014`: the manifest envelope version is bumped once, coordinated with the schema change.

## Implementation Target Files
**Freeze status**: Frozen. All 28 rows are `Verified` (path exists, concrete Repository Evidence measured in Step 2, each row linked to a defined Requirement or Acceptance criterion); no directory, glob, component, or file-group rows; no file appears in both tables. Two rows are conditional and state their condition in `Reason for Modification`.

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/generate_reference_table.py` | Modify | Fix matrix cell mapping (line 751); derive route entries from route-module decorators plus `require_role` (currently reads `_ROUTE_ROLE_MAP` at 572-580); correct `_MANIFEST_SOURCES` (460-476); remove the dead `PRAGMA` fallback (73, 562); drop the constant `disposition` (712); remove `component_mandatoriness` from `UNBOUND_MANIFESTS` (491); recursive symbol scan (329-363); welcome-line wording (439, 441) | REQ-001, REQ-003, REQ-004, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012; AC-001, AC-002, AC-003, AC-006, AC-007, AC-008, AC-009, AC-010 | Confirmed by reading source in Step 2 (line numbers above) | `tests/tools/test_generate_reference_table.py` | Verified |
| `tools/_contract_manifests.py` | Modify | `MANIFEST_VERSION` (line 23) bumped to 2 with the coordinated schema change; envelope validation otherwise unchanged | REQ-014; AC-011 | `MANIFEST_VERSION = 1` at line 23; envelope `version` accepts `minimum: 1` at `schemas/contract_manifest.json:26-31` | `tests/tools/test_generate_reference_table.py` | Verified |
| `schemas/contract_manifest.json` | Modify | Add gate and `check_type` enums (230); allow `{param}` in the route pattern (120); restate the version description to the stamp-less fingerprint model (160-163); remove the `health_contracts` `disposition` property (211) if UNK-03 lands as removal | REQ-002, REQ-003, REQ-005, REQ-008, REQ-011; AC-001, AC-002, AC-005, AC-010 | Current gate property has no enum; current version description names `PRAGMA user_version` and `WORKFLOW_SCHEMA_VERSION` | `tests/tools/test_generate_reference_table.py` | Verified |
| `scripts/eventbus/auth.py` | Modify | Remove `_ROUTE_ROLE_MAP` (line 78): no runtime consumer; enforcement stays `require_role` (line 300) per route | REQ-004; AC-003 | `rg` over `scripts/`, `tests/`, `tools/`, `docs/`: only `auth.py:78`, the generator (572-580), a test fixture in `tests/tools/`, and archived work items reference it | `tests/eventbus/test_eventbus_route_registry.py`, `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/ack_route.py` | Modify | `_do_ack` docstring names `/ack`, a route that is not registered; state the registered path only | REQ-007; AC-005 | Docstring "shared by /ack and /events/{event_id}/ack" at `_do_ack` (line 54 region); registered route is `POST /events/{event_id}/ack` (`ack_route.py:122,137`) | `tests/eventbus/test_eventbus_ack_nack.py` (unchanged behavior) | Verified |
| `scripts/eventbus/dlq_route.py` | Modify | `route="/dlq/requeue"` (line 80) is not a registered path; use `/dlq/{event_id}/requeue` (line 50) | REQ-007; AC-005 | Confirmed by reading source in Step 2 | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/authz_ttl.py` | Modify | `route="/ttl_sweep"` (line 112) is an internal sweep loop, not a route; emit a documented non-route identifier | REQ-007; AC-005 | No `@router` decorator defines `/ttl_sweep` in `scripts/eventbus/` | `tests/eventbus/test_authz_generation_ttl.py:148` | Verified |
| `scripts/eventbus/app.py` | Modify | `route="/startup"` (line 81) is a startup phase, not a route; emit a documented non-route identifier | REQ-007; AC-005 | `app.py:235-241` registers only the seven routers; no `/startup` route exists | `tests/eventbus/` startup audit assertions | Verified |
| `scripts/eventbus/audit.py` | Modify | Document the `route` field vocabulary: a registered route path, or an internal loop identifier that is explicitly not a route (current docstring line 151 says only "Route being accessed") | REQ-007; AC-005 | `log_privileged_action` signature and docstring at lines 138-155 | `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `tests/tools/test_generate_reference_table.py` | Modify | Existing fixtures mirror synthetic sources only (16 tests; line 163 is a `_ROUTE_ROLE_MAP` fixture); add gate/`check_type` mapping, schema-rejection, route-derivation, source-declaration, single-mandatoriness-check, and recursive-scan assertions | REQ-001, REQ-002, REQ-003, REQ-004, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012; AC-001, AC-002, AC-006, AC-007, AC-008, AC-009, AC-010 | Test file inventory and fixture content read in Step 2 | new test methods | Verified |
| `tests/eventbus/test_eventbus_route_registry.py` | Modify | Add the manifest-parity test comparing `app.routes` (method, path, `require_role` role) with `registry/manifests/eventbus_route_roles.yaml`; `EXPECTED_ROUTES` (line 25-35) already locks the registered set | REQ-006; AC-004 | `EXPECTED_ROUTES` matches the 9 registered routes; no manifest comparison exists in the file today | new test methods | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | Modify | Line 1301 asserts the current audit route value; update it to the registered path | REQ-007; AC-005 | `rg` hit at `tests/eventbus/test_eventbus_dlq.py:1301` | updated assertion | Verified |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Line 148 asserts `kwargs["route"] == "/ttl_sweep"`; update it to the documented non-route identifier | REQ-007; AC-005 | `tests/eventbus/test_authz_generation_ttl.py:148` and `:306` | updated assertion | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Line 97 records `route="/startup"` as an operator-facing audit contract; must state the identifier the code emits | REQ-007; AC-005 | Confirmed by reading the doc in Step 2 | none (documentation gate: `tools/check_docs_consistency.py --domain eventbus`) | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Modify | Guarded block re-renders from the expanded `agent_api` manifest, and the welcome line (line 32) currently says `scripts/agent/*.py` top-level only | REQ-012; AC-009 | Welcome line at line 32; generator `DOMAIN_WELCOME_LINES["agent"]` at line 439 | `tests/tools/test_generate_reference_table.py` drift test | Verified |
| `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Modify | Guarded block re-renders after the `memory` welcome line (generator line 441) names its manifest, unifying the source wording with `agent` and `eventbus` | REQ-009; AC-006 | Welcome line at `docs/23_agent/agent_11_04_memory-module-reference-generated.md:37`; generator line 441 | `tests/tools/test_generate_reference_table.py` drift test | Verified |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify (conditional) | Its Contract Manifest Extension section (lines 129-135) states the manifest field and derivation rule; recording the new field set and the route-derivation source is required only if UNK-01, UNK-02 and UNK-03 land as specified. Skipped, and reported as a scope amendment, if the owner rejects them | REQ-003, REQ-008, REQ-014; AC-011 | Section text read in Step 2; `Current Decision Approval (pending)` at line 158 shows an approval record is required for a change here | none (documentation gate: `tools/check_adr_reference.py`, `tools/check_docs_quality.py`) | Verified |
| `registry/manifests/invariant_coverage.yaml` | Regenerate | gate values become Gate-column values; `check_type` added | REQ-001, REQ-003; AC-001, AC-002 | 34 entries, `gate` currently holds Type-column values (measured) | `tools/generate_reference_table.py --check` + `git diff --exit-code registry/manifests/` | Verified |
| `registry/manifests/eventbus_route_roles.yaml` | Regenerate | 9 registered routes with method, path and role; the four phantom keys disappear | REQ-004, REQ-005; AC-003 | Phantom keys `/ack`, `/dlq/requeue`, `/events`, `/admin/*` measured in Step 2 | `tests/eventbus/test_eventbus_route_registry.py` | Verified |
| `registry/manifests/health_contracts.yaml` | Regenerate | Constant `disposition` removed (or derived) per UNK-03 | REQ-008; AC-010 | 10 entries each with `disposition: fail-fast` produced by the constant at generator line 712 | `tests/tools/test_generate_reference_table.py` | Verified |
| `registry/manifests/db_schema_versions.yaml` | Regenerate | `sources` corrected to `scripts/db/config.py`, `config/agent.toml`, `scripts/eventbus/schema.sql` | REQ-009, REQ-011; AC-006, AC-008 | Committed file declares `scripts/db/schema_sql.py` and omits `config/agent.toml` | `tests/tools/test_generate_reference_table.py` | Verified |
| `registry/manifests/agent_api.yaml` | Regenerate | Recursive scan adds the four `scripts/agent/` subpackages (171 to 297 entries) | REQ-012; AC-009 | Symbol counts measured by running `_extract_public_top_level_symbols` over each directory in Step 2 | `tests/tools/test_generate_reference_table.py` | Verified |
| `registry/manifests/component_mandatoriness.yaml` | Regenerate | Envelope version bump only; entries unchanged | REQ-010, REQ-014; AC-007, AC-011 | `version: 1` in the committed file; checked twice today (generator lines 484, 491, 989) | `tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/config_ownership.yaml` | Regenerate | Envelope version bump only; entries unchanged | REQ-014; AC-011 | `version: 1` in the committed file | `tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/mcp_endpoints.yaml` | Regenerate | Envelope version bump only; entries unchanged | REQ-014; AC-011 | `version: 1` in the committed file | `tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/tool_ownership.yaml` | Regenerate | Envelope version bump only; entries unchanged | REQ-014; AC-011 | `version: 1` in the committed file | `tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/eventbus_api.yaml` | Regenerate | Envelope version bump only; `scripts/eventbus/` has no subpackages so entries are unchanged | REQ-012, REQ-014; AC-009, AC-011 | `find scripts/agent -mindepth 1 -maxdepth 1 -type d` shows no `scripts/eventbus` subpackage | `tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/memory_api.yaml` | Regenerate | Envelope version bump only; memory symbols stay out of `agent_api` (ASM-06) | REQ-012, REQ-014; AC-009, AC-011 | 24 files / 65 symbols measured under `scripts/agent/memory/` | `tools/generate_reference_table.py --check` | Verified |
| `tools/check_module_size_tools_baseline.txt` | Modify (conditional) | `tools/generate_reference_table.py` is baselined at 42762 B, and a baselined file that grows past its recorded size fails as a regression; update the recorded size only if the net change grows the file, otherwise tighten it | REQ-013; AC-011 | Baseline entry `generate_reference_table.py 42762`; measured file size 42762 B | `tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_01_index.md` | The invariant matrix is the source of the Gate, Type, Timing and Verification Status cells; 34 rows with the column order `Invariant \| Statement \| Type \| Timing \| Gate \| Verification Status` and no Approval column | `tools/generate_reference_table.py`, REQ-001, REQ-002, REQ-003 |
| `tools/check_adr_invariant_matrix.py` | Its `_matrix_rows` (line 94) and `_split_row` (line 325) cell-splitting and `_MANUAL_STATUSES` (line 329) define how the same rows are parsed elsewhere; the generator must stay consistent with them, and its rebuild belongs to the sibling matrix-checks issue | `tools/generate_reference_table.py`, REQ-001, REQ-003 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Decision #14 and #15 are the authority for a `fail-fast` / `fail-closed` disposition | `schemas/contract_manifest.json`, REQ-008 |
| `scripts/eventbus/health_route.py` | Registered route decorators and their `Depends(require_role(...))` argument (`health_route.py:74`) | `tools/generate_reference_table.py`, REQ-004 |
| `scripts/eventbus/publish_route.py` | Registered route decorator and role dependency (line 43) | `tools/generate_reference_table.py`, REQ-004 |
| `scripts/eventbus/subscribe_route.py` | Registered route decorator and role dependency (line 58) | `tools/generate_reference_table.py`, REQ-004 |
| `scripts/eventbus/replay_route.py` | Registered route decorator (line 30) and its audit route value (line 46) | `tools/generate_reference_table.py`, REQ-004, REQ-007 |
| `scripts/eventbus/admin_route.py` | Registered route decorator (line 72) and its audit route value (line 224) | `tools/generate_reference_table.py`, REQ-004, REQ-007 |
| `scripts/eventbus/schema.sql` | Only source of the `db_schema_versions` schema entry; contains no `PRAGMA user_version` statement | `registry/manifests/db_schema_versions.yaml`, REQ-011 |
| `scripts/db/schema_sql.py` | Declared as a source today although nothing is read from it; must be confirmed unused before removal from `_MANIFEST_SOURCES` | `tools/generate_reference_table.py`, REQ-009 |
| `config/agent.toml` | Read by `_db_path_entries` (line 221) for the `db_path` entries; currently undeclared as a source | `tools/generate_reference_table.py`, REQ-009 |
| `scripts/shared/component_mandatoriness.py` | Field vocabulary mirrored by the mandatoriness manifest | `tools/generate_reference_table.py`, REQ-010 |
| `registry/component_mandatoriness.yaml` | Live source the mandatoriness manifest mirrors | `registry/manifests/component_mandatoriness.yaml`, REQ-010 |
| `tests/eventbus/test_eventbus_auth.py` | `TestProductionRouteWiring` (line 1382) is the characterization baseline proving role enforcement is unchanged | `scripts/eventbus/auth.py`, REQ-004 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | States that every route is registered by its route module's router together with the role dependency that gates it; the derivation must agree with it | `tools/generate_reference_table.py`, REQ-004 |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Authoritative registered path `POST /dlq/{event_id}/requeue` | `scripts/eventbus/dlq_route.py`, REQ-007 |
| `rules/persisted-schema-change.md` | Checklist applied in Design: no persisted SQLite schema is touched | `registry/manifests/db_schema_versions.yaml`, REQ-011 |

## Acceptance Criteria
- `AC-001` (REQ-001, REQ-002): `registry/manifests/invariant_coverage.yaml` gate values are only Gate-column values, and `uv run python -c` validation against `schemas/contract_manifest.json` rejects a Type-column value in `gate`.
- `AC-002` (REQ-003): each `invariant_coverage` entry carries `check_type` with the Type-column value, and the field is enumerated.
- `AC-003` (REQ-004, REQ-005): `registry/manifests/eventbus_route_roles.yaml` contains exactly the 9 registered routes with their method, path (including `{event_id}`) and role; no phantom key remains.
- `AC-004` (REQ-006): a test compares the registered FastAPI routes and their role dependencies with the committed manifest and fails when a route is added, renamed, or un-gated without regenerating the manifest.
- `AC-005` (REQ-007): no audit record, docstring, or EventBus operations doc names a route that is not registered; `rg '`/ack`\|`/dlq/requeue`\|"/ttl_sweep"\|"/startup"'` over `scripts/eventbus/`, `tests/eventbus/` and `docs/24_eventbus/` returns only documented non-route identifiers.
- `AC-006` (REQ-009): each manifest's `sources` equals the files its builder reads, asserted by a test that reads `_MANIFEST_SOURCES` and the builder bodies.
- `AC-007` (REQ-010): `component_mandatoriness` is checked once per `--check` run, asserted by a test that counts its drift-check invocations.
- `AC-008` (REQ-011): no `PRAGMA user_version` fallback remains in the generator, and the `db_schema_versions` version description names only the stamp-less fingerprint model.
- `AC-009` (REQ-012): `registry/manifests/agent_api.yaml` and the agent API reference include the `scripts/agent/workflow/`, `scripts/agent/services/`, `scripts/agent/commands/` and `scripts/agent/shared/` symbols.
- `AC-010` (REQ-008): `health_contracts` no longer carries a constant `disposition`, or every value is produced from a declared source.
- `AC-011` (REQ-013, REQ-014): all 11 committed manifests carry the bumped envelope version and the CI chain passes: `uv run python tools/generate_reference_table.py --check`, `uv run python tools/generate_reference_table.py --manifests`, `git diff --exit-code registry/manifests/`.
- `AC-012` (REQ-013): the diff contains no hand-edited generated file, no alias, shim, or tolerant fallback for previous values, and no history-style comment.

## Tests
- `T-001` `tests/tools/test_generate_reference_table.py::TestInvariantCoverage::test_gate_reads_gate_column` (REQ-001, AC-001)
- `T-002` `tests/tools/test_generate_reference_table.py::TestInvariantCoverage::test_check_type_reads_type_column` (REQ-003, AC-002)
- `T-003` `tests/tools/test_generate_reference_table.py::TestManifestSchema::test_gate_rejects_a_type_column_value` (REQ-002, AC-001)
- `T-004` `tests/tools/test_generate_reference_table.py::TestManifestSchema::test_parameterized_route_path_is_accepted` (REQ-005, AC-003)
- `T-005` `tests/tools/test_generate_reference_table.py::TestRouteRoleEntries::test_entries_come_from_decorators_and_role_dependency` (REQ-004, AC-003)
- `T-006` `tests/tools/test_generate_reference_table.py::TestRouteRoleEntries::test_unregistered_route_entry_is_rejected` (REQ-004, AC-003)
- `T-007` `tests/eventbus/test_eventbus_route_registry.py::TestRouteManifestParity::test_registered_routes_match_manifest_entries` (REQ-006, AC-004)
- `T-008` `tests/eventbus/test_eventbus_route_registry.py::TestRouteManifestParity::test_manifest_role_matches_require_role_dependency` (REQ-004, REQ-006, AC-004)
- `T-009` `tests/tools/test_generate_reference_table.py::TestManifestSources::test_declared_sources_match_builder_reads` (REQ-009, REQ-011, AC-006, AC-008)
- `T-010` `tests/tools/test_generate_reference_table.py::TestMandatorinessClassification::test_mandatoriness_is_drift_checked_once` (REQ-010, AC-007)
- `T-011` `tests/tools/test_generate_reference_table.py::TestSymbolEntries::test_recursive_scan_covers_agent_subpackages` (REQ-012, AC-009)
- `T-012` `tests/eventbus/test_eventbus_dlq.py::test_requeue_audit_record_uses_registered_route` (REQ-007, AC-005)
- `T-013` `tests/eventbus/test_authz_generation_ttl.py::test_sweep_audit_record_uses_internal_identifier` (REQ-007, AC-005)
- `T-014` `tests/tools/test_generate_reference_table.py::TestHealthContracts::test_disposition_is_not_a_generator_constant` (REQ-008, AC-010)
- Regression coverage, unchanged and required to stay green: `tests/eventbus/test_eventbus_auth.py::TestProductionRouteWiring`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_admin_topics_authorization.py` (REQ-004).
- Commands: `uv run pytest tests/tools/test_generate_reference_table.py tests/eventbus/test_eventbus_route_registry.py tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v`, then `uv run pytest tests/ -n logical`.

## Documentation Impact
Yes. The regenerated API reference and the EventBus operations reference are updated by the generated-artifact chain, and the ADR-015 disposition document records the manifest extension only if the owner approves the field-set change (UNK-01, UNK-02, UNK-03). The driven requirements are REQ-007 (EventBus operations doc), REQ-009 and REQ-012 (generated symbol references), REQ-003, REQ-008 and REQ-014 (ADR-015 Contract Manifest Extension section). Target documents are the ones already listed as rows in `Implementation Target Files`, which are the `docs/` files named by `docs/00_index.md`'s task-scope mapping for the agent and eventbus domains; no additional `docs/` file is in scope.

Generator commands (never hand-edit the guarded blocks or the manifests):

```bash
uv run python tools/generate_reference_table.py --manifests
```

Post-generation verification:

```bash
uv run python tools/generate_reference_table.py --check
uv run python tools/check_docs_consistency.py --domain agent
uv run python tools/check_docs_consistency.py --domain eventbus
uv run python tools/check_docs_quality.py
uv run python tools/check_compat_shims.py
```

Generator boundary note: `docs/90_deployment/deployment_01_deployment.md` and `docs/24_eventbus/eventbus_08_reference_api.md` are re-checked but expected byte-identical (their source declarations already match the corrected sources), so they are not target rows.

## Assumptions
- `ASM-01`: The registered EventBus HTTP surface is exactly 9 routes and every one of them is gated by `Depends(require_role(Role.X))` (measured from the route-module decorators and `EXPECTED_ROUTES`).
- `ASM-02`: The audit `route` field has no code consumer — `rg` over `scripts/` and `tools/` found only the emitting call sites — so its vocabulary is an operator-facing log contract, not a runtime contract.
- `ASM-03`: The `PRAGMA user_version` fallback is dead: neither `scripts/eventbus/schema.sql` nor `scripts/db/schema_sql.py` contains a `PRAGMA user_version` statement (measured).
- `ASM-04`: `MANIFEST_VERSION` may be bumped to 2 without a schema edit of the envelope `version` property, which only constrains `minimum: 1`.
- `ASM-05`: `_ROUTE_ROLE_MAP` has no live consumer outside the generator, one synthetic fixture in `tests/tools/test_generate_reference_table.py`, and archived work items (measured by `rg` across `scripts/`, `tests/`, `tools/`, `docs/`).
- `ASM-06`: Memory symbols stay in `memory_api` and are not duplicated into `agent_api` when the scan becomes recursive (see UNK-05).
- `ASM-07`: `docs/` prose for the EventBus HTTP contract already uses the registered paths, so aligning code to them does not require contract-document rewrites beyond the one line in `eventbus_07_configuration-and-operations.md`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Gate enum membership. The issue asks the schema to reject anything but `Blocking` or `Non-Blocking`, but 6 of the 34 matrix rows record `Deployment Blocking` (`docs/10_adr/adr_01_index.md:185-190`), and the matrix section defines only the `Not verified` implies `Non-Blocking` rule, with no enumerated Gate vocabulary. A two-value enum makes `--manifests` fail on current data. | Owner decision on whether `Deployment Blocking` is a gate value or a qualification of `Blocking`. | Owner decision before Phase 1. Plan default: enum `{Blocking, Deployment Blocking, Non-Blocking}` (all values in use, no value changed, no approval fabricated). | True |
| UNK-02 | Adding `check_type`, removing `health_contracts.disposition`, and bumping the envelope version change the manifest contract that ADR-015 defines. The constraint forbids writing or simulating a maintainer approval, and `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md:158` shows an approval record there is still pending. | An approval record for the manifest field-set change. | Owner approval before Phase 1; without it the plan lands only the column-mapping fix and reports the rest as a scope amendment. | True |
| UNK-03 | `health_contracts.disposition`: remove the field, or derive it by parsing ADR-004 Decision #14 text. A per-server value is not mechanically derivable from `posture_contract.REQUIRED_CHECK_IDS`. | Owner decision on whether the manifest should carry a field whose value comes from an ADR decision rather than live code. | Owner decision before Phase 1. Plan default: remove the field; ADR-004 remains the authority. | True |
| UNK-04 | The two non-route audit identifiers. Rename `/ttl_sweep` and `/startup` to non-path identifiers, or keep the strings and document them as internal. | Owner decision on the operator-facing audit vocabulary. | Plan default: emit `ttl_sweep` and `startup` (no leading slash) and document the vocabulary in `scripts/eventbus/audit.py` and the EventBus operations doc. Owner veto changes only the two call sites, the two test assertions, and one doc line. | False |
| UNK-05 | Whether the recursive `agent_api` scan should include `scripts/agent/memory/`, which already has its own manifest and reference doc. | Owner decision on duplicate listing across manifests. | Plan default: exclude `scripts/agent/memory/` from `agent_api` so the existing document boundary is preserved. | False |
| UNK-06 | Which way "unify the memory description" goes: name the manifest in the memory welcome line (as `agent` and `eventbus` do), or drop manifest naming from those two. | Owner intent; the generator welcome line is part of the guarded block, so either direction rewrites a generated doc. | Plan default: name `registry/manifests/memory_api.yaml` in the memory welcome line. | False |
| UNK-07 | Whether this plan must machine-check that Blocking and Deployment Blocking gates carry an approval record. The matrix table has 6 cells per row and no Approval column (`docs/10_adr/adr_01_index.md:177-210`), and no approval-record field for a gate value exists anywhere in `docs/10_adr/`; the approval-record convention lives in ADR decision sections such as `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:333-334`. | Where an approval record would be written for a gate value. | Out of scope here; resolved by the sibling matrix-checks issue. This plan enforces vocabulary only. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/generate_reference_table.py` | Modify | Sole producer of all 11 manifests and 5 guarded doc blocks; a mapping error propagates to every generated artifact and to the CI diff gate | 7 | 2 authors | No (tools/ is not synced; the generator runs from the repository) |
| `tools/_contract_manifests.py` | Modify | Envelope shape of all 11 manifests | 1 | 1 author | Yes (`schemas/` and `registry/` are copied to `/opt/llm/`) |
| `schemas/contract_manifest.json` | Modify | Validation of all 11 manifests | 2 | 2 authors | Yes (`deploy/deploy.sh:174-176` copies `schemas/` to `/opt/llm/schemas/`) |
| `scripts/eventbus/auth.py` | Modify | Authorization module; enforcement unchanged but the module is security-critical | 11 | 2 authors | Yes (`scripts/` is rsynced; the EventBus service restarts) |
| `scripts/eventbus/ack_route.py` | Modify | Docstring only | 12 | 2 authors | Yes (`scripts/` rsync) |
| `scripts/eventbus/dlq_route.py` | Modify | Audit log field value for requeue events | 5 | 2 authors | Yes |
| `scripts/eventbus/authz_ttl.py` | Modify | Audit log field value for the TTL sweep loop | 4 | 2 authors | Yes |
| `scripts/eventbus/app.py` | Modify | Audit log field value for the startup baseline record | 19 | 3 authors | Yes |
| `scripts/eventbus/audit.py` | Modify | Audit record contract documentation for all privileged-action records | 3 | 2 authors | Yes |
| `tests/tools/test_generate_reference_table.py` | Modify | Generator regression suite | 4 | 2 authors | Yes (`tests/` rsync) |
| `tests/eventbus/test_eventbus_route_registry.py` | Modify | Route and authorization regression suite | 1 | 1 author | Yes |
| `tests/eventbus/test_eventbus_dlq.py` | Modify | DLQ audit assertion | 17 | 2 authors | Yes |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | TTL sweep audit assertion | 7 | 2 authors | Yes |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Operator-facing audit vocabulary | 12 | 2 authors | Yes (`docs/` rsync) |
| `docs/23_agent/agent_13_reference-api-generated.md` | Regenerate | Generated API reference grows from 171 to 297 symbol rows | 23 | 2 authors | Yes |
| `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Regenerate | Generated memory reference welcome line | 1 | 2 authors | Yes |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify (conditional) | ADR body that defines the manifest contract | 4 | 1 author | Yes |
| `registry/manifests/invariant_coverage.yaml` | Regenerate | Verification-coverage mirror for 34 invariants | 7 | 2 authors | Yes (`deploy/deploy.sh:80-82` rsyncs `registry/`) |
| `registry/manifests/eventbus_route_roles.yaml` | Regenerate | Route-role reference | 1 | 1 author | Yes |
| `registry/manifests/health_contracts.yaml` | Regenerate | Health-contract reference | 1 | 1 author | Yes |
| `registry/manifests/db_schema_versions.yaml` | Regenerate | DB path and schema reference; feeds the deployment guarded block | 13 | 2 authors | Yes |
| `registry/manifests/agent_api.yaml` | Regenerate | Agent symbol reference (171 to 297 entries) | 16 | 2 authors | Yes |
| `registry/manifests/component_mandatoriness.yaml` | Regenerate | Mandatoriness mirror | 1 | 1 author | Yes |
| `registry/manifests/config_ownership.yaml` | Regenerate | Config-ownership reference | 3 | 1 author | Yes |
| `registry/manifests/mcp_endpoints.yaml` | Regenerate | MCP endpoint reference | 1 | 1 author | Yes |
| `registry/manifests/tool_ownership.yaml` | Regenerate | Tool-ownership reference | 1 | 1 author | Yes |
| `registry/manifests/eventbus_api.yaml` | Regenerate | EventBus symbol reference | 13 | 2 authors | Yes |
| `registry/manifests/memory_api.yaml` | Regenerate | Memory symbol reference | 2 | 1 author | Yes |
| `tools/check_module_size_tools_baseline.txt` | Modify (conditional) | tools/ size gate baseline ceiling | 29 | 2 authors | No |

## Design
Grounded in the Path B analysis: `uv run lint-imports` → 6 contracts kept, 0 broken (518 files, 3101 dependencies); `tools/` is not contract-covered, so the generator change introduces no import-cycle risk; `scripts/eventbus/` stays isolated from the other layers because nothing here adds an import.

- `D-01` (REQ-001, REQ-003) — Column-faithful field names. Unpack the matrix row so each manifest field matches its column: `gate` takes the Gate cell (index 4) and a new `check_type` takes the Type cell (index 2). The existing trigger/cadence derivation keeps reading the Type cell internally, so no `trigger` or `cadence` value changes; only field names and the discarded Gate value are corrected. `tools/check_adr_invariant_matrix.py` is not edited: the generator keeps its own parse and the two stay consistent through a shared test on the same matrix file.
- `D-02` (REQ-002) — Enforcement point is the manifest schema. `schemas/contract_manifest.json` gains the gate enum, so the failure surfaces in `build_manifest` validation, `--check`, the `manifest-check` pre-commit hook, and the CI `lint` job. Adding matrix-side vocabulary validation to `tools/check_adr_invariant_matrix.py` is deliberately left to the sibling matrix-checks issue to keep the reused parsers in one owner's hands.
- `D-03` (REQ-004, REQ-006) — Route roles come from what enforces them. `tools/generate_reference_table.py` parses each `scripts/eventbus/*_route.py` module with the existing `_module_ast`/`_assigned_value` helpers: it reads `@router.<method>("<path>")` decorators and the route function's `Depends(require_role(Role.X))` argument, and emits `{route, method, role}`. It fails closed with `ManifestError` when a route function has no role dependency or a decorator form it cannot read, instead of guessing. Enforcement behavior is untouched, so `TestProductionRouteWiring` and the consumer-authorization suites are the characterization gate. `_ROUTE_ROLE_MAP` is deleted (ASM-05): keeping a constant that neither enforces nor feeds anything is the defect the issue names.
- `D-04` (REQ-005) — Route identity is the registered path template, matching `EXPECTED_ROUTES` and the EventBus contract docs, so `/dlq/{event_id}/requeue` is a valid manifest key once the schema pattern accepts `{param}` segments.
- `D-05` (REQ-007) — Two audit vocabularies, stated once. A registered HTTP route emits its registered path; an internal maintenance loop or startup phase emits a non-path identifier, documented in `scripts/eventbus/audit.py` and in the EventBus operations doc. `/ttl_sweep` and `/startup` are not HTTP routes and are never written into a route manifest.
- `D-06` (REQ-008) — A constant is not a derived fact. `health_contracts` loses the `disposition` field (schema property and entries), leaving ADR-004 Decisions #14 and #15 as the single authority. Deriving it by parsing ADR prose is the recorded alternative and is only taken if UNK-03 resolves that way.
- `D-07` (REQ-009, REQ-011) — Sources state what is read. `db_schema_versions` declares `scripts/db/config.py`, `config/agent.toml` and `scripts/eventbus/schema.sql`; the unread `scripts/db/schema_sql.py` entry is removed. The `_PRAGMA_USER_VERSION_RE` branch is deleted (ASM-03) and the version description restates the stamp-less content-hash fingerprint model, with no reference to `WORKFLOW_SCHEMA_VERSION`, which `tools/check_compat_shims.py` records as confirmed removed. No alias or fallback is left behind.
- `D-08` (REQ-010) — One classification per manifest. `component_mandatoriness` is removed from `UNBOUND_MANIFESTS`; it stays in `MANIFESTS_BY_DOMAIN["mandatoriness"]`, so `_run_check` drift-checks it once.
- `D-09` (REQ-012) — Completeness with a preserved boundary. `_symbol_entries` scans `rglob("*.py")`, and `agent_api` excludes `scripts/agent/memory/` so the existing `memory_api` manifest and memory reference doc keep their own scope (UNK-05). The `agent` and `memory` welcome lines are updated inside the generator so the guarded blocks describe the scan they were rendered from.
- `D-10` (REQ-013, REQ-014) — One coordinated contract revision. `MANIFEST_VERSION` goes 1 to 2 and all 11 manifests are regenerated in the same commit as the generator and schema edits, because `--check` and CI's `git diff --exit-code registry/manifests/` cannot pass with a stale manifest. Nothing reads the old shape: no runtime consumer loads these manifests (measured by `rg` for `registry/manifests` and `load_manifest`, which matched only the generator and tests), so no migration or alias path is written (REQ-013).
- Persistence checklist outcome (`rules/persisted-schema-change.md`): does not apply. `registry/manifests/*.yaml` are committed generated artifacts under git, not persisted SQLite schema; no DDL, schema version, or migration step is touched, and `/opt/llm/db/eventbus.sqlite` is not opened by any step of this Plan.

### Verification Design

Commands:

```bash
uv run ruff check scripts/ tools/ tests/
uv run ruff format --check .
uv run mypy --no-namespace-packages scripts/ tests/eventbus tools
uv run bandit -q -r scripts/ -c pyproject.toml -ll
uv run lint-imports
uv run pytest tests/tools/test_generate_reference_table.py tests/eventbus/test_eventbus_route_registry.py tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v
uv run pytest tests/ -n logical
uv run python tools/generate_reference_table.py --manifests
git diff --exit-code registry/manifests/
uv run python tools/generate_reference_table.py --check
uv run python tools/check_adr_reference.py
uv run python tools/check_docs_consistency.py --domain agent
uv run python tools/check_docs_consistency.py --domain eventbus
uv run python tools/check_docs_quality.py
uv run python tools/check_module_size.py
uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt
uv run python tools/check_compat_shims.py
uv run python tools/check_workitem_structure.py
uv run python tools/audit_plan_target_paths.py
uv run python tools/check_plan_target_overlaps.py
```

Validation gates:

| Gate | Command | Pass condition |
|---|---|---|
| Manifest freshness | `--manifests` then `git diff --exit-code registry/manifests/` | Committed manifests equal regenerated output |
| Manifest/source drift | `generate_reference_table.py --check` | "No drift found" |
| Schema rejection | `T-003`, `T-004` | Wrong-column and malformed-key values are rejected |
| Route parity | `T-007`, `T-008` | Registered routes and manifest entries are identical sets |
| Enforcement unchanged | `tests/eventbus/test_eventbus_auth.py::TestProductionRouteWiring`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_admin_topics_authorization.py` | All pass with no assertion edits |
| Documentation freshness | `check_docs_consistency.py --domain agent`, `--domain eventbus`, `check_docs_quality.py`, `check_adr_reference.py` | No drift, no stale reference |
| Module size ceiling | `check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | `tools/generate_reference_table.py` stays at or below its recorded baseline |
| No leftover contract text | `check_compat_shims.py` (pre-commit) | No stale symbol or compat leftover |

CI stage mapping: the `lint` job runs `ruff check scripts/`, `mypy --no-namespace-packages scripts/ tests/eventbus tools`, `bandit -r scripts/ -c pyproject.toml -ll`, `lint-imports`, `generate_reference_table.py --check`, `generate_reference_table.py --manifests` followed by `git diff --exit-code registry/manifests/`, and the module-size checks; the pre-commit hooks add `manifest-check`, `check-compat-shims`, `adr-invariant-matrix`, `docs-consistency`, `plan-target-overlaps` and `workitem-traceability`; the test job runs the full pytest suite and `diff-cover --fail-under=90` against `master`. Deployment: `deploy/deploy.sh` syncs `scripts/`, `tests/`, `docs/`, `registry/` and `schemas/`, so the deploy step is required after this change; no new deploy step is added.

## Implementation steps
Each step description cites the frozen `Implementation Target Files` rows it touches.

1. **Phase 1: Manifest contract revision (schema and envelope)**
   - [ ] Add the gate and `check_type` enums, the parameterized route pattern, the stamp-less version description, and the `health_contracts` disposition removal (REQ-002, REQ-003, REQ-005, REQ-008, REQ-011; `schemas/contract_manifest.json`).
   - [ ] Bump the envelope version constant once (REQ-014; `tools/_contract_manifests.py`).
   - [ ] Gate: UNK-01, UNK-02 and UNK-03 resolved by the owner before any edit; otherwise stop and report a scope amendment.
2. **Phase 2: Matrix column mapping and invariant coverage**
   - [ ] Read the Gate cell into `gate` and the Type cell into `check_type`, keeping the internal Type usage for trigger and cadence derivation unchanged (REQ-001, REQ-003; `tools/generate_reference_table.py`).
   - [ ] Add `T-001`, `T-002`, `T-003`; regenerate `registry/manifests/invariant_coverage.yaml`.
   - [ ] Acceptance command: `uv run pytest tests/tools/test_generate_reference_table.py -v` then `uv run python tools/generate_reference_table.py --check`.
3. **Phase 3: Route-role derivation from the enforcing declarations**
   - [ ] Replace the `_ROUTE_ROLE_MAP` read with AST derivation from `@router.<method>` decorators plus `Depends(require_role(Role.X))`, failing closed on an un-gated or unreadable route (REQ-004; `tools/generate_reference_table.py`).
   - [ ] Delete the unconsumed map (REQ-004; `scripts/eventbus/auth.py`).
   - [ ] Add `T-005`, `T-006`, `T-007`, `T-008`; regenerate `registry/manifests/eventbus_route_roles.yaml` (REQ-006; `tests/tools/test_generate_reference_table.py`, `tests/eventbus/test_eventbus_route_registry.py`).
   - [ ] Acceptance command: `uv run pytest tests/eventbus/test_eventbus_route_registry.py tests/eventbus/test_eventbus_auth.py -v`.
4. **Phase 4: Audit route vocabulary**
   - [ ] Use the registered path in the requeue audit record (REQ-007; `scripts/eventbus/dlq_route.py`).
   - [ ] Emit the documented non-route identifiers for the sweep loop and the startup baseline (REQ-007; `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/app.py`).
   - [ ] State the two vocabularies in the audit record docstring and correct the `_do_ack` docstring (REQ-007; `scripts/eventbus/audit.py`, `scripts/eventbus/ack_route.py`).
   - [ ] Update the two audit assertions and the operator-facing line (REQ-007; `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_authz_generation_ttl.py`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`).
   - [ ] Acceptance command: `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v` then `uv run python tools/check_docs_consistency.py --domain eventbus`.
5. **Phase 5: Source truthfulness, classification, and completeness**
   - [ ] Correct `_MANIFEST_SOURCES` for `db_schema_versions` and `health_contracts`, and assert the source declaration against the builders (REQ-009; `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py`).
   - [ ] Remove the dead `PRAGMA user_version` fallback (REQ-011; `tools/generate_reference_table.py`).
   - [ ] Remove `component_mandatoriness` from the unbound list and assert one drift-check (REQ-010; `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py`).
   - [ ] Switch the symbol scan to `rglob`, exclude `scripts/agent/memory/` from `agent_api`, and update the `agent` and `memory` welcome lines (REQ-012, REQ-009; `tools/generate_reference_table.py`).
   - [ ] Acceptance command: `uv run pytest tests/tools/test_generate_reference_table.py -v`.
6. **Phase 6: Regeneration, documentation, and deployment verification**
   - [ ] Run `uv run python tools/generate_reference_table.py --manifests` once and commit all 11 regenerated manifests together with the generator and schema edits (REQ-013, REQ-014; every `registry/manifests/*.yaml` row).
   - [ ] Commit the regenerated guarded blocks (REQ-009, REQ-012; `docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_11_04_memory-module-reference-generated.md`).
   - [ ] Record the manifest extension only if the owner approved the field-set change (REQ-003, REQ-008, REQ-014; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`).
   - [ ] Re-tighten the tools module-size baseline only if the net change grew the generator (REQ-013; `tools/check_module_size_tools_baseline.txt`).
   - [ ] Deployment validation: `deploy/deploy.sh` syncs `scripts/`, `tests/`, `docs/`, `registry/` and `schemas/`; confirm `/opt/llm/DEPLOYED_REV` records the new revision and restart the EventBus service so the audit vocabulary change is live (`skills/deploy/SKILL.md` pre-deploy gate).
   - [ ] Acceptance command: the full `Validation plan` sequence.

### Release units
**Unit**: manifest-contract-revision | **Phases**: 1, 2, 6 | **Reason**: the enum and field-set change makes the committed manifests stale the moment the schema lands; `--check` and CI's `git diff --exit-code registry/manifests/` only pass once `invariant_coverage`, `health_contracts` and `db_schema_versions` are regenerated in the same commit.
**Unit**: route-role-source | **Phases**: 1, 3, 6 | **Reason**: deleting `_ROUTE_ROLE_MAP` and switching the derivation leaves `eventbus_route_roles.yaml` stale and the parity test red until regeneration lands.
**Unit**: audit-route-vocabulary | **Phases**: 4, 6 | **Reason**: the new `route` values break `tests/eventbus/test_eventbus_dlq.py:1301` and `tests/eventbus/test_authz_generation_ttl.py:148` until the assertions and the EventBus operations doc are updated together.
**Unit**: reference-completeness | **Phases**: 5, 6 | **Reason**: the recursive scan changes `agent_api.yaml` and the generated agent reference block in the same commit; `--check` fails with either half missing.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/generate_reference_table.py` | Unit (fixtures plus live-source assertions) | `uv run pytest tests/tools/test_generate_reference_table.py -v` | `T-001` to `T-006`, `T-009`, `T-010`, `T-011`, `T-014` pass |
| `tools/_contract_manifests.py` | Unit | `uv run pytest tests/tools/test_generate_reference_table.py -v` | Envelope version 2 validates against the schema |
| `schemas/contract_manifest.json` | Unit (jsonschema rejection cases) | `uv run pytest tests/tools/test_generate_reference_table.py -v` | Type-column value in `gate`, and a route key with an unsupported shape, are rejected |
| `scripts/eventbus/auth.py` | Integration through the production app (characterization) | `uv run pytest tests/eventbus/test_eventbus_route_registry.py tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_consumer_authorization.py tests/eventbus/test_admin_topics_authorization.py -v` | All 401/403 wiring tests pass unchanged after the map removal |
| `scripts/eventbus/dlq_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/app.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/ack_route.py` | Integration through the EventBus test client | `uv run pytest tests/eventbus/ -v` | `T-012`, `T-013` pass; no audit record names an unregistered route |
| `registry/manifests/*.yaml` (11 rows) | Generated-artifact freshness | `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` then `uv run python tools/generate_reference_table.py --check` | Clean diff and "No drift found" |
| `docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Generated-block drift | `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docs_consistency.py --domain agent` | Blocks match the regenerated manifests; the agent table lists the subpackage symbols |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Documentation checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_adr_reference.py` | No doc-claim or ADR-reference drift |
| `tools/check_module_size_tools_baseline.txt` | Size gate | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Generator stays at or below its recorded baseline, or the baseline is re-tightened with a stated reason |
| Whole change | Full suite and static analysis | `uv run pytest tests/ -n logical`; `uv run ruff check scripts/ tools/ tests/`; `uv run ruff format --check .`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit -q -r scripts/ -c pyproject.toml -ll`; `uv run lint-imports` | All pass; baseline measured today: bandit exit 0 with 0 reportable issues, `lint-imports` 6 contracts kept / 0 broken, `--check` "No drift found" |
| Scope hygiene | Work-item gates | `uv run python tools/check_workitem_structure.py`; `uv run python tools/audit_plan_target_paths.py`; `uv run python tools/check_plan_target_overlaps.py` | No target-path drift and no overlap with another active Plan |
| Deployment | Deploy and post-deploy freshness | `bash deploy/deploy.sh` then `uv run python tools/generate_reference_table.py --check` against the deployed tree | `registry/`, `schemas/`, `docs/` and `scripts/` under `/opt/llm/` match the repository |

## Risks
- **Risk**: The gate enum choice can make the current data invalid (6 rows carry `Deployment Blocking`), turning a correctness fix into a CI failure. → **Mitigation**: UNK-01 is resolved before Phase 1; the plan default enumerates all three values in use, so no gate value changes and no approval is needed for a value change.
- **Risk**: Removing `_ROUTE_ROLE_MAP` from a security-critical, high-churn module. → **Mitigation**: enforcement stays per-route; `TestProductionRouteWiring`, the consumer-authorization suite and the admin-authorization suite must pass with no assertion edits before the map removal is committed.
- **Risk**: The schema/field change and the manifest regeneration cannot be split across commits (CI compares regenerated manifests against committed ones). → **Mitigation**: the four declared release units land as single commits; each phase's acceptance command runs the freshness pair.
- **Risk**: `agent_api` growth (171 to 297 entries) rewrites a large generated doc and may trip documentation quality or size checks. → **Mitigation**: regenerate first, then run `check_docs_quality.py` and `check_docs_consistency.py --domain agent`; if a doc gate fails, stop and report rather than trimming the manifest by hand.
- **Risk**: `tools/generate_reference_table.py` sits exactly at its baselined size (42762 B), so any net growth fails the tools size gate. → **Mitigation**: the change removes code (map read, `PRAGMA` fallback, constant disposition) as it adds the route parser; run `check_module_size.py --scripts-dir tools` after each phase and only touch `tools/check_module_size_tools_baseline.txt` with a stated reason.
- **Risk**: The route AST derivation could silently accept an unreadable decorator form and emit a wrong manifest. → **Mitigation**: `D-03`'s fail-closed rule plus `T-005` and `T-006`, which assert that an unregistered or un-gated route raises rather than being guessed.
- **Risk**: Audit `route` value changes alter operator-facing log fields and any runbook text. → **Mitigation**: `ASM-02` measured no code consumer; the vocabulary is documented in `scripts/eventbus/audit.py` and in the EventBus operations doc in the same commit (Phase 4).
- **Risk**: Target-file overlap with the sibling matrix-checks and ADR-graph issues on `registry/manifests/invariant_coverage.yaml` and `tools/generate_reference_table.py`. → **Mitigation**: `tools/check_plan_target_overlaps.py` is re-run immediately before editing, and the issue-level instruction to re-search the acceptance criteria before editing is repeated at Phase 2; if a defect is already fixed by the sibling work, its evidence is recorded and the sub-task is skipped.
- **Quality assessment**: measured baselines — `generate_reference_table.py --check` clean; `lint-imports` 6 kept / 0 broken; `bandit -r scripts/ -ll` exit 0; `vulture` reports no dead code in the target files; radon flags `_config_ownership_entries` (17), `_health_contract_entries` (14) and `_invariant_coverage_entries` (12) as C-grade functions, so the Phase 2 and Phase 5 edits must not deepen their branching.
- **Uncertainty assessment**: three Blocking unknowns (UNK-01, UNK-02, UNK-03) gate Phase 1; every other design choice has a stated plan default and a bounded blast radius.
- **Observability**: after Phase 4, the emitted audit identifiers are `ttl_sweep` and `startup` for internal phases and registered path templates for HTTP routes; `tests/eventbus/` asserts both forms, and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` states the vocabulary an operator will see in the logs.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: manifest contract revision | Blocked | — | — | Waiting on UNK-01, UNK-02, UNK-03 owner decisions |
| 2 | Phase 2: matrix column mapping and invariant coverage | Pending | — | — | Depends on Phase 1 |
| 3 | Phase 3: route-role derivation and `_ROUTE_ROLE_MAP` removal | Pending | — | — | Characterization suites must stay green |
| 4 | Phase 4: audit route vocabulary | Pending | — | — | Blast radius measured: 4 call sites, 2 tests, 1 doc line |
| 5 | Phase 5: sources, classification, completeness | Pending | — | — | Skips the already-fixed workflow-schema-version sub-claim |
| 6 | Phase 6: regeneration, docs, deployment verification | Pending | — | — | Single commit with the generator, schema and all 11 manifests |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | blocked - pending owner approval before step 1: gate enum membership (UNK-01), manifest field-set approval record (UNK-02), and `health_contracts.disposition` removal vs derivation (UNK-03) | No | — |
| 6 | blocked - pending owner decision before step 6 if UNK-02 is refused: the ADR-015 row is then skipped and reported as a scope amendment | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| N/A: no follow-up work item created at planning time | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261117-123014_adrchk014_contract-manifest-sources.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-181257
- **Related target files**: `tools/generate_reference_table.py`, `tools/_contract_manifests.py`, `schemas/contract_manifest.json`, `scripts/eventbus/auth.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/app.py`, `scripts/eventbus/audit.py`, `tests/tools/test_generate_reference_table.py`, `tests/eventbus/test_eventbus_route_registry.py`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_authz_generation_ttl.py`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_11_04_memory-module-reference-generated.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `registry/manifests/invariant_coverage.yaml`, `registry/manifests/eventbus_route_roles.yaml`, `registry/manifests/health_contracts.yaml`, `registry/manifests/db_schema_versions.yaml`, `registry/manifests/agent_api.yaml`, `registry/manifests/component_mandatoriness.yaml`, `registry/manifests/config_ownership.yaml`, `registry/manifests/mcp_endpoints.yaml`, `registry/manifests/tool_ownership.yaml`, `registry/manifests/eventbus_api.yaml`, `registry/manifests/memory_api.yaml`, `tools/check_module_size_tools_baseline.txt`

Traceability:
- Issue "gate column holds the wrong data" -> Design (D-01, D-02) -> Implementation (Phase 2, Phase 6) -> Validation (T-001, T-002, T-003; gates "Manifest freshness", "Schema rejection")
- Issue "route-role manifest is not enforced and lists routes that do not exist" -> Design (D-03, D-04) -> Implementation (Phase 3, Phase 6) -> Validation (T-005, T-006, T-007, T-008; gate "Enforcement unchanged")
- Issue "audit records and docstrings use non-route paths" -> Design (D-05) -> Implementation (Phase 4) -> Validation (T-012, T-013; gate "No leftover contract text")
- Issue "`disposition` is a generator constant" -> Design (D-06) -> Implementation (Phase 1, Phase 5, Phase 6) -> Validation (T-014; gate "Manifest freshness")
- Issue "classifications and descriptions are inconsistent" -> Design (D-07, D-08, D-09) -> Implementation (Phase 5, Phase 6) -> Validation (T-009, T-010; gate "Documentation freshness")
- Issue "API reference is incomplete" -> Design (D-09) -> Implementation (Phase 5, Phase 6) -> Validation (T-011; gate "Documentation freshness")
- Issue constraint "regenerate, never hand-edit; no migrations or shims" -> Design (D-10) -> Implementation (Phase 6) -> Validation (AC-011, AC-012; gates "Manifest freshness", "No leftover contract text")
- Issue acceptance "a test asserts registered route roles match the manifest" -> Design (D-03) -> Implementation (Phase 3) -> Validation (T-007, T-008)
- Stale claim "phantom workflow schema version rows" -> Design (N/A: already resolved in current source) -> Implementation (N/A: skipped) -> Validation (evidence recorded in Problem)

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes ("Store Blocking as `gate`"); `tools/generate_reference_table.py:751` unpacking | `tools/generate_reference_table.py` | Phase 2 | AC-001 | T-001 | Confirmed by repository evidence |
| REQ-001 | `registry/manifests/invariant_coverage.yaml` gate distribution measured in Step 2 | `registry/manifests/invariant_coverage.yaml` | Phase 2, Phase 6 | AC-001, AC-011 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria ("schema rejects a `gate` value other than ..."); `schemas/contract_manifest.json:230` | `schemas/contract_manifest.json` | Phase 1 | AC-001 | T-003 | Explicit in issue |
| REQ-003 | Required Changes ("keep Type as a separate enum field"); matrix Type column distribution | `schemas/contract_manifest.json` | Phase 1 | AC-002 | T-002, T-003 | Explicit in issue |
| REQ-003 | Required Changes; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md:129-135` | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Phase 6 | AC-011 | `check_adr_reference.py` | Needs confirmation (UNK-02 approval) |
| REQ-004 | Target Files (`_ROUTE_ROLE_MAP`); `scripts/eventbus/auth.py:78`, `:300`; `EXPECTED_ROUTES` | `scripts/eventbus/auth.py` | Phase 3 | AC-003 | `TestProductionRouteWiring`, T-008 | Confirmed by repository evidence |
| REQ-004 | Required Changes ("Derive route roles from the FastAPI routes"); generator lines 572-580 | `tools/generate_reference_table.py` | Phase 3 | AC-003 | T-005, T-006 | Explicit in issue |
| REQ-004 | `registry/manifests/eventbus_route_roles.yaml` phantom keys | `registry/manifests/eventbus_route_roles.yaml` | Phase 3, Phase 6 | AC-003 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-005 | Required Changes ("allow `{}` in the schema route pattern"); `schemas/contract_manifest.json:120` | `schemas/contract_manifest.json` | Phase 1 | AC-003 | T-004 | Explicit in issue |
| REQ-006 | Acceptance Criteria; `tests/eventbus/test_eventbus_route_registry.py:25-35` | `tests/eventbus/test_eventbus_route_registry.py` | Phase 3 | AC-004 | T-007, T-008 | Explicit in issue |
| REQ-007 | Target Files (route strings and docstrings); `dlq_route.py:80`, `ack_route.py` `_do_ack`, `authz_ttl.py:112`, `app.py:81` | `scripts/eventbus/dlq_route.py` | Phase 4 | AC-005 | T-012 | Confirmed by repository evidence |
| REQ-007 | `scripts/eventbus/authz_ttl.py:112` and its assertion | `scripts/eventbus/authz_ttl.py` | Phase 4 | AC-005 | T-013 | Confirmed by repository evidence |
| REQ-007 | `scripts/eventbus/app.py:81` | `scripts/eventbus/app.py` | Phase 4 | AC-005 | `tests/eventbus/` startup assertions | Confirmed by repository evidence |
| REQ-007 | `_do_ack` docstring naming `/ack` | `scripts/eventbus/ack_route.py` | Phase 4 | AC-005 | `tests/eventbus/test_eventbus_ack_nack.py` | Confirmed by repository evidence |
| REQ-007 | `scripts/eventbus/audit.py:138-155` docstring | `scripts/eventbus/audit.py` | Phase 4 | AC-005 | T-012, T-013 | Derived from confirmed evidence |
| REQ-007 | `tests/eventbus/test_eventbus_dlq.py:1301` | `tests/eventbus/test_eventbus_dlq.py` | Phase 4 | AC-005 | T-012 | Confirmed by repository evidence |
| REQ-007 | `tests/eventbus/test_authz_generation_ttl.py:148` | `tests/eventbus/test_authz_generation_ttl.py` | Phase 4 | AC-005 | T-013 | Confirmed by repository evidence |
| REQ-007 | `docs/24_eventbus/eventbus_07_configuration-and-operations.md:97` | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 4 | AC-005 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-008 | Reason for Change / Required Changes ("Remove `disposition` or derive it"); generator line 712 | `tools/generate_reference_table.py` | Phase 5 | AC-010 | T-014 | Explicit in issue |
| REQ-008 | `schemas/contract_manifest.json:211` | `schemas/contract_manifest.json` | Phase 1 | AC-010 | T-014 | Confirmed by repository evidence |
| REQ-008 | `registry/manifests/health_contracts.yaml` entries | `registry/manifests/health_contracts.yaml` | Phase 6 | AC-010, AC-011 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-009 | Required Changes (source lists); `_MANIFEST_SOURCES` lines 460-476 | `tools/generate_reference_table.py` | Phase 5 | AC-006 | T-009 | Confirmed by repository evidence |
| REQ-009 | `registry/manifests/db_schema_versions.yaml` sources; `_db_path_entries` reads `config/agent.toml` (line 221), which is a Reference File, not a modification target | `registry/manifests/db_schema_versions.yaml` | Phase 5, Phase 6 | AC-006, AC-008 | T-009 | Confirmed by repository evidence |
| REQ-009 | Welcome line mismatch, generator line 441 | `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Phase 5, Phase 6 | AC-006 | Documentation freshness gate | Confirmed by repository evidence |
| REQ-010 | Required Changes ("one bound or unbound classification"); lines 484, 491, 989 | `tools/generate_reference_table.py` | Phase 5 | AC-007 | T-010 | Confirmed by repository evidence |
| REQ-010 | `registry/manifests/component_mandatoriness.yaml` | `registry/manifests/component_mandatoriness.yaml` | Phase 6 | AC-007, AC-011 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-011 | Required Changes ("update the version description"); `schemas/contract_manifest.json:160-163` | `schemas/contract_manifest.json` | Phase 1 | AC-008 | T-009 | Confirmed by repository evidence |
| REQ-011 | `_PRAGMA_USER_VERSION_RE` at lines 73, 562 with no matching source text | `tools/generate_reference_table.py` | Phase 5 | AC-008 | T-009 | Confirmed by repository evidence |
| REQ-012 | Reason for Change / Required Changes; `_symbol_entries` lines 329-363 | `tools/generate_reference_table.py` | Phase 5 | AC-009 | T-011 | Explicit in issue |
| REQ-012 | `registry/manifests/agent_api.yaml` 171 entries | `registry/manifests/agent_api.yaml` | Phase 5, Phase 6 | AC-009 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-012 | Welcome line `scripts/agent/*.py` at `docs/23_agent/agent_13_reference-api-generated.md:32` | `docs/23_agent/agent_13_reference-api-generated.md` | Phase 6 | AC-009 | Documentation freshness gate | Confirmed by repository evidence |
| REQ-012 | No subpackages under `scripts/eventbus/` or `scripts/agent/memory/` | `registry/manifests/eventbus_api.yaml` | Phase 6 | AC-009, AC-011 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-012 | 24 files / 65 symbols measured under `scripts/agent/memory/` | `registry/manifests/memory_api.yaml` | Phase 6 | AC-009, AC-011 | Manifest freshness gate | Confirmed by repository evidence |
| REQ-013 | Constraints ("Do not edit the YAML files by hand"; Current-Specification-Only) | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Phase 6 | AC-012 | `check_compat_shims.py` (pre-commit) | Explicit in issue |
| REQ-013 | tools module-size baseline rule | `tools/check_module_size_tools_baseline.txt` | Phase 6 | AC-011 | `check_module_size.py --scripts-dir tools` | Derived from confirmed evidence |
| REQ-013 | All regenerated manifests, no hand edits | `registry/manifests/invariant_coverage.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/eventbus_route_roles.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/health_contracts.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/db_schema_versions.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/agent_api.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/config_ownership.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/mcp_endpoints.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-013 | Remaining regenerated manifests | `registry/manifests/tool_ownership.yaml` | Phase 6 | AC-011, AC-012 | Manifest freshness gate | Derived from confirmed evidence |
| REQ-014 | Required Changes ("bump the manifest version"); `tools/_contract_manifests.py:23` | `tools/_contract_manifests.py` | Phase 1 | AC-011 | T-009 | Explicit in issue |
| REQ-014 | Envelope `version` in every committed manifest | `registry/manifests/component_mandatoriness.yaml` | Phase 6 | AC-011 | Manifest freshness gate | Confirmed by repository evidence |

### Open Questions / Unknowns
- UNK-01 Gate enum membership vs the `Deployment Blocking` value used by 6 matrix rows (Blocking: True) — see `## Unknowns`.
- UNK-02 Approval record for the manifest field-set change before ADR-015 is edited (Blocking: True) — see `## Unknowns`.
- UNK-03 `health_contracts.disposition`: removal or derivation from ADR-004 (Blocking: True) — see `## Unknowns`.
- UNK-04 Naming of the two non-route audit identifiers (Blocking: False, plan default stated) — see `## Unknowns`.
- UNK-05 Whether `agent_api` includes `scripts/agent/memory/` (Blocking: False, plan default stated) — see `## Unknowns`.
- UNK-06 Direction of the memory source-description unification (Blocking: False, plan default stated) — see `## Unknowns`.
- UNK-07 Machine-checking Blocking-gate approval records (Blocking: False, out of scope; sibling matrix-checks issue) — see `## Unknowns`.
