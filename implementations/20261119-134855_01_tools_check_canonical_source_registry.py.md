## Goal

- Fix the checker defects in `tools/check_canonical_source_registry.py` (Blocking gate GV-020) per the Plan: `REQ-001` single severity for non-Accepted ADR references, `REQ-002` repository-root anchored paths, `REQ-003` unknown-option guard, `REQ-004` dead-code removal, `REQ-005` deterministic error output.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the five fixes above, applied to the target file only.
- Companion test coverage lives in `implementations/20261119-134855_08_tests_tools_test_check_canonical_source_registry.py.md` (Plan Phase 1 step 1: add the failing fixture tests there before these fixes).

## Assumptions

- Clean baseline: the tool exits 0 on the repo registry when run from the repo root (verified 2026-11-19); the fixes must keep that run green (Plan `AC-12`).
- vulture (min-confidence 90) measured 2026-11-19: 100 items in this file (the Plan's "~98" is approximate); the removal list follows UNK-03 — keep anything a passing test imports.
- Fixture registries/ADRs are inlined as pytest fixtures under `tmp_path`, not committed as standalone files (Plan Assumptions).

## Design decisions

- Repo-root anchoring (`REQ-002`): add a module-level `REPO_ROOT` (new) = `Path(__file__).resolve().parent.parent`; derive `DEFAULT_REGISTRY_PATH` (line 51) from it; replace `Path.cwd()` at line 960 (in `validate_registry_schema`) and line 981 (in `main`) with `REPO_ROOT` (new). This mirrors `check_canonical_source_conflicts.py` (lines 921–925) and `check_canonical_document_prose.py`.
- Single severity (`REQ-001`): keep `RegistryEntry.validate`'s error text "ADR-sourced entry has non-Accepted status" (line 143) as the only severity source for that class; `validate_all` (lines 841–856) must not also report the same class as warnings via `find_non_accepted_adr` (lines 793–807) — drop the warning extension at lines 852–854 (the conflicts-side warning is owned by the companion conflicts-checker document). `AC-01` pins the outcome: registry reports exactly one error; the conflicts side reports exactly one warning.

## Alternatives considered

- Keep the cwd-relative default and pass `--registry` explicitly everywhere — rejected: `AC-02` requires identical findings from any cwd without caller discipline.

## Implementation
### Target file
`tools/check_canonical_source_registry.py`
### Procedure
1. Add the `REPO_ROOT` (new) constant and re-derive `DEFAULT_REGISTRY_PATH` from it.
2. Replace the two `Path.cwd()` call sites with `REPO_ROOT` (new).
3. Remove the duplicated severity reporting in `validate_all` (see Design decisions).
4. Remove dead code in batches (see Details); run the checker test file after each batch.
5. Confirm error-list output determinism (see Details) and add the regression guard tests per the test document.

### Method
- Each fix is gated by Plan `AC-01`–`AC-05` fixture tests (written first in the test document): fix one defect class, re-run `uv run pytest tests/tools/test_check_canonical_source_registry.py -v` and the two checker CLIs, keep the clean repo-registry run exit 0.

### Details
- `REQ-004` dead code: run `uv run vulture tools/check_canonical_source_registry.py --min-confidence 90`; candidate clusters are the unused `RegistryEntry` helpers (`clone`, `diff`, `get_effective_area`, `is_architecture_decision`, `has_multiple_sources`, ...), the `CanonicalSourceRegistry` aux methods (`copy`, `clone_with_version`, `sort_by_area_then_target`, `to_json`, `from_json`), and `find_unrecognized_claim_types`, `find_multi_source_on_single_source_type`, `find_duplicate_entries` — verify each against the three checker test files and `check_canonical_source_conflicts.py` imports before deleting (UNK-03).
- `REQ-003`: `main` already uses `argparse.parse_args` and exits 2 on unknown options (live probe 2026-11-19); keep the behavior and add the `T03` regression test; do not switch to lenient (non-erroring) argument parsing.
- `REQ-005`: `validate` builds its error list from entry order with no set constructions, so repeated runs are already byte-identical; add the `T05` assertion to lock it. The Plan's original `--diff` wording was re-scoped 2026-11-19: no `--diff` CLI option exists in the current source.

## Compatibility considerations

- GV-020 Blocking semantics are unchanged (Plan Assumptions); only what is reported changes.
- Consumers of this module: `tools/check_canonical_source_conflicts.py` (imports `load_registry`, `validate_registry_schema` under `HAS_REGISTRY_VALIDATOR`), the three `tests/tools/` checker test files, and the CI gate registration in `tools/_validation_gate_defs.py` — none of their call signatures change.
- Removing a helper that any passing test imports is out of contract: re-check before each batch (UNK-03).

## Security considerations

- N/A: no trust-boundary or input-handling change; the tools only read registry/config files.

## Rollback considerations

- Single-commit revert; the checker is read-only, so no data or state cleanup is required.

## Validation plan

- `uv run pytest tests/tools/test_check_canonical_source_registry.py -v` — fixture findings exact (`AC-01`–`AC-05`).
- Run the tool from the repo root and from `/tmp/opencode` (with absolute `--registry`): identical findings (`AC-02`).
- `uv run python tools/check_canonical_source_registry.py --unknown-option`; expect exit 2 (`AC-03`).
- `uv run vulture tools/check_canonical_source_registry.py --min-confidence 90`: 0 items after removal (`AC-04`, `T04`).
- Full sequence per `rules/toolchain.md` (lint/type checks, full suite, diff-cover ≥ 90 %).

## Completion criteria

- `AC-01`–`AC-05` hold; the repo-registry clean run still exits 0; vulture ≥90 % count is 0 for this file; the existing 13 test functions stay green.

## Out of Scope

- Splitting this oversized module (baselined in `tools/check_module_size_tools_baseline.txt`; Plan Out-of-Scope).
- Changes to `tools/check_canonical_source_conflicts.py` (own document, seq 02) and to the registry config (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repo-root anchoring (`REQ-002`) | Pending | — | — | Requires `REPO_ROOT` (new) |
| 2 | Single-severity fix in `validate_all` (`REQ-001`) | Pending | — | — | |
| 3 | Dead-code removal in batches (`REQ-004`) | Pending | — | — | UNK-03 gating per batch |
| 4 | Regression guards for unknown options and output determinism (`REQ-003`, `REQ-005`) | Pending | — | — | Already current behavior; lock with tests |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (severity consistency), `REQ-002` (cwd-independent paths), `REQ-003` (unknown-option guard), `REQ-004` (dead code), `REQ-005` (deterministic output)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `tools/check_canonical_source_registry.py`
