## Goal

- Fix the checker defects in `tools/check_canonical_source_conflicts.py` (Blocking gates GV-019/GV-021) per the Plan: `REQ-006` main-path detectors, `REQ-007` wrapper gate removal, `REQ-008` one-finding-per-error dedup, `REQ-009` unique codes, `REQ-010` routing and duplicate-return cleanup, `REQ-012` dead code, `REQ-013` help text.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the seven fixes above, applied to the target file only.
- Out of scope here: GV-0xx gate renumbering (adrchk011 owns it); GV-019/GV-020/GV-021 Blocking semantics stay unchanged (Plan Assumptions).

## Assumptions

- Clean baseline: the tool exits 0 on the repo registry; fixes keep it green while fixtures fail exactly as specified (`AC-12`).
- Fixture registries/ADRs are inlined as pytest fixtures (Plan Assumptions); failing fixture tests are written first in the documents for seq 08/09.
- `REQ-009` code target: `CANONICAL-012` (new).
- The pin for the existing code is `tests/tools/test_check_canonical_source_conflicts.py` lines 446–463.
- `CANONICAL-009` is already used by the empty-area detector in `tools/check_canonical_source_conflicts.py` lines 637 and 823. The adrchk011 collision check (UNK-01) still precedes allocation.

## Design decisions

- Main-path execution (`REQ-006`): in `detect_all_conflicts` (lines 911–946) always run `_run_detection_functions` on the loaded entries — the validator path currently wraps only validation errors (lines 927–936) and the nine semantic detectors run only in the fallback/except paths (lines 937–942).
- Wrapper attribution (`REQ-007`/`REQ-008`): replace the substring gate (lines 739–743) with per-entry attribution of the registry validation errors; emit exactly one finding per `(code, decision_target)` with the matching entry list preserved in the finding detail (Plan Design "Deduplication key"). Registry error texts that do not name a `decision_target` (missing source path, unsupported version) must still produce findings — the current gate drops them.
- Wrapper restructure (2026-11-19 verification): the current function is radon D(22); the rework is data-driven — a frozen `_ValidationRule` table (substrings → code/severity/blocking) matching the registry tool's real error strings, a target regex (`targeting|decision_target='…'`), a source-path match fallback, then a registry-wide single finding when nothing matches. New mapping: empty decision_target→002, empty claim_type→003, unrecognized claim_type→004 (HIGH/BLOCKING), empty source_paths→005, multiple source_paths→006, duplicate entry→007, empty area→009, missing Status section→010, non-Accepted status→011 (MEDIUM/NON_BLOCKING per `AC-01`, see UNK-12), version→012 (`REQ-009`), "source path does not exist"/"cannot read ADR file"→`CANONICAL-013` (new extension beyond the Plan's `REQ-009` code list, recorded in the Final Report), unmatched fallback→001 HIGH/BLOCKING (`REQ-007`: no error may be dropped).
- Severity mapping per the gate definitions (Plan Design "Severity model"): GV-021 classes — missing/invalid source (`013`), unrecognized claim type (`004`, lines 770–786) — are wrapped as blocking HIGH findings. Resolved 2026-11-19 (UNK-12): the only Draft/Proposed-ADR class the registry tool actually reports is the `ADR-sourced entry has non-Accepted status` error, which `AC-01` pins as "exactly one warning finding" on the conflicts side, so `011` (lines 880–890) stays MEDIUM/NON_BLOCKING; the fixture tests pin this outcome. `006`/`010` stay MEDIUM/NON_BLOCKING. The same severity fix applies to the `detect_unrecognized_claim_type` detector (lines 558–559) and the pin at test lines 381–383, updated in the same commit citing `AC-07`.
- Routing (`REQ-010`): `classify_finding` (lines 965–995) currently matches only `CANONICAL-C`/`CANONICAL-W` prefixes, so the real blocking family `CANONICAL-NNN` falls through to KNOWN_ISSUE (line 995); route the numeric family per severity (`HIGH`/`MEDIUM`→CANONICAL_CONFLICT, `LOW`→DOC_CORRECTION), keep `CANONICAL-W-NN` → DOC_CORRECTION, drop the synthetic `CANONICAL-C` branch.
- Dead-code verification (2026-11-19): `vulture --min-confidence 90` returns 1 item (the unreachable `return conflicts` at line 946), not "46 items + 3 imports" — that figure corresponds to `--min-confidence 60` (49 lines: `Severity.from_name`/`from_blocking`, `BlockingStatus.from_severity`, 11 unused `CLAIM_TYPE_*`, 12 `AUTHORITY_*`, `BLOCKING_SEVERITIES`/`NON_BLOCKING_SEVERITIES`/`SEVERITY_THRESHOLD_*`, the 7 `CanonicalConflict` 12-field-template attributes — a vulture false positive (`to_dict`/`__str__` read them via `getattr`) — 6 uncalled detectors, `classify_finding`, `detect_duplicate_active_records`, the unreachable line). Implementation outcome: the 6 entry-level detectors (`detect_empty_decision_target`/`detect_empty_claim_type`/`detect_unrecognized_claim_type`/`detect_empty_source_paths`/`detect_multiple_source_paths_violation`/`detect_empty_area`) were WIRED INTO `_run_detection_functions` instead of kept dead (fallback-path completeness; main-path duplicates merge via the dedup key); UNK-03 keeps reduced to `classify_finding` and `detect_duplicate_active_records`/`_build_key` (imported by passing tests); `CLAIM_TYPE_FUNCTIONAL_REQUIREMENT`/`CLAIM_TYPE_DOCUMENTATION_METADATA` kept (used at lines 435/470/473).
- `CANONICAL-012` collision check (UNK-01, step 3 blocker): RESOLVED 2026-11-19 — the repo allocates only 001–011; adrchk011 (issues/done + plans/done) contains zero `CANONICAL-` references.
- Fixture repo-root handling: `detect_all_conflicts` keeps its signature (no public API change); the tmp fixtures monkeypatch `tools.check_canonical_source_registry.REPO_ROOT` so `validate_registry_schema`'s default resolves entry paths against `tmp_path`. Clean repo-registry runs never use the patch. The 19 repo rows contain no `functional-requirement` claim type and no W-05 trigger terms, so main-path execution keeps the repo run finding-free (exit 0).

## Alternatives considered

- Map blocking findings to `Severity.HIGH` only inside `classify_finding` while leaving wrapper severities as-is — rejected: severity duplication (`REQ-001` class) would persist between wrapper output and routing.

## Implementation
### Target file
`tools/check_canonical_source_conflicts.py`
### Procedure
1. Restructure `detect_all_conflicts` so `_run_detection_functions` runs on the main path and remove the unreachable duplicate `return conflicts` (line 946; live return at line 944).
2. Rework `_wrap_validation_errors` (lines 724–891): per-entry attribution, no substring gate, dedup key `(code, decision_target)`, entry list in the finding detail; sort every output list, including the `affected_files` set constructions at lines 489 and 847 (`REQ-005`'s verified non-determinism).
3. Move the version-error finding from the reused `CANONICAL-008` (line 857; `CANONICAL-008` belongs to `detect_multiple_canonical_specifications` at line 447) to `CANONICAL-012` (new) after the adrchk011 collision check.
4. Fix `classify_finding` to route the real code families (see Design decisions).
5. Fix the `--registry` help text (line 1039): state the actual default `config/documentation_canonical_sources.toml` (`REQ-013`).
6. Remove dead code in batches (see Details).

### Method
- Test-first: the failing fixture tests (documents seq 08/09, Plan Phase 2 step 1) define each expected finding set; fix one defect class, then re-run `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v` and both checker CLIs, keeping the clean repo-registry run exit 0.

### Details
- `REQ-012` dead code: `uv run vulture tools/check_canonical_source_conflicts.py --min-confidence 90` measures 1 item (the unreachable line 946) as of 2026-11-19 — the document's earlier "46 items + 3 imports" was a mislabeled `--min-confidence 60` measurement (49 lines; see Design decisions); `--min-confidence 60` items outside the UNK-03 keep list (unused constants and `from_name`/`from_blocking`/`from_severity`) are also removed per the Plan's `REQ-012` scope; keep anything a passing test imports (UNK-03).
- The wrapper's fragile error-text parsing (`err.split("'")[1]` at line 836) is replaced by the per-entry attribution rework in step 2.
- The existing code pins must keep passing: `CANONICAL-008` multiple-specifications tests (test file lines 108–114) and `CANONICAL-009` empty-area tests (lines 452–463).
- Companion conflicts-test-file pins updated in the same commit: the `CANONICAL-004` detector pin (test lines 381–383) flips to HIGH/BLOCKING citing `AC-07`; the two `blocked on seq 01`/`blocked on seq 02` skip stubs (test lines ~300–311) are deleted — their scenarios are covered by the new T06–T09 fixtures and the obsolete precedence semantics were removed by M-01-04.

### Companion test files
- `tests/tools/test_check_canonical_source_conflicts_routing.py`
  - Procedure: replace the synthetic `CANONICAL-C001`/`CANONICAL-C002` parametrization (lines 50–60) with the real code families produced by this file's detectors (`CANONICAL-001`–`CANONICAL-012`, `CANONICAL-W-NN`), covering HIGH→CANONICAL_CONFLICT, MEDIUM→CANONICAL_CONFLICT, warning→DOC_CORRECTION (`REQ-011`).
  - Validation: `uv run pytest tests/tools/test_check_canonical_source_conflicts_routing.py -v` passes with the fixed `classify_finding` (`AC-10`).

## Compatibility considerations

- GV-019/GV-021 Blocking gate semantics unchanged; finding codes 001–011 keep their existing meanings, `CANONICAL-012` (new) is additive.
- Consumers: the two conflicts test files, CI lint job, and the registry-validator import contract (`HAS_REGISTRY_VALIDATOR`) with `tools/check_canonical_source_registry.py` (fixed separately in seq 01); no public signature changes.

## Security considerations

- N/A: read-only static analysis tool; no new input surface.

## Rollback considerations

- Single-commit revert; the tool is read-only, no state to clean up.

## Validation plan

- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v` — fixture findings deduplicated, blocking, uniquely coded, correctly routed (`AC-06`–`AC-11`).
- `uv run python tools/check_canonical_source_conflicts.py --help` shows the corrected default (`AC-11`).
- `uv run vulture tools/check_canonical_source_conflicts.py --min-confidence 90`: 0 items after removal (`AC-04`, `T04`).
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- `AC-06`–`AC-11` hold; no finding code appears twice in any run; the repo-registry clean run still exits 0; exactly one `return conflicts` path remains; vulture ≥90 % count is 0 for this file.

## Out of Scope

- Splitting this oversized module (baselined in `tools/check_module_size_tools_baseline.txt`).
- GV-code renumbering and the registry config rows (owned by other rows of the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Main-path detector execution + duplicate-return removal (`REQ-006`, `REQ-010`) | Completed | 2026-11-19 | 2026-11-19 | T06 written red first (seq 09 fixtures); unreachable `return conflicts` deleted; main path = wrapper + `_run_detection_functions` merged on the `(code, decision_target)` key |
| 2 | Wrapper attribution + dedup + deterministic lists (`REQ-007`, `REQ-008`, `REQ-005`) | Completed | 2026-11-19 | 2026-11-19 | Data-driven `_ValidationRule` table; `CANONICAL-013` extension; attribution regex `(?:targeting\|decision_target)\s*(?:=\s*)?'…'` + source-path fallback (verification note: registry quotes the target with a space — `targeting 'x'` — so the planned quoted-extraction pattern needed the optional-`=` variant) |
| 3 | Code uniquification to `CANONICAL-012` (`REQ-009`) | Completed | 2026-11-19 | 2026-11-19 | Collision check RESOLVED 2026-11-19 (see Blocker Log); version branch `012` HIGH/BLOCKING, "source path does not exist"/"cannot read ADR file" branch `013` |
| 4 | Routing fix + help-text fix + companion routing parametrization (`REQ-010`, `REQ-011`, `REQ-013`) | Completed | 2026-11-19 | 2026-11-19 | `classify_finding` numeric family `^CANONICAL-\d{3}$` (HIGH/MEDIUM→CANONICAL_CONFLICT, LOW→DOC_CORRECTION); synthetic `CANONICAL-C` branch dropped; routing-test parametrization rewritten; help default fixed; `011` stays MEDIUM/NON_BLOCKING per `AC-01` (UNK-12) |
| 5 | Dead-code removal in batches (`REQ-012`) | Completed | 2026-11-19 | 2026-11-19 | `Severity.from_name`/`from_blocking`, `BlockingStatus.from_severity`, 11 unused `CLAIM_TYPE_*`, 12 `AUTHORITY_*`, `BLOCKING_SEVERITIES`/`NON_BLOCKING_SEVERITIES`/`SEVERITY_THRESHOLD_*`, route-name constants, unreachable line, unused `SUPPORTED_VERSIONS` import all removed; the six entry-level detectors were instead WIRED INTO `_run_detection_functions` (fallback-path completeness) instead of kept as dead code |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-19 | 2026-11-19 | See Implementation record below |

### Implementation record (2026-11-19)
- Validation gates: ruff format/check + mypy clean; bandit clean; `vulture --min-confidence 90` = 0 items (was 1: the unreachable return; the unused `SUPPORTED_VERSIONS` import was found by the gate and removed); three checker test files 200 passed / 1 skipped; `--help` prints `config/documentation_canonical_sources.toml`; `--unknown-option` exits 2; `--json` output byte-identical across runs (`REQ-005`); repo clean runs exit 0 for all three consumers (`AC-12` baseline, pre-seq-03); radon: no C-or-worse in the touched code (`_wrap_validation_errors` D(22) → B(10)).
- Dedup attribution: `decision_target` is now populated by the nine registry-key detectors (`001`/`002`/`003`/`004`/`005`/`006`/`008`/`009`/`010` findings) so wrapper findings and detector findings for the same `(code, decision_target)` merge into exactly one finding per run (`AC-08`, `AC-09`). Cross-code pairs on the same pair (detector `001` + wrapper `007` for one duplicate) are intentionally distinct codes and both kept (pinned by T08).
- `CANONICAL-013` extension recorded for the Final Report (beyond the Plan's `REQ-009` code list): HIGH/BLOCKING, covers "source path does not exist" and "cannot read ADR file" — the `REQ-007` no-drop guarantee.
- T12 corrected-rows half (`test_corrected_repo_rows_match_governing_spec`) is skip-marked "blocked on seq 03" and must be unskipped by member 03; the defective-rows half and the clean-run half already pass. Pin value `scripts/eventbus/schema.sql` verified to exist.
- Remaining `vulture --min-confidence 60` items are the UNK-03 keeps (`classify_finding`, `detect_duplicate_active_records`/`_build_key` — imported by the routing tests) plus the `CanonicalConflict` 12-field template attributes read via `getattr` (false positive) and unused enum members (`Severity.LOW`, `BlockingStatus.WARNING`) retained as API surface.
- Module length after rework: 1056 lines (was 1063).

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | `CANONICAL-012` allocation must be collision-checked against the adrchk011 plan (UNK-01) | Yes | 2026-11-19 — repo uses only 001–011; adrchk011 issue/plan contain zero `CANONICAL-` references |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (main path), `REQ-007` (wrapper gate), `REQ-008` (dedup), `REQ-009` (unique codes), `REQ-010` (routing), `REQ-011` (routing tests), `REQ-012` (dead code), `REQ-013` (help text)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `tools/check_canonical_source_conflicts.py`, `tests/tools/test_check_canonical_source_conflicts_routing.py`
