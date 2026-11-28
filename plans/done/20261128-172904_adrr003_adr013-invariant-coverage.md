## Goal
- Register every ADR-013 invariant (INV-01 to INV-07) in the ADR index verification matrix and the generated invariant coverage manifest with concrete existing test nodes, correct the two mislabeled evidence rows in the ADR-013 body, and add the TTL-precedence and generation-publication evidence once the tests of the two prerequisite Plans exist, so the cited-test CI gate protects all seven invariants.

## Priority
Medium

## Scope
- **In-Scope**: Add index matrix rows for ADR-013 INV-01, INV-03, INV-04, INV-05, and INV-06 (and update the Pipeline Mapping Summary row that lists the confirmed ADR-013 invariants); relabel the two one-generation rows of the ADR-013 Automated Tests table to the decision they verify; add body rows for the route-registry evidence and for the TTL-precedence and publication tests; regenerate `registry/manifests/invariant_coverage.yaml` with the repository generator; update the pinned cited-node count in `tests/test_run_cited_adr_tests.py`.
- **Out-of-Scope**: admin route behavior (the admin TTL-precedence Plan and the publication-boundary Plan); any ADR decision text; a new invariant for the one-generation decision (rows are labeled by Decision Detail, an existing convention in the same table); hand-editing the generated manifest.
- **Dependencies**: Needs the final test node names of the admin TTL-precedence Plan (adrr001) and the publication-boundary Plan (adrr002) for the TTL-precedence and publication evidence rows. Both are sequencing dependencies recorded below; the invariant rows themselves cite only tests that exist today.
  - **Depends on**: plans/20261128-172318_adrr001_admin-ttl-precedence.md | phase 2 | the stale-generation plus invalid-TTL test names are created by its test phase
  - **Depends on**: plans/20261128-172526_adrr002_authz-publication-invariant.md | phase 5 | the forced-interleave, race, and mixed-generation test names are created by its test phases

## Background
Verified against `HEAD` cc659c70a on 2026-11-28 (checked in Step 2, Step 3):
- `docs/10_adr/adr_01_index.md:228` is the only ADR-013 matrix row (`ADR-013 INV-02, INV-07`), and `registry/manifests/invariant_coverage.yaml` has one matching `adr: ADR-013` entry (`:396-405`). INV-01, INV-03, INV-04, INV-05, and INV-06 have no row (confirmed).
- The ADR-013 body Automated Tests table (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md:244-266`) already names concrete nodes for them. All cited nodes collect and run under `pytest` (14 nodes collected from the INV-01, INV-03, INV-04, INV-05, INV-06 rows and the two one-generation rows).
- The two rows "One-generation publish" and "Failed rebuild preserves previous generation's principals" are labeled `INV-01` (`:260-261`), but INV-01 is the unauthenticated-401 invariant (`:207`); the rows verify Decision Detail 9 (`:89`). The same table already labels rows by Decision Detail ("Decision Details #10", "Decision Details #12", `:247-248`).
- The Issue's "Admin route sentence concatenated" claim is refuted by the Issue itself; not part of this Plan.
- Gates are green today: `uv run python tools/check_adr_invariant_matrix.py` and `check_adr_structure.py` report no issues.
- Pinned count fallout (new finding): `tests/test_run_cited_adr_tests.py:155` asserts `len(helper.extract_cited_node_ids(lines)) == 75` against the live index, so registering new cited nodes changes the count.
- Same-file fallout (new finding): the Pipeline Mapping Summary row "CI (pull request), confirmed" at `docs/10_adr/adr_01_index.md:247` lists `ADR-013 INV-02 and INV-07` and must list the newly confirmed invariants.
- Evidence that helps INV-01 and INV-03 beyond the body table: `tests/eventbus/test_eventbus_route_registry.py` parametrizes `test_operator_route_rejects_missing_unknown_and_wrong_role` over the operator routes and `test_consumer_route_rejects_missing_token_and_wrong_role` over the consumer routes (401 for a missing or unknown token, 403 for a wrong role).

## Problem
Coverage for five of seven ADR-013 invariants is invisible to the matrix checker and the cited-test CI gate, so deleting their tests would not fail CI. Two evidence rows point at the wrong invariant, and a new evidence row for a mislabeled invariant would be rejected once INV-01 is registered.

## Reason for Change
Unregistered invariants are not protected against test deletion by the cited-test gate, and the ADR-013 TTL-precedence and publication decisions (Decision Details 9, 13, 14) get automated tests from the two prerequisite Plans that should be cited.

## Implementation Intent
Update the canonical sources first (the ADR body, then the index matrix), then regenerate the manifest with `tools/generate_reference_table.py`, then update the pinned count from the live index. Register only evidence that exists; read each cited test and the invariant text before choosing `Confirmed` or `Partial` for a row.

## Requirements
- `REQ-001`: The index matrix has a row for each of ADR-013 INV-01, INV-03, INV-04, INV-05, and INV-06 with a concrete Type, Timing, Gate, and Verification Status backed by existing test nodes; the Pipeline Mapping Summary lists them; the existing INV-02/INV-07 row is unchanged.
- `REQ-002`: The two one-generation rows of the ADR-013 Automated Tests table are relabeled from `INV-01` to Decision Detail 9; no decision text changes.
- `REQ-003`: The ADR-013 body cites the route-registry tests as evidence for INV-01 and INV-03, and cites the TTL-precedence tests (Decision Detail 13), the forced-interleave and race tests (Decision Details 9 and 14) once those tests exist; every cited node exists.
- `REQ-004`: `registry/manifests/invariant_coverage.yaml` is regenerated by the repository generator (never hand-edited), and the pinned cited-node count in `tests/test_run_cited_adr_tests.py` equals the live count.
- `REQ-005`: Every cited ADR-013 node runs and passes, and the ADR checkers, reference generation check, and cited-test gate pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify: relabel the two one-generation rows, add the route-registry evidence rows and the TTL-precedence and publication evidence rows | Rows at `:260-261` carry the wrong invariant id; evidence for the new nodes must exist in the body (the checker reports index evidence with no body evidence) | `REQ-002`, `REQ-003`; AC-2, AC-3 | Automated Tests table at `:244-266`; INV-01 definition at `:207`; Decision Detail 9 at `:89` (checked in Step 3) | `N/A: documentation row, checked by the ADR checkers` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: add the five ADR-013 matrix rows and update the Pipeline Mapping Summary row | The matrix has only the `ADR-013 INV-02, INV-07` row (`:228`); the summary row at `:247` lists only those two | `REQ-001`; AC-1 | Matrix rows at `:228`; summary row at `:247` (checked in Step 3) | `tests/test_run_cited_adr_tests.py` | Verified |
| `registry/manifests/invariant_coverage.yaml` | Modify (generated): regenerate from the index matrix | The manifest is produced by `_invariant_coverage_entries` in `tools/generate_reference_table.py` from the index rows | `REQ-004`; AC-4 | `adr: ADR-013` entry at `:396-405`; generator reads `adr_01_index.md` (checked in Step 3) | `tests/tools/test_generate_reference_table.py` | Verified |
| `tests/test_run_cited_adr_tests.py` | Modify: update the pinned count and its history comment | `assert len(helper.extract_cited_node_ids(lines)) == 75` is computed from the live index | `REQ-004`; AC-4 | Assertion at `:155` with a dated comment history (checked in Step 3) | `tests/test_run_cited_adr_tests.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks.
- Order rows by implementation sequence: row N is the Nth implementation unit, and
  `plan-to-implementation-procedure` derives each procedure's `seq` from this 1-indexed
  position, so the rows of a `Frozen` table MUST NOT be reordered. Canonical
  implementation order lives in this table.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/generate_reference_table.py` | The generator that rebuilds the manifest; run it, do not edit its output | `registry/manifests/invariant_coverage.yaml`; `REQ-004` |
| `tools/check_adr_invariant_matrix.py` | States the checks the new rows must satisfy (node existence, body-to-index file coverage, index evidence with no body evidence, `Not verified` rows are Non-Blocking) | `docs/10_adr/adr_01_index.md`; `REQ-001` |
| `.github/run_cited_adr_tests.py` | Runs every cited node in CI; defines `extract_cited_node_ids`, which the pinned count uses | `tests/test_run_cited_adr_tests.py`; `REQ-004` |
| `tests/eventbus/test_eventbus_route_registry.py` | Source of the route-registry evidence nodes for INV-01 and INV-03 | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `REQ-003` |
| `tests/eventbus/test_eventbus_config.py` | Source of the INV-04 and INV-06 evidence nodes; read to judge whether a missing-key case is covered | `docs/10_adr/adr_01_index.md`; `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): ADR-013 INV-01 to INV-07 are each represented in the index matrix (INV-02 and INV-07 by the existing row), each row's Status follows the index definitions (`Confirmed` only when the cited nodes cover every part of the invariant; otherwise `Partial` with the unverified scope, `Cadence:`, and Owner), and the Pipeline Mapping Summary lists them.
- AC-2 (`REQ-002`): no row of the ADR-013 Automated Tests table other than the INV-01 evidence is labeled `INV-01`; the two one-generation rows name Decision Detail 9.
- AC-3 (`REQ-003`): every automated evidence entry in the ADR-013 body resolves to an existing test node; no evidence text says only `Confirmed`.
- AC-4 (`REQ-004`): `uv run python tools/generate_reference_table.py --check` passes after regeneration, and `tests/test_run_cited_adr_tests.py` passes with the updated pin.
- AC-5 (`REQ-005`): every cited ADR-013 node passes; `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `uv run python .github/run_cited_adr_tests.py` pass.

## Tests
- `REQ-001`, `REQ-003`, `REQ-005`: run every cited ADR-013 node with `pytest` and the cited-test gate `.github/run_cited_adr_tests.py`.
- `REQ-004`: `tests/test_run_cited_adr_tests.py` (the pin) and `tests/tools/test_generate_reference_table.py` (generator behavior) with the live check `generate_reference_table.py --check`.
- `REQ-002`: `check_adr_invariant_matrix.py` and `check_adr_structure.py`.

## Documentation Impact
- `REQ-001` to `REQ-003` change the ADR-013 body Automated Tests table and the ADR index matrix (found through `docs/00_index.md` "Document References by Task", ADR row). No decision text changes and no approval text is added. The manifest is generated output.

## Assumptions
- The one-generation tests are labeled by Decision Detail 9 rather than a new invariant: the same table already uses "Decision Details #N" labels (`:247-248`), so no maintainer decision for a new invariant is needed.
- A row's Status is decided by reading the cited tests against the invariant text at implementation time; `Confirmed` is used only when every part is covered, otherwise `Partial` with a named unverified scope, `Cadence:`, and Owner (index definitions, `docs/10_adr/adr_01_index.md:168`).
- The INV-03 body row also cites two Consumer-route role tests (`test_subscribe_as_wrong_role`, `test_nack_with_publisher_token_is_rejected`); because the checker requires body-cited test files to be covered by the index, the index row cites all nodes of the body row as supplemental evidence.
- The pinned count is taken from the live index after the rows are added (`extract_cited_node_ids`), not predicted.
- Overlap judgment: this Plan edits the ADR-013 body that the admin TTL-precedence Plan (one sentence in Decision Detail 12) and the publication-boundary Plan (one component-list line) also edit; the edits touch different sections, so the overlap is a sequencing dependency, implemented after both.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Final test node names of the admin TTL-precedence Plan and the publication-boundary Plan | Both Plans are `Pending`; their tests do not exist yet | Implement both first (structured `Depends on` in Scope); cite only nodes that exist at that time | False |
| UNK-02 | Whether the INV-04 row (missing-key rejection) and the INV-06 row (post-start loopback verification) can be `Confirmed` | No test named for a missing required key was found by `rg "def test_.*(missing\|required\|absent)" tests/eventbus/test_eventbus_config.py`; the post-start socket check in `scripts/eventbus/app.py` has no test found | Read `load_config` required-key handling and `tests/eventbus/test_eventbus_startup.py` at implementation; cite an existing test for `Confirmed`, else record `Partial` with scope, Cadence, and Owner; do not add tests in this Plan | False |
| UNK-03 | Whether registering the Decision-Detail-labeled body rows (TTL precedence, publication) requires index rows | The checker rules were read from its help text only | Run `check_adr_invariant_matrix.py` after the body edit; if it flags them, cite them in the ADR-013 index row as supplemental evidence and update the pin | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low: ADR text; cited by the matrix checker and the cited-test CI gate | 13 | High (100% single author) | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium: parsed by `tools/check_adr_invariant_matrix.py`, `tools/generate_reference_table.py`, and `.github/run_cited_adr_tests.py` | 25 | High (100% single author) | not applicable (rsynced) |
| `registry/manifests/invariant_coverage.yaml` | Modify | Low: generated manifest, drift-checked | 12 | High (100% single author) | not applicable (rsynced) |
| `tests/test_run_cited_adr_tests.py` | Modify | Low: one pinned assertion | 8 | High (100% single author) | not applicable (rsynced) |

## Design
- Path B (4 target rows). Documentation and a test pin only; the architecture, import-graph, and operational analyses are not applicable (no module, interface, or schema changes), and the only code touched is one assertion.
- Order: ADR body first (canonical evidence, relabel), index second (rows cite the body's nodes), manifest third (generated from the index), pin last (computed from the live index).
- Planned row shape (statuses are decided at implementation, see UNK-02): INV-01 `Integration Test | CI | Blocking | Confirmed` citing the three body nodes plus the two route-registry tests; INV-03 `Integration Test | CI | Blocking | Confirmed` citing the five body nodes plus `test_operator_route_rejects_missing_unknown_and_wrong_role`; INV-04 `Unit Test` citing `test_load_config_rejects_unknown_key` and `test_load_config_rejects_wrong_type`; INV-05 `Unit Test` citing `test_no_credential_leakage_in_audit_records` and the two admin audit tests; INV-06 `Regression` or `Unit Test` citing `test_non_loopback_host_raises_value_error`.
- Consumer scan: no symbol, schema, or constant changes; readers of the index are the checker, the generator, and the CI runner (all read it unchanged in shape).
- Predictable fallout check: module size not applicable (no `scripts/` or `tools/` file gains code); skill size not applicable (no covered instruction file gains text); pinned counts: `tests/test_run_cited_adr_tests.py:155` pins 75 (target row); tool inventory: no tool added or removed (not affected); generated blocks: `registry/manifests/invariant_coverage.yaml` is regenerated (target row).
- Validation quality baseline: `N/A: no Python target under scripts/ or tools/`.
- Persisted schema check and operational dependency inspection: not applicable (documentation and a test pin).

## Implementation steps
1. **Phase 1: ADR body (`REQ-002`, `REQ-003`)**
   - [ ] Relabel the two one-generation rows to Decision Detail 9, add the route-registry evidence and, once they exist, the TTL-precedence, interleave, and race evidence rows (`REQ-002`, `REQ-003`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
2. **Phase 2: Index matrix (`REQ-001`)**
   - [ ] Add the five matrix rows and update the Pipeline Mapping Summary row, deciding each Status from the cited tests (`REQ-001`; `docs/10_adr/adr_01_index.md`)
3. **Phase 3: Regenerate the manifest (`REQ-004`)**
   - [ ] Run `uv run python tools/generate_reference_table.py` and review the diff; do not hand-edit (`REQ-004`; `registry/manifests/invariant_coverage.yaml`)
4. **Phase 4: Pinned count and validation (`REQ-004`, `REQ-005`)**
   - [ ] Update the pinned count and its comment from the live count (`REQ-004`; `tests/test_run_cited_adr_tests.py`)
   - [ ] Run the validation plan; no `scripts/` or `config/` file changes, so no deploy step is needed (`N/A: documentation, manifest, and test pin only`)

### Release units
**Unit**: matrix-registration | **Phases**: 2, 3, 4 | **Reason**: once the index rows exist the generated manifest drifts and the pinned count fails until the manifest is regenerated and the pin updated, so the three cannot be validated alone

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADR-013 cited nodes | Integration and unit | `uv run python .github/run_cited_adr_tests.py` | Every cited node, old and new, passes |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_01_index.md` | Static documentation checks | `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_invariant_matrix.py` | No findings |
| `registry/manifests/invariant_coverage.yaml` | Generated-output check | `uv run python tools/generate_reference_table.py --check` | No drift |
| `tests/test_run_cited_adr_tests.py` | Unit | `uv run pytest tests/test_run_cited_adr_tests.py tests/tools/test_generate_reference_table.py -q` | Pass with the updated pin |
| All target files | Gate run | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: A row is marked `Confirmed` while a part of the invariant has no test (INV-04 missing key, INV-06 post-start check) → **Mitigation**: UNK-02 resolution path; read the invariant text against the cited tests and use `Partial` with Cadence and Owner when a part is uncovered.
- **Risk**: The pinned count is updated to a predicted value that the live index disagrees with → **Mitigation**: compute the value from `extract_cited_node_ids` after the index edit.
- **Risk**: A TTL-precedence or publication node name changes after the prerequisite Plans are reviewed → **Mitigation**: cite names only after those Plans' test phases land; run every cited node.
- **Risk**: Overlapping ADR-013 edits with the two prerequisite Plans → **Mitigation**: structured `Depends on`; different sections of the file.
- **Risk**: Hand-editing the manifest hides generator drift → **Mitigation**: regenerate only, then `generate_reference_table.py --check`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relabel and add evidence rows in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | In Progress | — | — |  |
| 2 | Add the five matrix rows and the summary update in `docs/10_adr/adr_01_index.md` | In Progress | — | — |  |
| 3 | Regenerate `registry/manifests/invariant_coverage.yaml` | In Progress | — | — |  |
| 4 | Update the pin in `tests/test_run_cited_adr_tests.py` and run the validation plan | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261128-174125_01_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261128-174125_02_docs_10_adr_adr_01_index.md.md | 2, 4 | Procedure | Pending | — | — |
| implementations/20261128-174125_03_registry_manifests_invariant_coverage.yaml.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261125-103309_adrr003_adr013-invariant-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261128-172904
- **Evidence revision**: cc659c70a1811c504ec226a087ba3a39e85578bb
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_01_index.md`, `registry/manifests/invariant_coverage.yaml`, `tests/test_run_cited_adr_tests.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (rows for INV-01, INV-03 to INV-06); `docs/10_adr/adr_01_index.md:228` | `docs/10_adr/adr_01_index.md` | Step 2 | AC-1 | `check_adr_invariant_matrix.py`; cited-test gate | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (relabel); ADR-013 `:260-261`, INV-01 at `:207` | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 1 | AC-2 | `check_adr_invariant_matrix.py`; `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Issue Implementation Intent (TTL-precedence and publication evidence); `tests/eventbus/test_eventbus_route_registry.py` | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 1 | AC-3 | Cited-test gate; every cited node runs | Derived from confirmed evidence |
| REQ-004 | Issue Required Changes (regenerate manifest); `tools/generate_reference_table.py` `_invariant_coverage_entries` | `registry/manifests/invariant_coverage.yaml` | Step 3 | AC-4 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-004 | Pinned count at `tests/test_run_cited_adr_tests.py:155` | `tests/test_run_cited_adr_tests.py` | Step 4 | AC-4 | `tests/test_run_cited_adr_tests.py` | Confirmed by repository evidence |
| REQ-005 | Issue Testing Expectations | `docs/10_adr/adr_01_index.md` | Step 4 | AC-5 | `run_cited_adr_tests.py`; ADR checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-174125 -->