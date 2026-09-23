## Goal

Implement REQ-009 (`plans/20260923-152824_plan.md`) in
`tools/check_adr_invariant_matrix.py`: update `ADR_INDEX` for
`adr-index.md`'s new location.

## Scope

Modify only `tools/check_adr_invariant_matrix.py` to:
1. Change `ADR_INDEX = DOCS_DIR / "adr-index.md"` to
   `ADR_INDEX = DOCS_DIR / "10_adr" / "adr-index.md"`.
2. **Correction found during seq 07's implementation of the identical
   pattern** (2026-09-23): this file has the same "not found" hardcoded
   message issue seq 07 found in `tools/check_adr_reference.py` — line ~116
   hardcodes `message="docs/adr-index.md not found"` rather than deriving it
   from `ADR_INDEX`. Change it to an f-string using `ADR_INDEX`, same fix as
   seq 07.

## Assumptions

- `DOCS_DIR = REPO_ROOT / "docs"` (line 42) is used only to build
  `ADR_INDEX` in this file — same pattern as seq 07
  (`tools/check_adr_reference.py`), confirmed via `rg "DOCS_DIR"` during the
  source Plan's drafting.
- `tests/tools/test_check_adr_invariant_matrix.py` is confirmed hermetic
  (in-memory Matrix-table fixtures only, per its own docstring: "Live
  `docs/adr-index.md` validation (AC-1) is exercised separately by running
  the tool against the real repository, not duplicated here as a unit
  test") — no test change needed.
- This tool is wired into the `adr-invariant-matrix` pre-commit hook.

## Design decisions

- Single constant-value update, identical pattern to seq 07.

## Alternatives considered

- N/A: direct constant-value update is the only viable approach.

## Implementation

### Target file

`tools/check_adr_invariant_matrix.py`

### Procedure

1. Locate `ADR_INDEX = DOCS_DIR / "adr-index.md"` (line 43).
2. Change it to `ADR_INDEX = DOCS_DIR / "10_adr" / "adr-index.md"`.

### Method

One `Edit` call, a one-line constant-value update.

### Details

Current:
```python
DOCS_DIR = REPO_ROOT / "docs"
ADR_INDEX = DOCS_DIR / "adr-index.md"
```

After modification:
```python
DOCS_DIR = REPO_ROOT / "docs"
ADR_INDEX = DOCS_DIR / "10_adr" / "adr-index.md"
```

## Compatibility considerations

- Wired into the `adr-invariant-matrix` pre-commit hook.
- Correctness against the real repository only lands once `docsreorg11`
  (ADR physical move) also lands — until then, this tool will report
  `ADR_INDEX` not found against the pre-move tree, expected, not a failure
  of this document's own change.

**Correction found during git-commit-and-sync (2026-09-23)**: same
understatement as seq 07 — an `exit 1` from `adr-invariant-matrix` is a
pre-commit hook failure that blocks every commit outright, not a
harmless degraded report. Per user decision, `ADR_INDEX` (and the message
f-string) were reverted back to `DOCS_DIR / "adr-index.md"` /
`"docs/adr-index.md not found"` in the same commit as seq 06/seq 07, and
will be re-applied together with `docsreorg11`'s physical move.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `ADR_INDEX` to its original value.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q`
(confirmed hermetic — passes unchanged). Run
`uv run pre-commit run adr-invariant-matrix --all-files` against the
current (pre-move) tree to confirm the hook still invokes correctly.

## Completion criteria

- `ADR_INDEX` equals `DOCS_DIR / "10_adr" / "adr-index.md"`.
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` passes
  unchanged.
- `uv run pre-commit run adr-invariant-matrix --all-files` runs without a
  Python exception.

## Out of scope

- `DOCS_DIR`'s own value.
- The Invariant Matrix parsing/validation logic once `ADR_INDEX` is found.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-162116 | 20260923-162116 | stale_detector: no mismatches (clean pass). ADR_INDEX updated. Same hardcoded-message issue as seq07 found and fixed (message=f'{ADR_INDEX} not found'). |
| 2 | Add or update tests per Validation plan | Completed | 20260923-162116 | 20260923-162116 | No test change needed; test_check_adr_invariant_matrix.py confirmed hermetic, 6 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-162116 | 20260923-162116 | ruff/mypy/bandit pass. pytest: 6 passed. uv run pre-commit run adr-invariant-matrix --all-files: exit 1 (expected pre-move state), correctly reports real checked path /home/masaos/llmagent/docs/10_adr/adr-index.md. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-162116 | 20260923-162116 | N/A: no docs/00_index.md task-scope mapping for tools/check_adr_invariant_matrix.py. |
| — | Correction: `ADR_INDEX`/message update reverted at commit time | Reverted | 20260923-162116 | 2026-09-23 (commit 2d15f9cb8) | See Compatibility considerations' "Correction found during git-commit-and-sync" note. Reverted to `DOCS_DIR / "adr-index.md"`; will be re-applied together with `docsreorg11`. |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_adr_invariant_matrix.py