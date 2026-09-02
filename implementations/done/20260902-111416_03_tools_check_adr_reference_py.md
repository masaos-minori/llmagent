## Goal
Fix `REQ-003`: create `tools/check_adr_reference.py`, which requires an inline `ADR-XXX`
reference comment only on files/functions already named by a `docs/adr-index.md` Invariant
Matrix row.

## Scope
Create exactly `tools/check_adr_reference.py` (new file). No other file is modified by this
row. This row was discovered missing from the Plan's `Implementation Target Files` table
during `plan-to-implementation-procedure` Step 3 (2026-09-02) — the Plan's own Implementation
steps already named this file for REQ-003, but no target-file row existed for it; the Plan
was corrected in the same cycle to add it (see the Plan's own Traceability history).

## Assumptions
- Only 3 files currently carry an inline `ADR-[0-9]{3}` reference comment
  (`scripts/agent/tool_policy.py`, `scripts/db/recovery.py`,
  `scripts/shared/tool_registry.py`, confirmed by the Plan's own Background grep) — there is
  no existing repository-wide convention; this check must derive its required-file list
  directly from `docs/adr-index.md`'s Invariant Matrix rows, not from a separately
  hand-maintained list (per the Plan's Implementation intent §3: "not a repository-wide
  mandate").
- An Invariant Matrix row "names" a file when a `path/to/file.py` (with or without `::test_name`)
  appears in its `Verification Status` cell — the same extraction this Plan's
  `tools/check_adr_invariant_matrix.py` (REQ-001, seq 01) performs. Reusing that extraction
  logic (rather than re-implementing it) avoids two divergent parsers reading the same
  table.

## Design decisions
Per `skills/DESIGN.md` Avoid implementation-reference duplication: derive the target-file
list from the same Invariant Matrix parsing this Plan's `check_adr_invariant_matrix.py`
(seq 01) already implements — either import/reuse its parsing function if it exposes one, or
duplicate only the minimal table-parsing logic if factoring out a shared helper is not
practical within this Plan's scope. Do not maintain the required-file list by hand.

## Alternatives considered
- A hand-maintained YAML/list of files requiring an ADR-reference comment: rejected — would
  drift from `docs/adr-index.md`'s matrix, the same class of staleness GV-014 exists to
  prevent, and duplicates a decision already made for `check_adr_invariant_matrix.py`.

## Implementation
### Target file
`tools/check_adr_reference.py`

### Procedure
Parse `docs/adr-index.md`'s Invariant Matrix to obtain the set of files it names; for each,
check whether the file contains an `ADR-[0-9]{3}` reference comment; fail (non-zero exit) if
a named file lacks one.

### Method
1. Confirm whether `tools/check_adr_invariant_matrix.py` (this Plan's seq 01 document)
   exposes its table-parsing logic as an importable function; if so, import and reuse it to
   get the set of files named by the matrix. If not (e.g. it was implemented as a
   self-contained script), factor the minimal parsing logic into a small shared helper both
   tools import, or duplicate only the table-locating/row-splitting logic (not the
   test-path-vs-code-reference distinction, which this check does not need).
2. For each named file, check for a line matching `ADR-[0-9]{3}` (reusing the existing
   pattern already implicitly used by the Plan's own Background grep,
   `rg 'ADR-[0-9]{3}' scripts/`).
3. Emit one issue per named file lacking the comment, following the existing
   `Issue`/`report_and_exit` pattern from `tools/check_known_deviation_sync.py` or
   `tools/_docs_consistency_lib.py`.

### Details
- Confirmed by reading `docs/adr-index.md`: the Invariant Matrix currently names test files
  (e.g. `tests/agent/test_startup.py`) more often than production `scripts/` files in its
  `Verification Status` cells — the three files with an existing ADR comment
  (`scripts/agent/tool_policy.py`, `scripts/db/recovery.py`,
  `scripts/shared/tool_registry.py`) are not all necessarily cited by file path in the
  matrix's cells as currently worded; confirming which matrix rows actually name a
  `scripts/*.py` path (vs. only a `tests/*.py::test_name` path) is required before this
  check's real target-file set is known — flag this as a `Needs confirmation` item for
  whoever implements this row if the matrix's current cells name few or no `scripts/*.py`
  paths directly, since the check would then have very little to enforce yet (matches
  ADR-004's own pattern of Known Deviations being reported when zero, not fabricated).
- No other Plan-level inconsistency was found for this row beyond its own late discovery
  (already corrected).

## Compatibility considerations
N/A: new file. Does not modify `docs/adr-index.md` or any existing `tools/*.py` file (beyond
a possible small shared-helper factoring in `check_adr_invariant_matrix.py`, which — if
needed — is a change to that file's own implementation procedure document, seq 01, not this
one; if a shared helper is needed, report it as an additional-target-file discovery per
`skills/plan-to-implementation-procedure/workflow.md` Step 3 rather than silently editing
seq 01's target file from this document).

## Security considerations
Read-only text scanning of `docs/adr-index.md` and named `scripts/`/`tests/` files; no
external input, no code execution.

## Rollback considerations
Trivially revertable: delete the new file. No other file references it until the
`.pre-commit-config.yaml` row is implemented.

## Validation plan
- `uv run python tools/check_adr_reference.py` against the current repository — expect zero
  false positives against files that already carry an ADR comment and confirm the actual
  set of currently-named `scripts/*.py` files (see Details) before treating a missing
  comment as a real failure.
- `uv run pytest tests/tools/test_check_adr_reference.py -v` — covers a named file with a
  comment (pass), a named file without one (fail), and a file not named by the matrix (not
  checked at all).

## Completion criteria
The tool flags only files the Invariant Matrix actually names and that lack an `ADR-[0-9]{3}`
comment; it does not impose a repository-wide requirement; it produces zero false positives
against current, correct content.

## Out of scope
`tools/check_adr_invariant_matrix.py`, `tools/check_compat_shims.py`,
`.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
`docs/00_governance_04_documentation-checks.md` — each covered by its own implementation
procedure document for this same Plan. Adding the missing ADR-004 comment to
`scripts/agent/startup.py` — a real gap this check correctly found, but not a file in this
Plan's frozen `Implementation Target Files` table (see Execution Status Blocker Log).

## Documentation
`tools/check_adr_reference.py` has no matching row in `docs/00_index.md`'s "Document
References by Task" table — no `docs/*.md` update applies (Step 5: `N/A: no
docs/00_index.md task-scope mapping for tools/check_adr_reference.py`). Step 6 content
checks skipped accordingly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Determine matrix-parsing reuse strategy vs. seq 01 | Completed | 2026-09-02 | 2026-09-02 | Chose local duplication of the small row-locating logic over importing seq 01's private `_matrix_rows()`, per the Needs Confirmation note this document already recorded — cross-tool private-function imports avoided |
| 2 | Confirm actual set of `scripts/*.py` files named by the matrix | Completed | 2026-09-02 | 2026-09-02 | `grep -oE` over `docs/adr-index.md` found exactly one full `scripts/<path>.py` reference (`scripts/agent/startup.py`, INV-011/ADR-004); all other `.py`-containing backtick spans are either bare filenames (`config_loader.py`, `http_augment.py`, `offsets.py`, ambiguous/unresolvable, out of scope by design) or `tests/*.py::test_name` node ids (a different check's concern). Scope narrowed accordingly to `scripts/` full paths only |
| 3 | Implement the check | Completed | 2026-09-02 | 2026-09-02 | **Important finding**: running the tool against the live repo found `scripts/agent/startup.py` does NOT currently contain an 'ADR-004' reference — a true positive (the check works correctly), not a bug. This is a genuine, pre-existing gap the check was built to catch. **Decision needed before seq 04 (`.pre-commit-config.yaml`) wires this check into pre-commit**: wiring it now would make `pre-commit run --all-files` fail immediately for every future commit until `scripts/agent/startup.py` gets its ADR-004 comment. Fixing that comment is a 1-line, well-precedented change (matching `scripts/agent/tool_policy.py`/`scripts/db/recovery.py`/`scripts/shared/tool_registry.py`'s existing convention) but is NOT a file in this Plan's frozen `Implementation Target Files` table — adding it would be an additional-target-file discovery per `skills/plan-to-implementation-procedure/workflow.md` Step 3. Not resolved in this row; flagged for the user/Plan owner before seq 04 proceeds |
| 4 | Add tests under `tests/tools/` | Completed | 2026-09-02 | 2026-09-02 | 7 tests, all pass: scripts-path extraction, test-node exclusion, bare-filename exclusion, malformed-ADR-column exclusion, file-with-reference (no issue), file-missing-reference (error), nonexistent-file (error) |
| 5 | Run against live repository | Completed | 2026-09-02 | 2026-09-02 | `uv run python tools/check_adr_reference.py` → 1 ERROR (`scripts/agent/startup.py` missing ADR-004 reference) — see Step 3's Notes; zero *false* positives (the detection logic itself is correct) |
| 6 | Validation | Completed | 2026-09-02 | 2026-09-02 | `ruff`/`mypy`/`bandit` clean on both new files |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Wiring this check into `.pre-commit-config.yaml` (seq 04) would fail on every commit until `scripts/agent/startup.py` gets an ADR-004 comment — a 1-line fix not in this Plan's frozen `Implementation Target Files` table | Yes — user explicitly authorized adding the comment (2026-09-02) | 2026-09-02 |

Resolution: added a 3-line comment citing "ADR-004 Decision #14" immediately above the `# 4. MCP tool discovery and validation` block in `scripts/agent/startup.py` (the exact block INV-011's Verification Status cell describes), matching the existing convention in `scripts/agent/tool_policy.py`/`scripts/db/recovery.py`/`scripts/shared/tool_registry.py`. `uv run python tools/check_adr_reference.py` now reports "No issues found." `ruff`/`mypy` clean (one pre-existing, unrelated `I001` import-sort warning confirmed present before this change too, via `git stash`); `bandit` unchanged (1 pre-existing Low). `tests/agent/test_startup.py` still shows the same pre-existing, unrelated failure (`TestStartupWorkflowPreflight::test_aborts_on_missing_workflow_schema`, documented in seq 01's Execution Status) — 71 passed, 1 failed, no new regression.
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (Scoped ADR-reference requirement)
- **Source issue**: `issues/20260901-183941_gv014ci_adr-compliance-ci-check-for-gv-014.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220712_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-111416
- **Related target files**: `tools/check_adr_reference.py`
