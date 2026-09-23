## Goal

Implement REQ-006 (`plans/20260923-152824_plan.md`) in
`tools/check_known_deviation_sync.py`: update `ADR_DIR` for the ADR folder's
new location, and `_GOVERNANCE_KNOWN_ISSUES_DOC` for the directory-qualified
`rel_path` that `discover_md_files()` now produces once seq 01 lands.

## Scope

Modify only `tools/check_known_deviation_sync.py` to:
1. Change `ADR_DIR = DOCS_DIR / "adr"` to `ADR_DIR = DOCS_DIR / "10_adr"`.
2. Change `_GOVERNANCE_KNOWN_ISSUES_DOC`'s value from
   `"00_governance_03_issue-and-uncertainty-management.md"` to
   `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.

## Assumptions

- `ADR_DIR` is passed directly as `docs_dir` to
  `discover_md_files(ADR_DIR, prefix="")` inside `discover_adr_docs()`
  (line 148) — unaffected by seq 01's recursive-glob change, since
  `docs/10_adr` (once the physical move lands) has no further nesting; this
  document's `ADR_DIR` update alone is sufficient, no dependency on seq 01
  landing first for this specific constant.
- `_GOVERNANCE_KNOWN_ISSUES_DOC`, by contrast, IS compared via
  `f.rel_path == _GOVERNANCE_KNOWN_ISSUES_DOC` (line 142) inside
  `discover_canonical_docs()`, against files found via
  `discover_md_files(DOCS_DIR, prefix="")` (line 137) — this DOES depend on
  seq 01 having landed first, since `DOCS_DIR` stays the flat root and
  `rel_path` only becomes directory-qualified once the glob is recursive.
- `tests/tools/test_check_known_deviation_sync.py` is confirmed hermetic (its
  own docstring states live `docs/`-tree validation is out of scope for that
  file) — no test change needed for this document.

## Design decisions

- Two independent constant updates in one file, each with a different
  dependency profile (see Assumptions) — `ADR_DIR` can be updated and become
  correct as soon as the physical ADR move lands, independent of seq 01;
  `_GOVERNANCE_KNOWN_ISSUES_DOC` additionally depends on seq 01.

## Alternatives considered

- N/A: both changes are direct constant-value updates with no viable
  alternative approach given the established pattern from seq 03/04.

## Implementation

### Target file

`tools/check_known_deviation_sync.py`

### Procedure

1. Locate `ADR_DIR = DOCS_DIR / "adr"` (line 45).
2. Change it to `ADR_DIR = DOCS_DIR / "10_adr"`.
3. Locate `_GOVERNANCE_KNOWN_ISSUES_DOC = "00_governance_03_issue-and-uncertainty-management.md"`
   (line 61).
4. Change its value to
   `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.

### Method

Two `Edit` calls, each a one-line constant-value update.

### Details

Current:
```python
ADR_DIR = DOCS_DIR / "adr"
...
_GOVERNANCE_KNOWN_ISSUES_DOC = "00_governance_03_issue-and-uncertainty-management.md"
```

After modification:
```python
ADR_DIR = DOCS_DIR / "10_adr"
...
_GOVERNANCE_KNOWN_ISSUES_DOC = "00_governance/00_governance_03_issue-and-uncertainty-management.md"
```

## Compatibility considerations

- `_GOVERNANCE_KNOWN_ISSUES_DOC`'s correctness depends on seq 01 landing
  first (see Assumptions); `ADR_DIR`'s does not.
- Not wired into pre-commit or the CI workflows inspected for this Plan —
  low blast radius (confirmed during the source Plan's Affected areas
  analysis).

## Security considerations

No security impact.

## Rollback considerations

1. Revert `ADR_DIR` and `_GOVERNANCE_KNOWN_ISSUES_DOC` to their original
   values independently (they have no interdependency).
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`
(confirmed hermetic — should pass unchanged, since it never exercises
`discover_adr_docs()`/`discover_canonical_docs()` against the real `docs/`
tree per its own docstring).

## Completion criteria

- `ADR_DIR` equals `DOCS_DIR / "10_adr"`.
- `_GOVERNANCE_KNOWN_ISSUES_DOC` equals
  `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.
- `uv run pytest tests/tools/test_check_known_deviation_sync.py -q` passes
  unchanged.

## Out of scope

- `DOCS_DIR`'s own value.
- The cross-check/parsing logic once documents are found.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-161235 | 20260923-161235 | Step3 stale_detector false-positive ('docs_dir', a common variable name) confirmed as noise, bypassed. ADR_DIR and _GOVERNANCE_KNOWN_ISSUES_DOC both updated. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-161235 | 20260923-161235 | No test change needed; test_check_known_deviation_sync.py confirmed hermetic, 7 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-161235 | 20260923-161235 | ruff/mypy/bandit pass. pytest: 7 passed. Direct tool run against real (pre-move) tree: exit 0 but silently reports 'No issues found' instead of the 18 pre-existing WARNINGs it reported before this change -- unlike seq03/seq04's tools, this one has no explicit 'target not found' error path, so discover_canonical_docs()/discover_adr_docs() returning empty lists (since docs/00_governance/ and docs/10_adr/ don't exist yet) silently yields zero issues rather than erroring. This is a pre-existing design limitation of this tool (not introduced by this change) that will self-resolve once docsreorg05/docsreorg11 land; out of this Plan's REQ-006 scope to fix. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-161235 | 20260923-161235 | N/A: no docs/00_index.md task-scope mapping for tools/check_known_deviation_sync.py. |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_known_deviation_sync.py