## Goal

Implement REQ-007 (`plans/20260923-152824_plan.md`) in
`tools/check_adr_structure.py`: update `ADR_DIR` for the ADR folder's new
location.

## Scope

Modify only `tools/check_adr_structure.py` to change
`ADR_DIR = REPO_ROOT / "docs" / "adr"` to
`ADR_DIR = REPO_ROOT / "docs" / "10_adr"`.

## Assumptions

- `ADR_DIR` is passed directly as `docs_dir` to
  `discover_md_files(ADR_DIR, prefix="")` (line 131) — unaffected by seq 01's
  recursive-glob change, since `docs/10_adr` has no further nesting; this
  document's update is independent of seq 01 landing.
- `tests/tools/test_check_adr_structure.py` is confirmed hermetic (in-memory
  `DocFile` fixtures only, per its own docstring: "Live docs/adr/*.md
  validation is exercised separately by running the tool against the real
  repository, not duplicated here as a unit test") — no test change needed.
- This tool is wired into the `adr-structure` pre-commit hook.

## Design decisions

- Single constant-value update, same pattern as seq 05's `ADR_DIR` change.

## Alternatives considered

- N/A: direct constant-value update is the only viable approach.

## Implementation

### Target file

`tools/check_adr_structure.py`

### Procedure

1. Locate `ADR_DIR = REPO_ROOT / "docs" / "adr"` (line 43).
2. Change it to `ADR_DIR = REPO_ROOT / "docs" / "10_adr"`.

### Method

One `Edit` call, a one-line constant-value update.

### Details

Current:
```python
ADR_DIR = REPO_ROOT / "docs" / "adr"
```

After modification:
```python
ADR_DIR = REPO_ROOT / "docs" / "10_adr"
```

## Compatibility considerations

- Wired into the `adr-structure` pre-commit hook — this document's own
  Validation plan should include a pre-commit invocation to catch any
  wiring issue early.
- Correctness against the real repository only lands once the corresponding
  ADR physical-move issue (`docsreorg11`) also lands — until then, this tool
  will report "no files found" against the still-flat `docs/adr/` location,
  same coordinated-landing-order note as sibling documents in this Plan.

**Correction found during git-commit-and-sync (2026-09-23)**: at commit time,
sibling documents seq 07/seq 08's `ADR_INDEX` update (a single-file existence
check, unlike this tool's directory listing) turned out to make the
`adr-invariant-matrix`/`adr-reference-scoped` pre-commit hooks fail outright
against the still-flat pre-move tree — an actual blocking regression, not a
silent "no files found" degradation. To keep all three ADR tools' rollout
coordinated, this document's own `ADR_DIR` update was reverted back to
`REPO_ROOT / "docs" / "adr"` in the same commit and will be re-applied
together with `docsreorg11`'s physical move, alongside seq 07/seq 08.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `ADR_DIR` to its original value.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_adr_structure.py -q` (confirmed
hermetic — passes unchanged). Run
`uv run pre-commit run adr-structure --all-files` against the current
(pre-move) tree to confirm the hook itself still invokes correctly (it will
report 0 ADR files found until `docsreorg11` lands, which is expected, not a
failure of this document's own change).

## Completion criteria

- `ADR_DIR` equals `REPO_ROOT / "docs" / "10_adr"`.
- `uv run pytest tests/tools/test_check_adr_structure.py -q` passes
  unchanged.
- `uv run pre-commit run adr-structure --all-files` runs without a Python
  exception (a "0 files found" report against the pre-move tree is expected,
  not a failure).

## Out of scope

- `REPO_ROOT`'s own value.
- The structural-check logic once ADR files are found.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-161337 | 20260923-161337 | Step3 stale_detector false-positive ('docs_dir', common variable name) confirmed as noise, bypassed. ADR_DIR updated to docs/10_adr. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-161337 | 20260923-161337 | No test change needed; test_check_adr_structure.py confirmed hermetic, 5 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-161337 | 20260923-161337 | ruff/mypy/bandit pass. pytest: 5 passed. uv run pre-commit run adr-structure --all-files: Passed (0 ADR files found against the still-flat pre-move tree, no Python exception -- expected). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-161337 | 20260923-161337 | N/A: no docs/00_index.md task-scope mapping for tools/check_adr_structure.py. |
| — | Correction: `ADR_DIR` update reverted at commit time | Reverted | 20260923-161337 | 2026-09-23 (commit 2d15f9cb8) | See Compatibility considerations' "Correction found during git-commit-and-sync" note. `ADR_DIR` restored to `REPO_ROOT / "docs" / "adr"`; will be re-applied together with `docsreorg11`. |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_adr_structure.py