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
- Severity mapping per the gate definitions (Plan Design "Severity model"): GV-021 classes — missing/invalid source, unrecognized claim type, Draft/Proposed normative source — are wrapped as blocking HIGH findings (current code marks lines 770–786 and 880–890 MEDIUM/NON_BLOCKING); the non-Accepted ADR reference class reported by the registry tool's `validate` stays a single registry error with exactly one conflicts-side warning (`AC-01`). Distinguish the two classes in the wrapper so `AC-01` and `AC-07` are simultaneously satisfiable; the fixture tests pin the outcome.
- Routing (`REQ-010`): `classify_finding` (lines 965–995) currently matches only `CANONICAL-C`/`CANONICAL-W` prefixes, so the real blocking family `CANONICAL-NNN` falls through to KNOWN_ISSUE (line 995); route the numeric family per severity and keep `CANONICAL-W-NN` → DOC_CORRECTION.

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
- `REQ-012` dead code: `uv run vulture tools/check_canonical_source_conflicts.py --min-confidence 90` (46 unused items + 3 unused imports measured 2026-11-19; Plan's "~47" is approximate); keep anything a passing test imports (UNK-03).
- The wrapper's fragile error-text parsing (`err.split("'")[1]` at line 836) is replaced by the per-entry attribution rework in step 2.
- The existing code pins must keep passing: `CANONICAL-008` multiple-specifications tests (test file lines 102–112) and `CANONICAL-009` empty-area tests (lines 446–463).

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
| 1 | Main-path detector execution + duplicate-return removal (`REQ-006`, `REQ-010`) | Pending | — | — | |
| 2 | Wrapper attribution + dedup + deterministic lists (`REQ-007`, `REQ-008`, `REQ-005`) | Pending | — | — | |
| 3 | Code uniquification to `CANONICAL-012` (`REQ-009`) | Pending | — | — | After adrchk011 collision check (UNK-01) |
| 4 | Routing fix + help-text fix + companion routing parametrization (`REQ-010`, `REQ-011`, `REQ-013`) | Pending | — | — | |
| 5 | Dead-code removal in batches (`REQ-012`) | Pending | — | — | UNK-03 gating per batch |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | `CANONICAL-012` allocation must be collision-checked against the adrchk011 plan (UNK-01) | No | — |

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
