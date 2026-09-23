## Goal

Implement REQ-008 (`plans/20260923-152824_plan.md`) in
`tools/check_adr_reference.py`: update `ADR_INDEX` for `adr-index.md`'s new
location.

## Scope

Modify only `tools/check_adr_reference.py` to:
1. Change `ADR_INDEX = DOCS_DIR / "adr-index.md"` to
   `ADR_INDEX = DOCS_DIR / "10_adr" / "adr-index.md"`.
2. **Correction found during this document's own implementation**
   (2026-09-23): `collect_issues()`'s "not found" branch hardcodes the
   message string `"docs/adr-index.md not found"` (line ~163) rather than
   deriving it from `ADR_INDEX` — confirmed via running the
   `adr-reference-scoped` pre-commit hook against the current (pre-move)
   tree: it correctly detects `ADR_INDEX` (now `docs/10_adr/adr-index.md`)
   doesn't exist yet, but reports the stale bare-path text instead of the
   actual path it checked. Change it to an f-string using `ADR_INDEX`.

## Assumptions

- `DOCS_DIR = REPO_ROOT / "docs"` (line 43) is used only to build
  `ADR_INDEX` in this file — confirmed via `rg "DOCS_DIR"` during the source
  Plan's drafting, no other usage exists, so `DOCS_DIR` itself needs no
  change.
- `tests/tools/test_check_adr_reference.py` is confirmed hermetic
  (`monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)` in
  every test, per its own docstring: "Live... validation is exercised
  separately by running the tool against the real repository, not
  duplicated here as a unit test") — no test change needed.
- This tool is wired into the `adr-reference-scoped` pre-commit hook.

## Design decisions

- Single constant-value update, same pattern as seq 06.

## Alternatives considered

- N/A: direct constant-value update is the only viable approach.

## Implementation

### Target file

`tools/check_adr_reference.py`

### Procedure

1. Locate `ADR_INDEX = DOCS_DIR / "adr-index.md"` (line 44).
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

- Wired into the `adr-reference-scoped` pre-commit hook.
- Correctness against the real repository only lands once `docsreorg11`
  (ADR physical move) also lands — until then, `collect_issues()`'s
  `if not ADR_INDEX.exists()` branch will report "docs/adr-index.md not
  found" (with the new path in the message), which is expected, not a
  failure of this document's own change.

**Correction found during git-commit-and-sync (2026-09-23)**: the "expected,
not a failure of this document's own change" framing above understated the
actual impact — an `exit 1` from `adr-reference-scoped` is a pre-commit hook
failure, which blocks every commit outright, not merely a degraded-but-
harmless report like sibling tools' silent "no issues found" behavior. This
made the `git-commit-and-sync` commit for this Plan's changes fail. Per user
decision, `ADR_INDEX` (and the message f-string) were reverted back to
`DOCS_DIR / "adr-index.md"` / `"docs/adr-index.md not found"` in the same
commit, and will be re-applied together with `docsreorg11`'s physical move.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `ADR_INDEX` to its original value.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_adr_reference.py -q` (confirmed
hermetic — passes unchanged). Run
`uv run pre-commit run adr-reference-scoped --all-files` against the current
(pre-move) tree to confirm the hook still invokes correctly (an
`ADR_INDEX.exists()` failure against the pre-move tree is expected, not a
failure of this document's own change).

## Completion criteria

- `ADR_INDEX` equals `DOCS_DIR / "10_adr" / "adr-index.md"`.
- `uv run pytest tests/tools/test_check_adr_reference.py -q` passes
  unchanged.
- `uv run pre-commit run adr-reference-scoped --all-files` runs without a
  Python exception.

## Out of scope

- `DOCS_DIR`'s own value.
- The reference-checking logic once `ADR_INDEX` is found.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-161956 | 20260923-161956 | stale_detector: no mismatches (clean pass). ADR_INDEX updated. Additional discovery: collect_issues()'s 'not found' Issue hardcoded the message string 'docs/adr-index.md not found' instead of deriving it from ADR_INDEX -- confirmed via pre-commit run showing the stale bare-path text. Corrected this document's own procedure and fixed it (f-string using ADR_INDEX). |
| 2 | Add or update tests per Validation plan | Completed | 20260923-161956 | 20260923-161956 | No test change needed; test_check_adr_reference.py confirmed hermetic, 7 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-161956 | 20260923-161956 | ruff/mypy/bandit pass. pytest: 7 passed. uv run pre-commit run adr-reference-scoped --all-files: exit 1 (expected pre-move state), now correctly reports the real checked path /home/masaos/llmagent/docs/10_adr/adr-index.md instead of the stale hardcoded text. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-161956 | 20260923-161956 | N/A: no docs/00_index.md task-scope mapping for tools/check_adr_reference.py. |
| — | Correction: `ADR_INDEX`/message update reverted at commit time | Reverted | 20260923-161956 | 2026-09-23 (commit 2d15f9cb8) | See Compatibility considerations' "Correction found during git-commit-and-sync" note. Reverted to `DOCS_DIR / "adr-index.md"`; will be re-applied together with `docsreorg11`. |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_adr_reference.py