# Plan: Contract Manifests and Tightened ADR Invariant Coverage States

**Plan ID:** 20261030-001153-adrcov001
**Source Issue:** `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md` (SHA256: e28a0c34228674c4287313e9375a89a716bfcbe476751759252688ea3b6e8367)
**Task Classification:** Path B (medium; checker/CI semantics extension + manifest generation pipeline)
**Status:** Draft

## Goal
Extend the existing ADR invariant matrix and its checkers so skipped/xfailed evidence
counts as unverified and manual coverage has cadence and expected evidence, and generate
machine-readable contract manifests under `registry/` that both documentation blocks and
CI consume from one source.

## Priority
Low (P3). Existence and run checks already fail the build for missing/dangling evidence;
this strengthens guarantees and removes duplicate inventories. Not time-sensitive
(issue Reason for Change).

## Scope
**In-Scope**:
- Coverage-state vocabulary in `adr_01_index.md`: map `Confirmed`/`Partial`/`Manual`/
  `Not verified` onto the memo states, add `Static` and `Runtime-observed` evidence
  kinds, cadence + expected-evidence fields for `Manual`/`Partial`, and an approved-
  exception process recorded in the matrix.
- Skip/xfail detection: static marker detection in `check_adr_invariant_matrix.py`;
  runtime skip/xfail results in `.github/run_cited_adr_tests.py`.
- Manifest generation: new outputs of the `generate_reference_table.py` pattern writing
  YAML manifests under `registry/manifests/`; Markdown guard blocks generated FROM the
  manifests; drift failure in CI (`--check` + pre-commit).
- Manifests for: tool ownership, MCP endpoints, EventBus route-role mapping, DB schema
  and version, configuration ownership, health contracts, invariant coverage.
- Removal of superseded hand-maintained copies only after migration.

**Out-of-Scope**:
- The ADR authority/assumption models and the mandatoriness registry themselves (adrauth001,
  mcpgate001); this plan consumes their sources when they exist (see Phases).
- Full-suite-on-every-commit, re-deciding any invariant.
- Weakening/reclassifying any Blocking invariant to pass new checks (issue constraint).

**Dependencies**:
- Consumes mcpgate001 plan (`plans/20261030-001153_mcpgate001_*`) component-mandatoriness
  registry and adrauth001 plan (`plans/20261029-214650_adrauth001_*`) authority outputs —
  those manifests land only after those plans land.
- Coverage-state work and the independent manifests can proceed first (issue Dependencies).

## Background
### Codebase Context (directly verified 2026-10-30 + evidence-based audit, HEAD `c5a8285dd` + staged plans)
- Matrix: `docs/10_adr/adr_01_index.md` `## ADR Invariant Verification Matrix` :99, status
  vocabulary :105 (`Confirmed`/`Partial`/`Manual`/`Not verified`), canonical declaration
  :107, table data rows :111-147.
- `tools/check_adr_invariant_matrix.py` (pre-commit hook `.pre-commit-config.yaml:56`):
  ERROR severity body rules, cites test-file existence + pytest node `::` segment
  resolution via AST, body↔index containment rules; contains NO skip/xfail logic (verified).
  `tools/check_adr_reference.py` (hook :62): `# ADR-NNN` markers required in cited scripts.
- CI: `.github/workflows/ci.yml:43` runs `.github/run_cited_adr_tests.py`, which imports
  the checker's node-id regex as a single source and executes `pytest <nodeid> -m "not
  integration"`; no skip-result handling.
- Generated blocks: `tools/generate_reference_table.py --check` guards AUTO-GENERATED blocks
  (`mcp`, `rag`, `deployment`, `agent`, `eventbus` types; guard-comment pattern confirmed).
- Manifest convention today: TOML under `config/` (17 files) + `tools/schemas/` JSON schemas;
  no YAML manifests; `registry/` does not exist. Owner decision 2026-10-30: manifests are
  YAML under `registry/` (PyYAML `>=6.0` already a dependency).
- Checker library convention: `tools/_docs_consistency_lib.py` `Issue` / `report_and_exit`
  and `--format json` are shared by `check_adr_invariant_matrix.py`,
  `check_adr_reference.py`, `check_adr_structure.py`, `check_db_separation.py`.
- Existing skip inventory (audited): 27 skip/skipif sites, 0 xfail markers; NONE carries a
  GitHub issue or ADR reference. At least one cited matrix test is environment-skip-gated:
  `tests/agent/memory/test_memory_vec_session.py` (cited for ADR-008 INV-08) skips when
  sqlite-vec is absent. Migration must classify such cites as approved exceptions or
  re-cite them.
- Current not-covered facts the invariant-coverage manifest will surface (verified):
  ADR-008 INV-06/07/09/10/11/12 untested; ADR-009 INV-05/06/08/09/11 untested; ADR-010
  INV-02/08/09/10 untested, INV-05 Partial (stubbed run); ADR-007 INV-01/02/10 structural
  only; ADR-014 INV-01/INV-03 Manual. These match existing `Manual`/`Partial` matrix rows;
  no new reclassification is implied.

### Corrections to Issue Claims
None material. Issue anchors (:105, :109, pre-commit :56/:62, ci.yml :43, "skipping the
header row" as only skip-ish match) all verified.

### Historical Context
- `adrgate005` (archived) delivered existence + node-resolution enforcement; this plan is
  its explicit successor (issue Dependencies), extending the same checkers per the AI
  instruction ("extend them rather than adding a parallel mechanism").

## Problem
1. A cited test that is skipped or xfailed still "passes" the run gate, so Blocking
   invariants can silently lose real coverage.
2. `Manual`/`Partial` rows have owners but no cadence or expected evidence, so manual
   coverage decays invisibly.
3. Contract lists (tool ownership, endpoints, route roles, schema versions, config
   ownership, health contracts) exist as hand-maintained or document-embedded copies with
   no machine-readable single source consumable by CI and startup validation.

## Reason for Change
Strengthens the ADR evidence chain that the rest of this batch (adrauth001, mcpgate001,
adrcov001's own manifests) increasingly depends on. Low urgency, high leverage as those
contracts land.

## Implementation Intent
Extend the existing matrix vocabulary and the existing checker/runner/generator trio; do
not build parallel tooling. Static marker detection belongs in the checker (markers are
visible in the AST); runtime skip results belong in the CI runner (only it sees pytest
outcomes) — this split resolves the issue's first unresolved question. Existing
`Partial`/`Manual` rows keep their state in migration but must gain cadence and
expected-evidence fields within the migration window; the checker warns first, then fails
(stepped enforcement), which resolves the third unresolved question.

## Requirements
- `REQ-001`: `adr_01_index.md` defines the coverage-state vocabulary (existing four
  values mapped to the memo states), `Static` vs `Runtime-observed` evidence kinds,
  cadence + expected-evidence requirements for `Manual`/`Partial`, and the approved-
  exception process recorded in the matrix itself.
- `REQ-002`: `check_adr_invariant_matrix.py` reports `ERROR` when a cited node carries a
  static `skip`/`skipif`/`xfail` marker without an approved exception recorded in the
  matrix row.
- `REQ-003`: `run_cited_adr_tests.py` exits non-zero when a cited node reports SKIPPED or
  XFAIL at runtime without an approved exception (pytest report parsing; keep `-m "not
  integration"` semantics).
- `REQ-004`: Manual/Partial rows missing cadence/expected-evidence produce `WARNING` in
  the migration window, then `ERROR` (single flag flip in the checker constant).
- `REQ-005`: `generate_reference_table.py` gains a manifest mode: writes YAML manifests to
  `registry/manifests/` (one file per contract, schema-validated against a new
  `tools/schemas/contract_manifest.json`) and renders Markdown guard blocks FROM those
  manifests; `--check` detects drift in both directions (manifest vs source, block vs manifest).
- `REQ-006`: Manifests: `tool_ownership`, `mcp_endpoints`, `eventbus_route_roles`,
  `db_schema_versions`, `config_ownership`, `health_contracts`, `invariant_coverage`
  (sources: `config/agent.toml` + per-server configs; `scripts/eventbus/` authz route-role
  mapping; `scripts/db/schema_sql.py` + `scripts/eventbus/schema.sql` + migration version
  tables; `scripts/agent/services/config_field_registry.py`; posture/health contract
  definitions; `adr_01_index.md` matrix).
- `REQ-007`: Deferred manifests `component_mandatoriness`, `adr_authority`,
  `architecture_assumptions` are added only when mcpgate001 / adrauth001 sources exist;
  their absence must not fail the manifest pipeline (explicit deferred-state).
- `REQ-008`: CI + pre-commit consume manifest drift checks; superseded hand-maintained
  tables are removed only after their generated replacement passes `--check`.
- `REQ-009`: No Blocking invariant is reclassified; genuinely missing evidence surfaces as
  a failure or a named exception (issue AI instruction).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on
2026-10-30: every row exists-or-is-new-with-evidence, is linked to a Plan requirement,
and is `Verified` against `HEAD c5a8285dd` — matrix Manual/Partial rows, the 27
skip/skipif sites with zero issue/ADR references, the zero xfail markers, and the
`check_adr_invariant_matrix.py`/`run_cited_adr_tests.py` split of static vs runtime
states re-confirmed by direct scan; `check_workitem_structure.py` reports no findings;
cross-plan pairs reported by `check_plan_target_overlaps.py` are recorded sequenced in
Dependencies.)

| File Path | Change Type | Notes | Priority | Dependencies | Estimated Complexity |
|---|---|---|---|---|---|
| docs/10_adr/adr_01_index.md | docs | coverage-state vocabulary, mapping table, exception process, cadence fields populated for current Manual/Partial rows | P1 | none | Medium |
| tools/check_adr_invariant_matrix.py | refactor | static skip/xfail marker detection; cadence/expected-evidence validation; exception column parsing | P1 | adr_01_index.md vocabulary | Medium |
| .github/run_cited_adr_tests.py | refactor | runtime SKIPPED/XFAIL result handling + exception allowlist from matrix | P1 | REQ-001 | Medium |
| docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md | docs | describe manifest outputs as an ADR-015 generation extension | P1 | manifest pipeline | Low |
| tools/generate_reference_table.py | refactor | manifest mode + render guard blocks from manifests; --check two-way drift | P1 | none | High |
| tools/schemas/contract_manifest.json | create | manifest schema (follows tools/schemas/doc_front_matter.json convention) | P1 | none | Low |
| registry/manifests/tool_ownership.yaml | create (generated) | generated by manifest mode | P1 | generator | Low |
| registry/manifests/mcp_endpoints.yaml | create (generated) | from configs | P1 | generator | Low |
| registry/manifests/eventbus_route_roles.yaml | create (generated) | from scripts/eventbus authz route-role mapping | P1 | generator | Medium |
| registry/manifests/db_schema_versions.yaml | create (generated) | schema_sql.py + eventbus/schema.sql + migration versions (coordinates with dbmig001's version framework) | P1 | generator; dbmig001 sequencing | Medium |
| registry/manifests/config_ownership.yaml | create (generated) | from config_field_registry.py | P1 | generator | Low |
| registry/manifests/health_contracts.yaml | create (generated) | posture/health contract definitions | P1 | generator | Medium |
| registry/manifests/invariant_coverage.yaml | create (generated) | from adr_01_index.md matrix + checker output | P1 | REQ-001/002 | Medium |
| .github/workflows/ci.yml | config | manifest drift-check step | P1 | generator | Low |
| .pre-commit-config.yaml | config | manifest-check hook (mirrors :56/:62 pattern) | P1 | generator | Low |
| tests/tools/test_check_adr_invariant_matrix.py | test | marker-detection, cadence-missing, exception-recorded cases (synthetic repo fixtures) | P1 | checker | Medium |
| tests/tools/test_run_cited_adr_tests.py | create | runner skip/xfail-result fixtures | P1 | runner | Medium |
| tests/tools/test_generate_reference_table.py | test | manifest reproducibility + two-way drift cases | P1 | generator | Medium |
| docs/22_mcp/mcp_01_tool_ownership_matrix.md | docs | block now rendered from the manifest (guard markers unchanged) | P2 | generator | Low |
| docs/24_eventbus/eventbus_08_reference_api.md | docs | same rendering path (eventbus type) | P2 | generator | Low |
| docs/23_agent/agent_13_reference-api-generated.md | docs | same rendering path (agent type) | P2 | generator | Low |
| tools/TOOL_DESCRIPTIONS.md | docs | register manifest mode/flags for generate_reference_table.py | P2 | generator | Low |

Explicitly excluded from target files:
- `tools/check_adr_reference.py` — verified no change needed (marker rules unaffected).
- `registry/component_mandatoriness.yaml` (mcpgate001's file — consumed as a manifest
  source later, REQ-007), `config/adr_authority.toml` (adrauth001's file).
- Any ADR body other than adr_015 (ADR-001..014 invariant texts are frozen).

## Reference Files
- tools/check_adr_invariant_matrix.py + tests/tools/test_check_adr_invariant_matrix.py — extension targets and test pattern (synthetic repo fixtures)
- tools/_docs_consistency_lib.py — Issue/report_and_exit/--format json convention
- tools/check_db_separation.py — live-repo drift checker pattern
- docs/00_governance/governance_01_docs-document-standards.md — heading standards touched by adr_01_index edits
- skills/DESIGN.md — Docs content policy

## Acceptance Criteria
- AC-1: A cited node with a static skip/xfail marker and no recorded exception fails
  `check_adr_invariant_matrix.py` (demonstrated with synthetic fixtures).
- AC-2: A cited node that SKIPS at runtime fails `run_cited_adr_tests.py` unless an
  approved exception is recorded in the matrix (demonstrated in fixtures; the sqlite-vec
  cite on `test_memory_vec_session.py` is explicitly decided: exception-recorded or re-cited).
- AC-3: Every `Manual`/`Partial` row in `adr_01_index.md` names owner, procedure, expected
  evidence, and cadence after migration; missing fields warn, then error after the
  migration window.
- AC-4: All seven manifests regenerate deterministically (byte-stable diff review),
  schema-validate, and their Markdown blocks regenerate from them; a source edit without
  regeneration fails `--check` in CI and pre-commit.
- AC-5: Superseded hand-maintained copies are removed only after the generated equivalent
  passes `--check`; generated blocks are not normative sources (ADR-015 INV-01 preserved).
- AC-6: No Blocking invariant row changed state; diff of the matrix shows added fields
  only.

## Tests
### New
- `tests/tools/test_run_cited_adr_tests.py`.
- Extension cases in `tests/tools/test_check_adr_invariant_matrix.py` (skipped test,
  xfailed test, missing cadence, state mapping — issue Testing Expectations).
- Manifest reproducibility + drift cases in `tests/tools/test_generate_reference_table.py`.
### Modified
- None beyond the above.
### Regression
- `test_ci_runner_regex_import_still_works`-style single-source test extended for the
  new result-parsing code path.

## Documentation Impact
Yes: `adr_01_index.md` (states, mapping, exception process), ADR-015 (manifest outputs).
Intent and boundaries only per `skills/DESIGN.md`. `docs/00_index.md` task-scope mapping
applies at implementation time; docs checkers in `routing.md` must pass.

## Assumptions
- A-1: Manifest home/format fixed by owner decision 2026-10-30: YAML under
  `registry/manifests/` (PyYAML already a dependency).
- A-2: Skip/xfail detection split: static markers in the checker, runtime results in the
  runner (resolution of issue Unresolved #1; recorded as plan decision).
- A-3: Existing `Partial` rows keep their state; cadence/expected-evidence fields are
  backfilled in Phase 1 with stepped warning→error enforcement (resolution of issue
  Unresolved #3).

## Unknowns
- U-1: Exact EventBus route-role source (module names under `scripts/eventbus/`) — pinned
  at implementation start from the ebauthgen001 verification; manifest generator reads a
  declared source file, so a move is a config change.
- U-2: `db_schema_versions` manifest depends on dbmig001's schema-version framework
  landing; until then the manifest carries current static schema hashes only (explicit
  deferred-state under REQ-007).
- U-3: Which of the 27 audited skips are reachable by cited matrix nodes (at least one
  is: `test_memory_vec_session.py`); the full classification is a Phase 1 output, each
  resolved as exception-recorded, re-cite, or skip-removal.

## Affected areas
- docs/10_adr (2), tools (2 extended, 1 schema), tests/tools (3), .github (2),
  .pre-commit-config.yaml, registry/manifests/ (new), docs/22_mcp + docs/24_eventbus +
  docs/23_agent (1 each, re-rendered)

## Design
### Current Architecture
Matrix (human) → checker (static existence) → CI runner (execute cites) → separate
generated Markdown blocks → hand-maintained operational tables. No run-result feedback,
no machine-readable manifests.

### Target Architecture
Matrix (human, with states/exceptions/cadence) → checker (existence + markers + fields) →
runner (execution + result semantics) → invariant_coverage manifest ← manifests generated
from code/config sources → Markdown guard blocks rendered from manifests → CI/pre-commit
two-way drift gates. Deferred manifests declare their pending sources explicitly.

### Key Components
1. Matrix vocabulary extension (docs-first; checkers parse it).
2. Checker marker detection (AST decorators already parsed for node resolution — reuse).
3. Runner result parsing (pytest report outcome per cited nodeid).
4. Generator manifest mode (sources → validated YAML → Markdown blocks; one renderer).

## Implementation steps
### Phase 1: Coverage states (independently reviewable; issue AI instruction: separate steps)
- adr_01_index.md vocabulary + backfill + exception process; checker marker/field rules;
  runner result rules; tests; matrix cites for environment-gated skips decided (AC-2).
- Done when: AC-1..AC-3 fixtures pass and `pre-commit` hooks are green on the live repo.
### Phase 2: Manifest pipeline core
- Schema + generator manifest mode + renderer + drift `--check`; tool_ownership and
  mcp_endpoints as pilot manifests; Markdown blocks re-rendered from manifests; CI/pre-commit wiring.
- Done when: AC-4 holds for the pilot manifests; superseded copies removed (AC-5).
### Phase 3: Remaining independent manifests
- eventbus_route_roles, db_schema_versions (static-hash form), config_ownership,
  health_contracts, invariant_coverage.
- Done when: AC-4 holds for all seven.
### Phase 4: Dependent manifests (blocked, explicitly deferred)
- component_mandatoriness (after mcpgate001 lands), adr_authority +
  architecture_assumptions (after adrauth001 lands).
- Done when: source files exist and manifests validate; deferred-state flags removed.

## Validation plan
- Issue-specified: `uv run python tools/check_adr_invariant_matrix.py`,
  `uv run python tools/check_adr_reference.py`,
  `uv run python tools/generate_reference_table.py --check`, docs checkers in `routing.md`
  (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`,
  `check_docs_consistency.py` for touched domains), `check_tool_descriptions_sync.py`.
- `uv run pytest tests/tools/`; runner fixtures run in CI-equivalent env.
- `uv run mypy tools/check_adr_invariant_matrix.py tools/generate_reference_table.py
  .github/run_cited_adr_tests.py` explicitly (mypy default scope excludes tools/),
  `ruff`, `bandit` on changed tools.
- CI-equivalence: verify the new ci.yml step and pre-commit hook locally before landing.

## Risks
| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| Skip/xfail gate breaks the build on the day it lands (27 existing skips, some cited) | Medium | High | Phase 1 explicitly classifies every cited skip as exception-recorded/re-cited before enabling ERROR; environment-conditional cites get approved exceptions |
| Manifest mode turns generate_reference_table.py into an oversized module | Medium | Medium | check_module_size gate; extract manifest rendering into a dedicated module if needed |
| Manifest-as-source changes what is normative (ADR-015 INV-01) | High | Medium | Docs state manifests are derived artifacts; sources remain config/code; ADR-015 wording updated in Phase 2 review |
| adr_01_index.md edit conflicts with dbmig001/adrauth001/turnadr001 row edits | Low | Medium | Sequenced in Dependencies; adrcov001 lands last among them |
| Deferred manifests silently missing when their sources land | Low | Medium | Deferred-state entries asserted by tests + Phase 4 gate |

## Dependencies
- Consumes: mcpgate001 plan (mandatoriness registry), adrauth001 plan (ADR authority),
  dbmig001 plan (schema-version framework for `db_schema_versions`) — Phase 4 / U-2.
- Shared `docs/10_adr/adr_01_index.md` with dbmig001, adrauth001, turnadr001 plans:
  landing order adrauth001 → dbmig001 → turnadr001 → adrcov001 (each touches disjoint
  sections; this plan touches the matrix vocabulary and its own rows only).
- Successor of archived adrgate005 (re-verified above).

## Execution Status
| Phase | Status |
|---|---|
| Phase 1 | not started |
| Phase 2 | not started |
| Phase 3 | not started |
| Phase 4 | blocked (mcpgate001, adrauth001 not yet implemented) |

## Traceability
- Issue source: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`

## Requirement Traceability
- Issue Required Change 1 (coverage states + mapping + cadence) → REQ-001, AC-3 → Phase 1.
- Issue Required Change 2 (skipped/xfailed unverified unless exception; keep failing on missing nodes) → REQ-002/003/004, AC-1/2 → Phase 1.
- Issue Required Change 3 (machine-readable manifests, named set) → REQ-005/006/007, AC-4 → Phases 2-4.
- Issue Required Change 4 (blocks from manifests; drift fails CI) → REQ-005/008, AC-4 → Phase 2.
- Issue Required Change 5 (remove superseded copies after migration) → REQ-008, AC-5 → Phase 2+.
- Issue AC "manual coverage records owner/procedure/evidence/cadence" → REQ-001/004 → Phase 1.
- Issue Unresolved #1/#2/#3 → A-2 / A-1 (owner decision) / A-3.
