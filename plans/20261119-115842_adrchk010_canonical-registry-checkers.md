## Goal
- Repair the two Canonical Source checker tools (`tools/check_canonical_source_registry.py`, `tools/check_canonical_source_conflicts.py`) so their Blocking CI gates (GV-020, GV-019/GV-021) report every finding exactly once, with stable codes, deterministic output, and cwd-independent path resolution; then align the five defective rows of `config/documentation_canonical_sources.toml` with the governance specification, fix two governance-document inconsistencies, and clean two stale history-style notes in config/code comments.

## Priority
High

## Scope
- **In-Scope**:
  - Checker correctness fixes: severity consistency, cwd-anchored path resolution, validation-error wrapping (gate fix, deduplication, code numbering), semantic-detector main-path execution, finding routing, dead-code removal, CLI strictness and help text (`REQ-001`–`REQ-013`).
  - Registry configuration fixes: `eventbus.persistence-schema.bootstrap-ddl` source path, `agent.posture-failure-handling` note, `governance.policy` row, `overview.architecture-overview` claim type (`REQ-014`–`REQ-016`, `REQ-019`).
  - Governance proposal (prepare only, do not merge): add ADR-017 and ADR-004 to the `mcp.component-mandatoriness` owner list in the Resolution Matrix (`REQ-017`).
  - Documentation fixes: `governance_02` optional-field miscount (`REQ-018`).
  - Note/comment cleanup: `config/adr_authority.toml` "Transcribed" note, `tools/generate_reference_table.py` stale ADR reference comment (`REQ-020`, `REQ-021`).
  - Regression tests: failing-fixture tests added to the three existing checker test files before each fix.
- **Out-of-Scope**:
  - Splitting the two oversized checker modules (41349 B / 36416 B, both in `tools/check_module_size_tools_baseline.txt`) — deferred to a separate refactoring issue (see Unknowns).
  - Applying the Resolution Matrix owner change (ADR-017/ADR-004) without maintainer approval — proposal preparation only.
  - Renumbering GV-0xx gate rows in `docs/00_governance/governance_04_documentation-checks.md` — owned by the sibling adrchk011 governance work.
  - Changing GV-019/GV-020/GV-021 Blocking semantics — fixed behavior must match the existing gate definitions.
- **Dependencies**: Fix order against the sibling adrchk011 issue (ADR approval governance): checker-code phases are independent; the governance Matrix change and the `CANONICAL-009` code allocation must be sequenced after adrchk011 is planned to avoid conflicting governance proposals and code collisions.
  - **Depends on**: issues/20261117-123011_adrchk011_adr-approval-governance.md | phase 3 | The `mcp.component-mandatoriness` owner expansion (REQ-017) and any GV-code renumbering overlap adrchk011's governance scope; phase 3 proposals and the REQ-009 code allocation must be reconciled with adrchk011's plan before merge decisions.

## Background
- The Canonical Source Registry (`config/documentation_canonical_sources.toml`) declares, for each governed decision target, which documents are canonical. Two checker tools enforce it in CI as Blocking gates (`tools/_validation_gate_defs.py` GV-020/GV-019/GV-021; `docs/00_governance/governance_04_documentation-checks.md` section 13).
- The source issue catalogued defects in both checkers and five defective registry rows. Adversarial verification (this Plan's Step 2) reproduced every claim against current source and with fixture runs; see Repository Evidence below.

## Problem
- `check_canonical_source_registry.py`: a non-Accepted ADR reference is reported as an error by `RegistryEntry.validate()` and again as a warning by `find_non_accepted_adr()` in `validate_all()` — the same defect with two severities. Default registry path and `repo_root = Path.cwd()` make findings cwd-dependent: from `/tmp/opencode` the tool reports "Registry file not found" (exit 1), and with an absolute `--registry` it reports 20 bogus "source path does not exist" errors. Dozens of unused methods/attributes (vulture: 98 items) remain.
- `check_canonical_source_conflicts.py`: semantic detectors (`_run_detection_functions`) run only in the fallback/except path of `detect_all_conflicts`; `_wrap_validation_errors` drops errors whose text lacks the entry's `decision_target` (fixture: a missing-source-path error was dropped); one wrapped error is emitted once per matching entry (fixture: two identical `CANONICAL-007` findings); `classify_finding` compares the `CANONICAL-0XX` codes against `CANONICAL-C`/`CANONICAL-W` prefixes so every canonical finding routes to KNOWN_ISSUE; `CANONICAL-008` is reused by two detectors; a duplicate `return conflicts` exists (lines 944/946); the `--registry` help names the wrong default file.
- Registry configuration: `eventbus.persistence-schema.bootstrap-ddl` points to `scripts/db/schema_sql.py` while the DB docs name `scripts/eventbus/schema.sql` as the only DDL definition for that Decision Target; `agent.posture-failure-handling` notes "fail-open in development" against ADR-004 Group 1 item 1 (environment-specific policies banned; Alternative A rejected); `governance.policy` contradicts the Resolution Matrix row for `documentation-metadata`; `mcp.component-mandatoriness` registers `security-policy` although the Matrix limits owners to ADR 007/012/013 while ADR-004 Group 3 item 13 names the yaml source; `overview.architecture-overview` uses claim type `documentation-metadata` inconsistently.
- Governance docs: `governance_02` says "one optional field" in the Front Matter Example text while the spec lists two (`status`, `class`).
- Stale notes: `config/adr_authority.toml` line 9 keeps a history-style "Transcribed 2026-10-30" comment; `tools/generate_reference_table.py` line 559 cites a stale "ADR-02.05 REQ-004" comment.

## Reason for Change
- Both checkers are Blocking CI gates whose findings are currently mis-reported, duplicated, mis-routed, or dropped; the defects are latent only because the current registry happens to pass clean (fixture runs prove otherwise). Five registry rows contradict the governing ADRs and the Resolution Matrix, so the Canonical Source contract is unenforced for those targets.

## Implementation Intent
- Fix the checkers first (code + regression tests), keeping the GV-019/GV-020/GV-021 Blocking semantics unchanged; then fix the registry rows so the (already green) clean-run baseline stays green while the fixture-based failing cases now fail with the exact expected findings; then fix docs and comments. Governance owner-list changes are prepared as proposals only and applied after maintainer approval. Current-Specification-Only: ADR bodies and governance docs are the specification; the registry and checkers are aligned to them, never the reverse.

## Requirements
- `REQ-001`: A defect class (non-Accepted ADR reference) must have exactly one severity across both checkers, matching the gate definitions (registry error, conflicts warning) without contradicting itself inside `validate_all()`.
- `REQ-002`: Default registry resolution and source-path existence checks must be anchored to the repository root (derived from the tool file location), not the current working directory; running from any cwd reports identical findings.
- `REQ-003`: Unknown CLI options must fail with a usage error (exit code 2), not be silently accepted.
- `REQ-004`: Dead code in `check_canonical_source_registry.py` (unused public helpers, ~98 vulture items) must be removed or exercised by tests, without changing checker output.
- `REQ-005`: `--diff` output and error lists must be deterministically ordered (byte-identical across repeated runs).
- `REQ-006`: `_run_detection_functions` must run on the main path of `detect_all_conflicts`, not only in the fallback/except path.
- `REQ-007`: `_wrap_validation_errors` must report every validation error (missing source path, invalid claim type, Draft/Proposed normative source) as a blocking `CANONICAL-C0xx` finding regardless of whether the error text contains the entry's `decision_target`.
- `REQ-008`: One validation error must produce exactly one finding (deduplicated across matching entries; entry list retained in the finding detail).
- `REQ-009`: Every finding code must be unique; the version error must move from the reused `CANONICAL-008` to an unused code (target `CANONICAL-009`, checked against adrchk011 GV renumbering first).
- `REQ-010`: `classify_finding` must route `CANONICAL-C0xx` codes to CANONICAL_CONFLICT and `CANONICAL-W0xx` codes to their routing-table destination; the duplicate `return conflicts` (lines 944/946) must be removed.
- `REQ-011`: Routing tests must exercise the real `CANONICAL-C0xx`/`CANONICAL-W0xx` code prefixes, not the synthetic `CANONICAL-C001`-style literals only.
- `REQ-012`: Dead code in `check_canonical_source_conflicts.py` (~47 vulture items) must be removed or exercised by tests.
- `REQ-013`: `--registry` help text must state the actual default `config/documentation_canonical_sources.toml`.
- `REQ-014`: `eventbus.persistence-schema.bootstrap-ddl` `source_paths` must name `scripts/eventbus/schema.sql` (the DDL definition per the DB docs), not `scripts/db/schema_sql.py`.
- `REQ-015`: `agent.posture-failure-handling` notes must match ADR-004 (no environment-specific fail-open policy).
- `REQ-016`: The `governance.policy` row (claim type / source paths) must agree with the Resolution Matrix row that assigns `documentation-metadata` to the documentation-metadata document.
- `REQ-017`: Prepare (do not merge) a Resolution Matrix proposal adding ADR-017 and ADR-004 as owners of `mcp.component-mandatoriness`, citing ADR-004 Group 3 item 13; the registry row stays unchanged until maintainer approval.
- `REQ-018`: `governance_02` must state the correct number of optional front matter fields (`status` and `class` — two).
- `REQ-019`: `overview.architecture-overview` `claim_type` must match the claim kind actually made about that decision target.
- `REQ-020`: `config/adr_authority.toml` must drop the history-style "Transcribed 2026-10-30" comment (the toml is the hand-maintained input model of `tools/generate_adr_authority.py`; guarded blocks are unaffected).
- `REQ-021`: `tools/generate_reference_table.py` line 559 must cite the current normative ADR/requirement instead of the stale "ADR-02.05 REQ-004" comment.
- `REQ-022`: No generated artifact (`registry/manifests/*.yaml`, guarded blocks in `docs/10_adr/adr_01_index.md`) may be hand-edited; drift gates (`tools/generate_reference_table.py --check`, `tools/generate_adr_authority.py --check`) must pass.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed
2026-11-19: `check_workitem_structure.py` and `audit_plan_target_paths.py` clean; every row
`Verified` against current source — see `rules/workflow-lifecycle.md`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/check_canonical_source_registry.py | checker fix | severity consistency, cwd-anchored paths, CLI strictness, dead code, deterministic output | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; AC-01–AC-05 | `validate()` error + `find_non_accepted_adr()` warning duplication; fixture run 3 errors exit 1; `/tmp/opencode` run 20 bogus errors; vulture 98 items | tests/tools/test_check_canonical_source_registry.py | Verified |
| tools/check_canonical_source_conflicts.py | checker fix | detector main-path, wrapper gate, dedup, code numbering, routing, dead code, help text | REQ-006–REQ-013; AC-06–AC-11 | `_wrap_validation_errors` gate drops errors; duplicate `CANONICAL-007` fixture findings; `CANONICAL-008` reuse; `return conflicts` lines 944/946; help default mismatch; vulture 47 items | tests/tools/test_check_canonical_source_conflicts.py; tests/tools/test_check_canonical_source_conflicts_routing.py | Verified |
| config/documentation_canonical_sources.toml | config fix | align 5 defective rows with the ADR/governance specification | REQ-014, REQ-015, REQ-016, REQ-019; AC-12 | lines 10–15, 18–22, 31–36, 66–71, 73–78 vs docs db_02/db_03/db_08, ADR-004, Resolution Matrix lines 134–135 | tests/tools/test_check_canonical_source_registry.py; tests/tools/test_check_canonical_source_conflicts.py | Verified |
| config/adr_authority.toml | comment cleanup | remove history-style "Transcribed 2026-10-30" note | REQ-020; AC-15 | line 9; generator docstring confirms the toml is the hand-maintained input model | N/A: comment-only change; drift gates `generate_adr_authority.py --check`, `check_adr_authority.py` | Verified |
| docs/00_governance/governance_01_documentation-policy.md | governance proposal (apply only after approval) | Resolution Matrix owner-list change for `mcp.component-mandatoriness` | REQ-017; AC-13 | Matrix lines 134–135 vs registry row and ADR-004 Group 3 item 13 | N/A: proposal pending approval (UNK-02) | Verified |
| docs/00_governance/governance_02_documentation-metadata.md | doc fix | correct optional-field miscount | REQ-018; AC-14 | line 49 "one optional field" vs lines 80–81 listing `status` and `class` | N/A: doc gates via CI lint | Verified |
| tools/generate_reference_table.py | comment cleanup | replace stale "ADR-02.05 REQ-004" comment | REQ-021, REQ-022; AC-15, AC-16 | line 559 | N/A: comment-only change; drift gate `generate_reference_table.py --check` | Verified |
| tests/tools/test_check_canonical_source_registry.py | test update | fixture regression tests for REQ-001–REQ-005 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; AC-01–AC-05 | existing 273-line file, 77 tests passed baseline | — | Verified |
| tests/tools/test_check_canonical_source_conflicts.py | test update | fixture regression tests for REQ-006–REQ-009, REQ-012, REQ-013 | REQ-006–REQ-009, REQ-012, REQ-013; AC-06–AC-11 | existing 525-line file, baseline passing | — | Verified |
| tests/tools/test_check_canonical_source_conflicts_routing.py | test update | route the real canonical code prefixes | REQ-010, REQ-011; AC-10 | existing 100-line file routes only synthetic `CANONICAL-C001` codes | — | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | GV-019/GV-020/GV-021 gate wording and Blocking semantics that must be preserved | REQ-006–REQ-013 |
| tools/_validation_gate_defs.py | Gate registration for the two checkers; Blocking status source | REQ-001–REQ-013 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Group 1 item 1 and Group 3 item 13 (normative basis for REQ-015/REQ-017) | REQ-015, REQ-017 |
| docs/41_db/db_02_architecture_and_schema-schema-reference.md | Names Decision Target `eventbus.persistence-schema.bootstrap-ddl` and `scripts/eventbus/schema.sql` | REQ-014 |
| scripts/eventbus/schema.sql | Existence check for the new source path (2892 B, exists) | REQ-014 |
| tools/generate_adr_authority.py | Confirms `config/adr_authority.toml` is the hand-maintained input model; guarded-block drift gate | REQ-020, REQ-022 |
| tools/check_adr_authority.py | Validation of the authority model after the comment cleanup | REQ-020 |
| tools/check_canonical_document_prose.py | Sibling consumer of the same registry config; must stay green after config edits | REQ-014–REQ-016, REQ-019 |
| tools/check_module_size_tools_baseline.txt | Records the oversized-checker baseline; module split stays out of scope | Out-of-Scope (module split) |

## Acceptance Criteria
- `AC-01` (REQ-001): a fixture with a non-Accepted ADR reference yields exactly one registry error and, on the conflicts side, exactly one warning finding — no self-contradicting severity inside `validate_all()`.
- `AC-02` (REQ-002): both checkers run from the repo root and from `/tmp/opencode` (absolute `--registry`) and report identical findings; the default registry resolves from any cwd.
- `AC-03` (REQ-003): `--unknown-option` exits 2 with a usage message.
- `AC-04` (REQ-004, REQ-012): no unused method or module-level constant flagged at ≥90 % confidence by vulture remains in either checker, and the three checker test files pass unchanged in behavior otherwise.
- `AC-05` (REQ-005): two consecutive `--diff` runs produce byte-identical stdout.
- `AC-06` (REQ-006): on the fixture registry, semantic findings appear without triggering the fallback path (main-path execution proven by test).
- `AC-07` (REQ-007): the fixture (missing source path + invalid claim type + Draft ADR source) produces all findings as blocking `CANONICAL-C0xx`, including the previously dropped missing-path error.
- `AC-08` (REQ-008): the previously duplicated finding set yields exactly one `CANONICAL-C006`-class finding for one wrapped error.
- `AC-09` (REQ-009): no finding code appears twice in any run; the version error carries the new unique code (`CANONICAL-009`, subject to the adrchk011 collision check).
- `AC-10` (REQ-010, REQ-011): `classify_finding` routes real `CANONICAL-C0xx`/`CANONICAL-W0xx` codes to their routing-table destinations; routing tests parametrized on the real prefixes pass; only one `return conflicts` path remains.
- `AC-11` (REQ-013): `--help` prints `config/documentation_canonical_sources.toml` as the default.
- `AC-12` (REQ-014, REQ-015, REQ-016, REQ-019): after the config fixes, both checkers and `check_canonical_document_prose.py` exit 0 on the repo registry, and the four fixture-confirmed conflicts no longer appear.
- `AC-13` (REQ-017): the owner-change proposal exists as a prepared Matrix edit with citations, is not merged without approval, and the registry row is unchanged.
- `AC-14` (REQ-018): `governance_02` states two optional fields consistently in both places.
- `AC-15` (REQ-020, REQ-021): neither file contains a history-style or stale reference comment; `generate_adr_authority.py --check` and `generate_reference_table.py --check` pass.
- `AC-16` (REQ-022): no generated file is hand-edited in any phase; drift gates pass; full suite passes (baseline 12912 passed, 7 skipped) and diff-cover ≥ 90 %.

## Tests
- `T01` (REQ-001): registry fixture — non-Accepted ADR reference reported once, error severity; conflicts warning reported once.
- `T02` (REQ-002): cwd-independence test — same findings from repo root and from a foreign cwd with absolute `--registry` (fixture evidence: 20 bogus errors before fix).
- `T03` (REQ-003): unknown option → exit 2.
- `T04` (REQ-004, REQ-012): vulture ≥90 % confidence count is 0 for both files after removal.
- `T05` (REQ-005): repeated `--diff` byte-identical.
- `T06` (REQ-006): fixture findings produced on the main path (no exception raised).
- `T07` (REQ-007): missing-source-path, invalid-claim-type, and Draft-source errors all appear as blocking findings.
- `T08` (REQ-008): one wrapped error → exactly one finding (no per-entry duplication).
- `T09` (REQ-009): code-uniqueness assertion over all fixture findings; version error = `CANONICAL-009`.
- `T10` (REQ-010, REQ-011): routing parametrization extended to real `CANONICAL-C0xx`/`CANONICAL-W0xx` codes.
- `T11` (REQ-013): help-text default assertion.
- `T12` (REQ-014–REQ-016, REQ-019): corrected registry passes both checkers and the prose checker with exit 0; the fixture registry fails with the exact expected finding set.
- `T13` (REQ-018): doc text review of the two optional-field statements (CI lint doc gates).
- `T14` (REQ-020, REQ-021, REQ-022): `generate_adr_authority.py --check`, `generate_reference_table.py --check`, `check_adr_authority.py` all exit 0.

## Documentation Impact
- `docs/00_governance/governance_01_documentation-policy.md` (Resolution Matrix, REQ-017) and `docs/00_governance/governance_02_documentation-metadata.md` (REQ-018) are direct targets of this Plan and are edited in place (Matrix edit gated on approval). `docs/00_governance/governance_04_documentation-checks.md` needs no update: the fixed checker behavior is made to match its existing GV-019/GV-020/GV-021 wording (verified at Step 2). No other doc requires updating.

## Assumptions
- Current-Specification-Only: ADR bodies and the Resolution Matrix are the specification; registry rows and checker behavior are corrected toward them, never the reverse.
- `config/adr_authority.toml` is the hand-maintained input model consumed by `tools/generate_adr_authority.py` (confirmed by the generator docstring), so a comment-only edit does not require regenerating the guarded blocks — the `--check` drift gate still validates them.
- GV-019/GV-020/GV-021 Blocking semantics are preserved; fixes change what is reported, not how severities gate CI.
- The fixture registry/ADR pair used for baseline evidence (`/tmp/opencode/fixture_registry.toml`, `/tmp/opencode/fixture_adr.md`) will be recreated as pytest fixtures inside the test files, not committed as standalone files.
- `tools/` and `config/` are rsynced by the deploy flow; no new deploy copy lines are required.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Overlap with the still-open adrchk011 issue (ADR approval governance): its future plan may propose the same Matrix changes and GV-code renumbering | adrchk011 has no Plan yet | Process adrchk011 before applying REQ-017; check its plan before allocating `CANONICAL-009` | False |
| UNK-02 | Maintainer approval for adding ADR-017/ADR-004 to the `mcp.component-mandatoriness` owners | No approval record exists | REQ-017 is proposal-only; merge requires an explicit owner decision recorded in the Blocker Log | False |
| UNK-03 | Exact dead-code removal list (vulture 98 + 47 items includes helpers referenced only by tests) | Per-helper usage audit not yet done | Enumerate removal candidates in the implementation procedure; keep anything a passing test imports | False |
| UNK-04 | Final claim-type value for `overview.architecture-overview` and the exact `governance.policy` row correction (claim_type vs source path) | Matrix semantics require a line-by-line reading during implementation | Decide in the implementation procedure against the Matrix rows; fixture test pins the outcome | False |
| UNK-05 | Module-split policy for the two oversized checkers (41349 B / 36416 B, baselined in `tools/check_module_size_tools_baseline.txt`) | No repo decision recorded (issue Unresolved Question 2) | Out-of-scope here; file a follow-up refactoring issue after the fixes land | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/check_canonical_source_registry.py | edit | GV-020 gate; registry tests; governance_04 wording consumers | 1 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| tools/check_canonical_source_conflicts.py | edit | GV-019/GV-021 gates; two conflicts test files; CI lint job | 0 | Masao SUGIMOTO (sole author) | not applicable (rsynced) |
| config/documentation_canonical_sources.toml | edit | both checkers; `check_canonical_document_prose.py`; reference-table manifests | 4 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| config/adr_authority.toml | edit | `generate_adr_authority.py`, `check_adr_authority.py`, `adr_01_index.md` guarded blocks | 6 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| docs/00_governance/governance_01_documentation-policy.md | edit (approval-gated) | Resolution Matrix consumers: both checkers, adr_authority docs | 4 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| docs/00_governance/governance_02_documentation-metadata.md | edit | doc lint gates only | 4 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| tools/generate_reference_table.py | edit (comment-only) | `registry/manifests/*.yaml` drift gate consumers | 6 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| tests/tools/test_check_canonical_source_registry.py | edit | GV-020 regression coverage | 0 | Masao Sugimoto (sole author) | not applicable (rsynced) |
| tests/tools/test_check_canonical_source_conflicts.py | edit | GV-019/GV-021 regression coverage | 0 | Masao SUGIMOTO (sole author) | not applicable (rsynced) |
| tests/tools/test_check_canonical_source_conflicts_routing.py | edit | routing regression coverage | 0 | Masao SUGIMOTO (sole author) | not applicable (rsynced) |

## Design
- Step 5 (Path B) analysis results:
  - Architecture: `lint-imports` reports 6 contracts kept, 0 broken — the checkers live outside the layered `scripts/` package contract and import only stdlib + `tomllib`/test-support. Consumer scan: the two checkers are consumed by `tools/_validation_gate_defs.py` (GV-020 at the registry tool; GV-019/GV-021 at the conflicts tool), the three `tests/tools/` files, `docs/00_governance/governance_04_documentation-checks.md`, and CI. The registry config is additionally consumed by `tools/check_canonical_document_prose.py` (same `DEFAULT_REGISTRY_PATH`). Fixing the checkers therefore has no import-cycle risk; the shared constant to fix is the two tools' own path anchoring.
  - Complexity/dead code: radon flags `_wrap_validation_errors` at D(22) and `RegistryEntry.validate` C(17), `CanonicalSourceRegistry.diff` C(12); vulture reports 98 (registry) + 47 (conflicts) unused items. Bandit: no issues. The wrapper fix (REQ-007/REQ-008) also reduces the D-graded function by replacing the substring gate with per-entry error iteration.
  - Historical: both checkers have near-zero 30-day churn (0 / 1 commits) and a single author; the registry config and governance docs churn 4–6 commits in 30 days — config/doc edits are the active surface, the checker defects are dormant code.
  - Operational baseline: full suite 12912 passed / 7 skipped; diff-cover over the current working diff reports no coverage-relevant lines; both checkers exit 0 on the repo registry today, so the fixes must keep the clean run green while making fixtures fail exactly as specified.
- Severity model: severities come from the gate definitions, not per-detector choice — the registry tool owns error-level conformance (GV-020), the conflicts tool owns blocking conflict findings (GV-019/GV-021); `find_non_accepted_adr()` becomes a warning-only detector consistent with that split.
- Path anchoring: derive repo root from `Path(__file__).resolve().parent.parent` instead of `Path.cwd()` in both tools (the sibling `check_canonical_document_prose.py` already uses a fixed relative default).
- Deduplication key: `(code, decision_target)` with the affected entry list attached to the finding, so per-entry wrapping collapses to one finding without losing detail.
- Governance split: registry/config/docs corrections that the spec already fixes are applied directly; the owner-list change the spec does not yet authorize is a prepared proposal (REQ-017) blocked on approval (UNK-02).

## Implementation steps
1. **Phase 1: Registry checker fixes**
   - [ ] Add failing fixture tests for REQ-001–REQ-005 to `tests/tools/test_check_canonical_source_registry.py` (REQ-001–REQ-005; tests/tools/test_check_canonical_source_registry.py)
   - [ ] Single severity source for non-Accepted ADR references in `tools/check_canonical_source_registry.py` (REQ-001; tools/check_canonical_source_registry.py)
   - [ ] Repo-root anchoring of `DEFAULT_REGISTRY_PATH` and `repo_root` in `tools/check_canonical_source_registry.py` (REQ-002; tools/check_canonical_source_registry.py)
   - [ ] Strict unknown-option handling (exit 2) and deterministic `--diff`/error ordering in `tools/check_canonical_source_registry.py` (REQ-003, REQ-005; tools/check_canonical_source_registry.py)
   - [ ] Dead-code removal per the audited list in `tools/check_canonical_source_registry.py` (REQ-004; tools/check_canonical_source_registry.py)
2. **Phase 2: Conflicts checker fixes**
   - [ ] Add failing fixture tests for REQ-006–REQ-009, REQ-012, REQ-013 to `tests/tools/test_check_canonical_source_conflicts.py` (REQ-006–REQ-009, REQ-012, REQ-013; tests/tools/test_check_canonical_source_conflicts.py)
   - [ ] Run `_run_detection_functions` on the main path in `tools/check_canonical_source_conflicts.py` (REQ-006; tools/check_canonical_source_conflicts.py)
   - [ ] Replace the `_wrap_validation_errors` substring gate with per-entry reporting and `(code, decision_target)` deduplication in `tools/check_canonical_source_conflicts.py` (REQ-007, REQ-008; tools/check_canonical_source_conflicts.py)
   - [ ] Reunique finding codes — version error moves to the `CANONICAL-009` slot after the adrchk011 collision check (REQ-009; tools/check_canonical_source_conflicts.py)
   - [ ] Route real `CANONICAL-C0xx`/`CANONICAL-W0xx` prefixes in `classify_finding`, remove the duplicate `return conflicts`, fix `--registry` help text in `tools/check_canonical_source_conflicts.py` (REQ-010, REQ-013; tools/check_canonical_source_conflicts.py)
   - [ ] Extend routing parametrization to real code prefixes in `tests/tools/test_check_canonical_source_conflicts_routing.py` (REQ-011; tests/tools/test_check_canonical_source_conflicts_routing.py)
   - [ ] Dead-code removal per the audited list in `tools/check_canonical_source_conflicts.py` (REQ-012; tools/check_canonical_source_conflicts.py)
3. **Phase 3: Registry config fixes and governance proposal**
   - [ ] Fix `eventbus.persistence-schema.bootstrap-ddl` source path, `agent.posture-failure-handling` note, `governance.policy` row, and `overview.architecture-overview` claim type in `config/documentation_canonical_sources.toml` (REQ-014–REQ-016, REQ-019; config/documentation_canonical_sources.toml)
   - [ ] Prepare (do not merge) the Resolution Matrix owner change for `mcp.component-mandatoriness` in `docs/00_governance/governance_01_documentation-policy.md`, citing ADR-004 Group 3 item 13 and ADR-017; record the approval gate in the Blocker Log (REQ-017; docs/00_governance/governance_01_documentation-policy.md)
   - [ ] Remove the "Transcribed 2026-10-30" note from `config/adr_authority.toml` (REQ-020; config/adr_authority.toml)
4. **Phase 4: Governance documentation fix**
   - [ ] Correct the optional-field count in `docs/00_governance/governance_02_documentation-metadata.md` to two (`status`, `class`) (REQ-018; docs/00_governance/governance_02_documentation-metadata.md)
5. **Phase 5: Comment cleanup and verification**
   - [ ] Replace the stale "ADR-02.05 REQ-004" comment in `tools/generate_reference_table.py` with the current normative reference (REQ-021; tools/generate_reference_table.py)
   - [ ] Run drift gates (`tools/generate_reference_table.py --check`, `tools/generate_adr_authority.py --check`, `tools/check_adr_authority.py`), both checkers, the prose checker, the three checker test files, the full suite, and diff-cover; confirm no generated artifact was hand-edited (REQ-022; tools/generate_reference_table.py)

### Release units
N/A: no release unit (every phase passes validation alone)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_canonical_source_registry.py | Unit fixture tests + cwd integration run | `uv run pytest tests/tools/test_check_canonical_source_registry.py -v`; run from repo root and from `/tmp/opencode` | Fixture findings exact (AC-01–AC-05); cwd-independent identical findings |
| tools/check_canonical_source_conflicts.py | Unit fixture tests | `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v` | Fixture findings deduplicated, blocking, uniquely coded, correctly routed (AC-06–AC-11) |
| config/documentation_canonical_sources.toml | Integration: three consumers over corrected config | `uv run python tools/check_canonical_source_registry.py`; `uv run python tools/check_canonical_source_conflicts.py`; `uv run python tools/check_canonical_document_prose.py` | All exit 0 (AC-12) |
| docs/00_governance/governance_01_documentation-policy.md; docs/00_governance/governance_02_documentation-metadata.md | Doc review + CI lint gates | CI `lint` doc gates; manual Matrix review | AC-13 proposal prepared, AC-14 count fixed |
| config/adr_authority.toml; tools/generate_reference_table.py | Drift gates | `uv run python tools/check_adr_authority.py`; `uv run python tools/generate_adr_authority.py --check`; `uv run python tools/generate_reference_table.py --check` | All exit 0; guarded blocks unchanged (AC-15, AC-16) |
| Whole repo | Full suite + diff-scoped coverage + static analysis | `uv run pytest tests/ -q`; `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"` + `uv run coverage xml` + `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; `uv run vulture tools/check_canonical_source_registry.py tools/check_canonical_source_conflicts.py --min-confidence 90`; `uv run radon cc -n C` on both checkers; `uv run bandit -q -r tools/check_canonical_source_registry.py tools/check_canonical_source_conflicts.py -c pyproject.toml`; `uv run lint-imports` | Suite green (12912+ baseline), diff-cover ≥ 90 %, vulture 0, no C-or-worse functions in touched code, bandit clean, 6 contracts kept |

## Risks
- **Risk**: severity-consistency and main-path-detector fixes surface new findings on the currently clean registry and break CI → **Mitigation**: main-path detectors already pre-run clean (0 blocking findings today); run both checkers after every phase and keep AC-12 as the green-registry gate.
- **Risk**: deduplication hides genuinely repeated conflicts across different entries → **Mitigation**: dedup key is `(code, decision_target)` with the affected entry list preserved in the finding detail (Design).
- **Risk**: dead-code removal breaks helpers imported by the existing 77-test baseline → **Mitigation**: run the three checker test files after each removal batch; keep anything a passing test imports (UNK-03).
- **Risk**: the REQ-017 proposal is rejected or conflicts with adrchk011's later plan → **Mitigation**: registry row stays untouched until approval; dependency bullet sequences phase 3 behind adrchk011; decision recorded in the Blocker Log.
- **Risk**: `CANONICAL-009` collides with a future adrchk011 GV renumbering → **Mitigation**: collision check before allocation (UNK-01, REQ-009).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Registry checker fixes | Pending | — | — | |
| 2 | Phase 2: Conflicts checker fixes | Pending | — | — | |
| 3 | Phase 3: Registry config fixes and governance proposal | Pending | — | — | |
| 4 | Phase 4: Governance documentation fix | Pending | — | — | |
| 5 | Phase 5: Comment cleanup and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | REQ-017 owner change requires maintainer approval before merge (UNK-02) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-19 11:58:42
- **Related target files**: tools/check_canonical_source_registry.py, tools/check_canonical_source_conflicts.py, config/documentation_canonical_sources.toml, config/adr_authority.toml, docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_02_documentation-metadata.md, tools/generate_reference_table.py, tests/tools/test_check_canonical_source_registry.py, tests/tools/test_check_canonical_source_conflicts.py, tests/tools/test_check_canonical_source_conflicts_routing.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue section 2 (registry checker) + fixture run (3 errors, duplicated non-Accepted ADR) | tools/check_canonical_source_registry.py | Phase 1 | AC-01 | T01 | Confirmed by repository evidence |
| REQ-001 | Issue section 2 (registry checker) + fixture run (3 errors, duplicated non-Accepted ADR) | tests/tools/test_check_canonical_source_registry.py | Phase 1 | AC-01 | T01 | Derived from confirmed evidence |
| REQ-002 | Fixture run from /tmp/opencode (20 bogus errors; "Registry file not found") | tools/check_canonical_source_registry.py | Phase 1 | AC-02 | T02 | Confirmed by repository evidence |
| REQ-002 | Fixture run from /tmp/opencode (20 bogus errors; "Registry file not found") | tests/tools/test_check_canonical_source_registry.py | Phase 1 | AC-02 | T02 | Derived from confirmed evidence |
| REQ-003 | Issue section 2 + `validate_all` unused-helper evidence | tools/check_canonical_source_registry.py | Phase 1 | AC-03 | T03 | Confirmed by repository evidence |
| REQ-003 | Issue section 2 + `validate_all` unused-helper evidence | tests/tools/test_check_canonical_source_registry.py | Phase 1 | AC-03 | T03 | Derived from confirmed evidence |
| REQ-004 | vulture 98 items (min-confidence 90) | tools/check_canonical_source_registry.py | Phase 1 | AC-04 | T04 | Confirmed by repository evidence |
| REQ-004 | vulture 98 items (min-confidence 90) | tests/tools/test_check_canonical_source_registry.py | Phase 1 | AC-04 | T04 | Derived from confirmed evidence |
| REQ-005 | Issue section 2 (`--diff` ordering) | tools/check_canonical_source_registry.py | Phase 1 | AC-05 | T05 | Explicit in issue |
| REQ-006 | `detect_all_conflicts` fallback-only `_run_detection_functions`; fixture main-path gap | tools/check_canonical_source_conflicts.py | Phase 2 | AC-06 | T06 | Confirmed by repository evidence |
| REQ-006 | `detect_all_conflicts` fallback-only `_run_detection_functions`; fixture main-path gap | tests/tools/test_check_canonical_source_conflicts.py | Phase 2 | AC-06 | T06 | Derived from confirmed evidence |
| REQ-007 | `_wrap_validation_errors` gate drops missing-path error (fixture) | tools/check_canonical_source_conflicts.py | Phase 2 | AC-07 | T07 | Confirmed by repository evidence |
| REQ-007 | `_wrap_validation_errors` gate drops missing-path error (fixture) | tests/tools/test_check_canonical_source_conflicts.py | Phase 2 | AC-07 | T07 | Derived from confirmed evidence |
| REQ-008 | Fixture: two identical CANONICAL-007 findings | tools/check_canonical_source_conflicts.py | Phase 2 | AC-08 | T08 | Confirmed by repository evidence |
| REQ-008 | Fixture: two identical CANONICAL-007 findings | tests/tools/test_check_canonical_source_conflicts.py | Phase 2 | AC-08 | T08 | Derived from confirmed evidence |
| REQ-009 | CANONICAL-008 reused (multiple-FR detector + version error) | tools/check_canonical_source_conflicts.py | Phase 2 | AC-09 | T09 | Confirmed by repository evidence |
| REQ-009 | CANONICAL-008 reused (multiple-FR detector + version error) | tests/tools/test_check_canonical_source_conflicts.py | Phase 2 | AC-09 | T09 | Derived from confirmed evidence |
| REQ-010 | `classify_finding` prefix mismatch; duplicate `return conflicts` lines 944/946 | tools/check_canonical_source_conflicts.py | Phase 2 | AC-10 | T10 | Confirmed by repository evidence |
| REQ-011 | Routing tests use synthetic CANONICAL-C001 codes only | tests/tools/test_check_canonical_source_conflicts_routing.py | Phase 2 | AC-10 | T10 | Confirmed by repository evidence |
| REQ-012 | vulture 47 items | tools/check_canonical_source_conflicts.py | Phase 2 | AC-04 | T04 | Confirmed by repository evidence |
| REQ-012 | vulture 47 items | tests/tools/test_check_canonical_source_conflicts.py | Phase 2 | AC-04 | T04 | Derived from confirmed evidence |
| REQ-013 | `--registry` help names wrong default file | tools/check_canonical_source_conflicts.py | Phase 2 | AC-11 | T11 | Confirmed by repository evidence |
| REQ-014 | Registry lines 10–15 vs docs db_02/db_03/db_08 (`scripts/eventbus/schema.sql`, exists 2892 B) | config/documentation_canonical_sources.toml | Phase 3 | AC-12 | T12 | Confirmed by repository evidence |
| REQ-015 | Registry lines 73–78 vs ADR-004 Group 1 item 1 | config/documentation_canonical_sources.toml | Phase 3 | AC-12 | T12 | Confirmed by repository evidence |
| REQ-016 | Registry lines 31–36 vs Resolution Matrix lines 134–135 | config/documentation_canonical_sources.toml | Phase 3 | AC-12 | T12 | Confirmed by repository evidence |
| REQ-017 | Registry lines 66–71 vs Matrix owners; ADR-004 Group 3 item 13 | docs/00_governance/governance_01_documentation-policy.md | Phase 3 | AC-13 | N/A: proposal pending maintainer approval (UNK-02) | Needs confirmation |
| REQ-018 | governance_02 line 49 vs lines 80–81 | docs/00_governance/governance_02_documentation-metadata.md | Phase 4 | AC-14 | T13 | Confirmed by repository evidence |
| REQ-019 | Registry lines 18–22 claim_type inconsistency | config/documentation_canonical_sources.toml | Phase 3 | AC-12 | T12 | Confirmed by repository evidence |
| REQ-020 | adr_authority.toml line 9 "Transcribed" note | config/adr_authority.toml | Phase 3 | AC-15 | T14 | Confirmed by repository evidence |
| REQ-021 | generate_reference_table.py line 559 stale comment | tools/generate_reference_table.py | Phase 5 | AC-15 | T14 | Confirmed by repository evidence |
| REQ-022 | Generated-file policy (registry/manifests, guarded blocks) | tools/generate_reference_table.py | Phase 5 | AC-16 | T14 | Explicit in issue |
