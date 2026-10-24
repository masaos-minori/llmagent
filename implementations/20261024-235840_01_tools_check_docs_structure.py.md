# Implementation Procedure: tools/check_docs_structure.py

## Goal

Make `main()` in `tools/check_docs_structure.py` fail when a supplied glob matches zero files:
track per-pattern match results, print `no files matched the given glob(s): {patterns}` (new) to
stderr, and return 1, while matched files' findings and all non-empty run behavior stay identical
(`REQ-001` unmatched-pattern message + non-zero exit, `REQ-002` findings still printed and counted
additively, `REQ-003` non-empty runs unchanged).

## Scope

- Modify only two regions of `main()` in `tools/check_docs_structure.py`: the glob resolution block
  (`:480-483`) and the tail exit path (`:517-521`).
- Every individual check function (`check_size`, `check_links`, `check_schema_compliance`,
  `check_adr_related_coverage`, `check_unique_adr_ids`, ...) stays byte-identical.

## Assumptions

- Today `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` exits `0` with
  `All checks passed` (re-probed 2026-10-24 at HEAD `9331b337a`, AC-1 defect reproduced).
- `uv run python tools/check_docs_structure.py "docs/**/*.md"` exits `0` today and must keep doing
  so (AC-2 baseline, measured 2026-10-24).
- The implicit default glob `docs/**/*.md` (used when no globs are passed) zero-matching is
  impossible with the current docs tree; if it ever happens it fails like any other zero-match —
  recorded Plan Design behavior, not a deviation.

## Design decisions

- Partial match fails like an all-empty match (fail, not warn) — the Issue's adopted decision,
  owner-revisable (Plan `Assumptions`); the message names the unmatched pattern(s) as supplied
  (Plan Design "Message form").
- Failure report is emitted before the existing findings summary so a mixed run prints both
  (REQ-002); report goes to stderr to separate it from per-file findings.

## Alternatives considered

- Glob normalization (auto-rewriting `23_agent/*` into `docs/23_agent/*`): out of Plan Scope —
  silently rewriting a user pattern is the failure mode the issue warns against.
- Warning + exit 0 on partial match: rejected by the frozen fail-not-warn decision above.

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

1. Replace the glob resolution block (`:480-483`) with the tracking form under Method.
2. Replace the tail exit path (`:517-521`, from `if total_issues:` to `return 0`) with the form
   under Method. Everything between (basename index, schema loading, `validate_file` loop, ADR id
   check) is untouched.

### Method

Glob block becomes:

```python
    patterns = args.globs or ["docs/**/*.md"]
    files: set[Path] = set()
    unmatched: list[str] = []
    for pattern in patterns:
        matched = list(ROOT_DIR.glob(pattern))
        if not matched:
            unmatched.append(pattern)
        files.update(matched)
    print(f"{len(files)} files matched the given glob(s): {patterns}")
```

Tail becomes:

```python
    if unmatched:
        print(f"no files matched the given glob(s): {', '.join(unmatched)}", file=sys.stderr)

    if total_issues:
        print(f"\n❌ Found {total_issues} issue(s).")
        return 1

    if unmatched:
        return 1
    print("\n✅ All checks passed.")
    return 0
```

### Details

- `unmatched` (new) is a function-local list preserving supplied pattern order; no new imports
  (`sys`, `ROOT_DIR` already in the module) and no new module-level names.
- When `unmatched` (new) is empty the tail output/exit is identical to today (REQ-003); when
  findings also exist, both the unmatched report and `Found {n} issue(s).` are emitted and exit
  stays 1 (REQ-002).

## Compatibility considerations

- CI `governance-docs-consistency.yml` (`:89`, `:95`) always passes globs with a non-empty match
  set (172 files measured), so CI invocations and exit behavior are unchanged (REQ-003).
- `tools/run_validation_gates.py`'s `check_docs_structure` gate row (`:642-655`) stays `Not
  available` (placeholder argv + `scripts/check_docs_structure.py` still absent); never auto-invoked.
- Existing 79 tests in `tests/tools/test_check_docs_structure.py` call module functions directly,
  none invokes `main()`, so none can break from this row.

## Security considerations

N/A: output/exit-path change in a repo-local validator; no I/O, secrets, or untrusted input beyond
argv globs already accepted today.

## Rollback considerations

Single-commit revert: the two edited regions of `main()` are self-contained; no persistence or
schema involvement.

## Validation plan

- `uv run pytest tests/tools/test_check_docs_structure.py -q` — all 79 existing tests pass plus the
  new `main()`-driving tests from the test row (written first, TDD order; they fail against the
  current silent-pass behavior before this row lands).
- `uv run python tools/check_docs_structure.py "docs/**/*.md"` → exit `0`, `All checks passed`
  (AC-2).
- `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` → exit `1`, stderr names
  the pattern (AC-1).
- `uv run ruff format tools/`, `uv run ruff check tools/`, `uv run mypy tools` → clean.

## Completion criteria

- Zero-match and mixed (unmatched + findings) runs exit 1 naming the unmatched pattern(s); every
  non-empty-match run's output and exit code is unchanged; the two commands above behave as
  recorded in the Plan Verification Table (AC-1, AC-2).

## Out of Scope

- `tests/tools/test_check_docs_structure.py` (procedure doc `20261024-235840_02`).
- `tools/TOOL_DESCRIPTIONS.md` (procedure doc `20261024-235840_03`) and
  `docs/00_governance/governance_04_documentation-checks.md` (procedure doc
  `20261024-235840_04`).
- `tools/run_validation_gates.py` and `.github/workflows/governance-docs-consistency.yml`
  (Reference Files: unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write failing `main()`-driving tests first (procedure doc `_02`) | Pending | — | — | TDD gate for this row |
| 2 | Apply the glob-tracking and tail-exit edits to `main()` | Pending | — | — | only `:480-483` and `:517-521` regions |
| 3 | Run targeted tests + AC-1/AC-2 commands + ruff/mypy | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (unmatched-glob message + non-zero exit), `REQ-002` (findings
  printed and counted additively), `REQ-003` (non-empty runs unchanged)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235840
- **Related target files**: `tools/check_docs_structure.py`
