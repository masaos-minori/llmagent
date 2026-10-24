# Implementation Procedure: tests/tools/test_check_docs_structure.py

## Goal

Add regression coverage for `check_docs_structure.py` `main()` glob exit semantics — a harness plus
four `main()`-driving tests (zero-match, valid single file, mixed valid+invalid globs, partial
match) that pin the new failure behavior and the unchanged green path (`REQ-004` regression tests,
`REQ-001`/`REQ-002`/`REQ-003` behaviors under test).

## Scope

- Append a harness helper and one new test class with four tests to
  `tests/tools/test_check_docs_structure.py`; existing 79 tests stay byte-identical.
- No production code in this row; the tests are written first and are expected to fail until
  procedure doc `_01` lands (TDD order).

## Assumptions

- Baseline `uv run pytest tests/tools/test_check_docs_structure.py -q` → 79 passed (77 test
  functions, measured 2026-10-24 at HEAD `9331b337a`); none invokes `main()` today, so `main()`
  must be driven via monkeypatched `sys.argv`.
- The permissive loader idiom `load_front_matter_schema(<nonexistent tmp path>)` (already used at
  `:60,67,85,95` of this file) keeps tests independent of the canonical
  `schemas/doc_front_matter.json`. The Plan's original "nonexistent `--schema` path" phrasing was
  corrected by revalidation (it raises `FileNotFoundError`; omitting `--schema` is default-on) —
  this row uses the monkeypatched-loader form recorded in the Plan's Revalidation record.
- tmp docs live under `tmp_path/docs/...` with front matter in the file's existing `_COMPLIANT_DOC`
  style (extended with `related: []` and the `## Keywords` tail) so `validate_file`'s non-schema
  checks pass on clean fixtures.

## Design decisions

- Patch `ROOT_DIR` and `DOCS_DIR` (the latter feeds `_build_basename_index(DOCS_DIR)` at `:486`) and
  `load_front_matter_schema` via the pytest `monkeypatch` fixture — tests never read the repo docs
  tree, keeping results independent of repo docs state (Plan harness requirement).
- Assert `main()`'s return code plus `capsys` output rather than shelling out: faster and hermetic;
  the shell-level AC-1/AC-2 runs remain validation commands, not unit tests.

## Alternatives considered

- subprocess-based invocation of the script: rejected — slower and leaks real repo state through the
  default globs unless fully sandboxed; monkeypatching gives the same contract for free.

## Implementation

### Target file

`tests/tools/test_check_docs_structure.py`

### Procedure

1. Add `import sys` and `from tools import check_docs_structure as mod` to the import block (new
   imports; existing direct imports stay).
2. Append the helper `_run_main` (new) and class `TestMainGlobExitSemantics` (new) at the end of
   the file with the four tests under Method.

### Method

```python
def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    *globs: str,
) -> int:
    monkeypatch.setattr(mod, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(mod, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(
        mod,
        "load_front_matter_schema",
        lambda _p: load_front_matter_schema(tmp_path / "no_schema_here.json"),
    )
    monkeypatch.setattr(sys, "argv", ["check_docs_structure.py", *globs])
    return mod.main()
```

Tests (all (new), each calling `_run_main` (new) after writing fixtures with the existing `_write`):

| Test | Fixture | Globs | Expected |
|---|---|---|---|
| `test_main_glob_zero_match_exits_1` (new) | empty tmp docs dir | `"docs/nope_*.md"` | return `1`; stderr contains `no files matched` (new) naming the pattern |
| `test_main_partial_match_exits_1` (new) | one compliant doc | `"docs/a.md" "docs/nope_*.md"` | return `1`; unmatched pattern named, no `All checks passed` |
| `test_main_unmatched_with_findings_additive` (new) | one doc with an invalid `status:` value + compliant doc | `"docs/*.md" "docs/nope_*.md"` | return `1`; findings summary line and unmatched report both present (REQ-002) |
| `test_main_all_matched_clean_exit_0` (new) | one compliant doc | `"docs/a.md"` | return `0`; `All checks passed` (REQ-003 anchor) |

### Details

- The invalid-`status` fixture reuses the file's existing status-value violation pattern (checked by
  `check_status_value`), so the mixed test produces exactly one finding.
- No tmp fixture path contains `docs/10_adr/`, keeping the ADR-id branch inert; `_write` already
  creates parent dirs.

## Compatibility considerations

- Existing tests import module functions/constants (`MAX_SIZE`, `SIZE_EXCEPTIONS`, ...) directly and
  are untouched; the module-level import list only grows.
- The tests pin the partial-match = fail policy; a future owner reversal changes one branch in
  `_01` plus `test_main_partial_match_exits_1` (new).

## Security considerations

N/A: test-only change; tmp fixtures only, no network, no secrets.

## Rollback considerations

N/A: revert the commit — the appended helper/class/imports are self-contained at file end and the
import block.

## Validation plan

- `uv run pytest tests/tools/test_check_docs_structure.py -q -k MainGlobExit -v` → the four new
  tests listed; against unmodified `main()` the zero-match/partial/mixed tests fail (defect
  capture), after `_01` all pass.
- `uv run pytest tests/tools/test_check_docs_structure.py -q` → 79 existing + 4 new pass (AC-3).
- `uv run ruff check tests/` → clean.

## Completion criteria

- Four named tests exist and pass against the fixed `main()`; every REQ-001/REQ-002/REQ-003 behavior
  maps to at least one named test; the 79 existing tests pass unmodified (AC-3).

## Out of Scope

- `tools/check_docs_structure.py` itself (procedure doc `20261024-235840_01`).
- Shell-level AC-1/AC-2 invocations and CI (validation commands, not tests).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write harness + four failing tests (before `_01` lands) | Pending | — | — | TDD: failures prove defect capture |
| 2 | Re-run after `_01` lands; all pass | Pending | — | — | |
| 3 | Run `ruff check tests/` + full-file pytest | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (regression tests for zero-match, valid file, mixed globs),
  covering `REQ-001`–`REQ-003` behaviors
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235840
- **Related target files**: `tests/tools/test_check_docs_structure.py`
