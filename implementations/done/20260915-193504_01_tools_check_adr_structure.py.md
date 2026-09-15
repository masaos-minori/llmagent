## Goal
Create `tools/check_adr_structure.py`, a new sibling to `check_adr_reference.py`/
`check_adr_invariant_matrix.py`, implementing two structural checks: (a) every
`docs/adr/*.md` file has a `## Known Deviations` heading, and (b) no ADR's
`## Implementation Notes` file/symbol list has drifted from its own
`### Implementation References`, per `REQ-001`, `REQ-002`, `REQ-003`.

## Scope
- In scope: the new script implementing checks (a) and (b), plus `--format
  json` matching `check_adr_reference.py`'s exact CLI shape.
- Out of scope: the four-way semantic classification (delete/promote/Known
  Issue/Needs Confirmation) — not automated by this or any check; registering
  the new hook in `.pre-commit-config.yaml`/documentation — covered by sibling
  procedures.

## Assumptions
- `tools/_docs_consistency_lib.py`'s `Issue` dataclass and `report_and_exit()`
  function are used as-is, matching `check_adr_reference.py`'s usage exactly.
- `discover_md_files(docs_dir, prefix="")` called with `docs_dir = REPO_ROOT /
  "docs" / "adr"` is used for file discovery, returning `DocFile` objects
  (`path`, `rel_path`, `lines`) — confirmed via reading `_docs_consistency_lib.py`
  that this shape fits directly.
- Check (b)'s section-boundary extraction (where `## Implementation Notes`/
  `### Implementation References` content ends) mirrors
  `check_adr_reference.py`'s own `_matrix_rows()`-style "stop at the next
  heading of level ≤ current" pattern, generalized to `^#{1,3} ` for ADR body
  sections (Implementation Notes is `##`, Implementation References is `###`
  under `## Related Documents`).

## Design decisions
- Check (a): for each `DocFile`, `re.search(r"^## Known Deviations", ...,
  re.MULTILINE)` against the joined content (or scan `lines` directly); if no
  match, emit one `ERROR`-severity `Issue(file=doc.rel_path, line_no=0,
  message="missing '## Known Deviations' heading")`.
- Check (b): for each `DocFile`:
  1. Locate `## Implementation Notes`'s line range (start = heading line,
     end = next line matching `^## ` or end of file).
  2. Within that range, extract every backtick-quoted path matching
     `` `((?:scripts|tests)/[^`]+\.\w+)` `` (a regex broader than
     `check_adr_reference.py`'s `scripts/[^`]+\.py`-only pattern, since Notes
     may cite `tests/*.py` too — confirm the exact extension set needed by
     re-reading a few already-cleaned ADRs' current Notes pointer lines before
     finalizing the regex, since most now read a plain-English pointer
     sentence with no backtick path at all).
  3. If step 2 finds zero paths, skip this ADR for check (b) entirely — no
     `Issue` emitted (per `REQ-002`'s explicit "no violation" rule for the
     now-common pointer-only state).
  4. Otherwise, locate `### Implementation References`'s line range the same
     way (start = heading line, end = next line matching `^#{1,3} ` or end of
     file) and extract the same path pattern from it.
  5. For every path found in Notes but absent from the References set, emit
     one `WARNING`-severity `Issue(file=doc.rel_path, line_no=<Notes path's
     line>, message="'{path}' appears in Implementation Notes but not in
     Implementation References — drift risk")`.
- `main()`/`render_json()`/argument parsing mirror `check_adr_reference.py`'s
  structure line-for-line (same `--format json` flag, same exit-code
  convention: `1` if any `ERROR`, `0` otherwise — `WARNING`-only findings do
  not fail the check, matching `report_and_exit()`'s own existing behavior).

## Alternatives considered
- Extend `check_adr_reference.py` in place instead of a new script — rejected
  per the source Plan's Design: that tool's own docstring scopes it to
  "matrix-named files only," narrower than "every ADR file."
- Require check (b)'s two lists to match exactly (byte-identical) — rejected
  per the source issue's own explicit instruction; only flag Notes-only paths
  (drift), not require symmetry.

## Implementation
### Target file
`tools/check_adr_structure.py`

### Procedure
1. Re-verify (idempotent recheck) `tools/check_adr_reference.py` and
   `tools/_docs_consistency_lib.py` are unchanged from this procedure's cited
   line numbers/signatures before copying their conventions.
2. Write the new module: module docstring (style matching
   `check_adr_reference.py`'s), imports (`argparse`, `re`, `sys`, `dataclasses`,
   `pathlib.Path`, `orjson`, the `sys.path.insert` shim for standalone
   execution, `from tools._docs_consistency_lib import Issue,
   discover_md_files, report_and_exit`), module-level constants (`REPO_ROOT`,
   `ADR_DIR = REPO_ROOT / "docs" / "adr"`).
3. Implement `check_known_deviations_heading(docs: list[DocFile]) ->
   list[Issue]` (check (a)).
4. Implement helper(s) to extract a named section's line range and its
   backtick-quoted paths, then `check_notes_references_drift(docs:
   list[DocFile]) -> list[Issue]` (check (b)).
5. Implement `collect_issues() -> list[Issue]` combining both checks'
   results, `render_json()`, and `main()` mirroring
   `check_adr_reference.py`'s exact shape.

### Method
Write the file directly (new file). Structure each function to be
independently unit-testable (accepting `list[DocFile]` or `list[str]` lines,
not doing file I/O itself except in `collect_issues()`), matching
`check_adr_reference.py`'s own `parse_matrix_source_refs()`/
`check_adr_reference()` separation — this is what makes
`tests/tools/test_check_adr_reference.py`'s direct-function-call pattern
possible, and the sibling test procedure
(`implementations/20260915-193504_02_tests_tools_test_check_adr_structure.py.md`)
depends on this same separation existing.

### Details
- Follow `rules/coding.md`: f-strings, English comments only, import order
  per ruff `I` rules.
- Do not import anything from `scripts/` — this is a `tools/` script, outside
  the `scripts/` import-boundary contract.
- Re-read a handful of already-cleaned ADRs' current `## Implementation
  Notes` pointer text (e.g. `docs/adr/ADR-001-workflow-engine-mandatory.md`,
  `docs/adr/ADR-005-rag-source-derived-index-relationships.md`) before
  finalizing the path-extraction regex, to confirm the "See Related Documents
  > Implementation References..." pointer sentences contain no backtick-quoted
  path themselves (they should not, since they were written as plain
  sentences) — this is what makes those ADRs correctly produce zero findings
  for check (b).

## Compatibility considerations
N/A: new, read-only checker script; no existing code imports or depends on
`tools/check_adr_structure.py` yet (the sibling `.pre-commit-config.yaml`
procedure is what wires it in).

## Security considerations
N/A: read-only file scanning, no subprocess/network/write operations.

## Rollback considerations
New file — revert by deleting it if validation fails; no other file depends
on its existence at this point in the cycle (registration happens in a later
row).

## Validation plan
- `uv run ruff format tools/check_adr_structure.py && uv run ruff check tools/check_adr_structure.py` — clean.
- `uv run mypy tools/check_adr_structure.py` — no errors (pass the path explicitly per `routing.md` "Adding a new tool").
- `uv run bandit tools/check_adr_structure.py` — no unaddressed findings.
- `uv run python tools/check_adr_structure.py` (manual smoke test against live `docs/adr/`) — expect exactly one `ERROR` (ADR-002) before the sibling ADR-002 procedure lands, zero after. Step 3a (code-implementation) adversarial verification, run against the live tree at implementation time, also found a genuine pre-existing `WARNING`: `ADR-004-environment-failure-handling-policy.md` cites `scripts/agent/shared/health_models.py` under Implementation Notes but that path is absent from Implementation References. This is not a bug in this check — it correctly detects a real, pre-existing drift the Plan's own AC-2 did not anticipate (AC-2 expected zero `WARNING` findings). `WARNING` severity does not fail `report_and_exit()`'s exit code, so this does not block the pre-commit hook; fixing ADR-004's own drift is out of this Plan's scope (only `ADR-002`'s missing heading, `REQ-008`, was in scope) and is left for a future cycle.
- `uv run python tools/check_adr_structure.py --format json` — valid JSON output matching the documented shape.
- Full test suite from the sibling test procedure must pass against this implementation (run after both are complete).

## Completion criteria
- Both checks are implemented as independently-callable functions accepting
  pre-loaded data (not requiring file I/O to unit-test).
- `--format json` matches `check_adr_reference.py`'s exact output shape.
- Manual smoke test against the live tree produces exactly the expected
  finding count per Validation plan.

## Out of scope
- `.pre-commit-config.yaml` registration, `docs/00_governance_04_documentation-checks.md`/`tools/TOOL_DESCRIPTIONS.md` documentation, and `docs/adr/ADR-002-config-isolation.md`'s fix — covered by sibling procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-194418 | 20260915-194418 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-194418 | 20260915-194418 | New tests are the sibling procedure's own responsibility; this row's own Validation plan covers lint/type/security/smoke-test only N/A: this row's own tests are covered by the sibling test procedure (02); this row's Validation plan covers lint/type/security/smoke-test only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-194418 | 20260915-194418 | This is a `tools/` addition — use `routing.md` "Adding a new tool"'s lighter sequence (this document's own Validation plan), not the full `scripts/` sequence ruff format/check, mypy, bandit all clean; smoke test found 1 ERROR (ADR-002, expected) + 1 pre-existing WARNING (ADR-004, see Validation plan note); --format json output valid |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-194418 | 20260915-194418 | N/A: documentation registration is the sibling procedures' responsibility N/A: documentation registration is the sibling procedures' responsibility |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 — implement checks (a) and (b) plus --format json
- **Source issue**: issues/done/20260914-124634_docqa05_adr-implementation-notes-lint-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-192743_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-193504
- **Related target files**: tools/check_adr_structure.py