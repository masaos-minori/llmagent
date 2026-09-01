## Goal
Add `tests/tools/test_rename_doc.py` covering a simple multi-file rename, the
opt-in title-rewrite flag, and non-link prose reporting, using fixture `docs/`-like
directories (REQ-008).

## Scope
- In scope: unit tests T1-T5 as defined in the Plan's Tests section, exercising
  `tools/rename_doc.py`'s move, link-rewrite, title-rewrite, prose-reporting, and
  dry-run/apply behavior against fixture directories (not the live `docs/` tree).
- Out of scope: testing reference-style `[ref]: path` link definitions (UNK-01,
  not observed in the current corpus); testing ADR-ID renaming (UNK-03, out of
  this Plan's scope).

## Assumptions
- `tools/rename_doc.py` (seq 01 of this Plan) exposes its scanner/rewriter logic
  as importable functions, not only as a CLI `main()`, so tests can assert on
  planned-rewrite data structures directly.
- Fixture directories are built under `tmp_path`, with a `docs/`-equivalent root
  and, for the `git mv` assertion, an initialized fixture git repository (since
  `git mv` requires a git-tracked file).

## Design decisions
- T1 (multi-file rename) includes at least one fixture file using the
  bare-filename link convention and one using the `../`-prefixed convention, per
  the Plan's Risks mitigation for the bare-vs-`../`-prefixed split — this
  directly tests the per-file style-preservation behavior, not just that a
  rewrite occurred.
- T4 (`--dry-run` vs `--apply`) asserts on file contents unchanged after
  `--dry-run`, then on file contents changed identically to the `--dry-run`
  report after `--apply` — proving the two modes report the same planned
  changes.

## Alternatives considered
- Running tests against the live `docs/` tree: rejected — the Plan's Scope
  explicitly requires fixture `docs/`-like directories, to keep tests
  independent of the live tree's actual content and avoid mutating real
  documentation during test runs.

## Implementation
### Target file
`tests/tools/test_rename_doc.py`

### Procedure
1. **T1** (REQ-001, REQ-002): build a fixture `docs/`-equivalent tree (git-
   initialized) with an old-path file and at least two referencing files — one
   using a bare-filename link, one using a `../`-prefixed link. Invoke the tool
   with `--apply`, and assert: the old path no longer exists, the new path
   exists via `git mv` (git status shows a rename), and each referencing file's
   link path is rewritten to the new path in its own original prefix style.
2. **T2** (REQ-003): using a fixture where a referencing file's link text
   duplicates the old title, invoke the tool with `--apply --old-title
   "..." --new-title "..."` and assert the adjacent link text is rewritten to
   the new title. Invoke the same fixture again without the title flags and
   assert the link text is left untouched (link path still rewritten).
3. **T3** (REQ-004): using a fixture file containing a non-link plain-prose
   mention of the old filename (outside any Markdown-link span), invoke the tool
   with `--apply` and assert: the mention is reported in the tool's output/
   return value, and the fixture file's prose text is unchanged (only its
   Markdown-link occurrences, if any, were rewritten).
4. **T4** (REQ-005): invoke the tool with `--dry-run` (default, no flag needed)
   against the T1 fixture and assert no file was written and no `git mv`
   occurred, while the reported planned changes match what `--apply` produces
   when run separately on an identical fresh copy of the fixture.
5. **T5** (REQ-006): invoke the tool with a `new-path`/rewrite-candidate
   argument crafted to attempt escaping the fixture's `docs/`-equivalent root
   (e.g. via a `..`-traversal path), and assert: non-zero exit / raised error,
   no write occurred anywhere, including outside the fixture root.

### Method
`pytest` test module using `tmp_path` for isolated, git-initialized fixture
`docs/`-equivalent directories; imports `tools.rename_doc`'s scanner/rewriter
functions directly (not via `subprocess`) for the assertion-heavy scenarios
(T1-T4), and may additionally invoke the CLI `main()` for T5's containment-
rejection assertion since that is fundamentally a CLI-argument-validation
concern.

### Details
- Each fixture's git repository needs at least one commit before `git mv` is
  attempted (a `git mv`-equivalent operation on an uncommitted file is not the
  scenario under test).
- T1's two referencing fixture files must use link syntax matching the two
  conventions confirmed in Reference Files:
  `docs/adr/ADR-005-rag-source-derived-index-relationships.md`'s bare-filename
  style and `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`'s
  `../`-prefixed style — reproduced as fixture content, not copied verbatim from
  the live files.
- T3's non-link prose fixture line must place the old filename mention outside
  any `[text](path)` span on that line (e.g. plain sentence text mentioning the
  filename), so the assertion distinguishes "found outside a link span" from
  "found inside a link's text or path".
- One test function per T1-T5 at minimum, each building its own isolated
  `tmp_path` fixture tree so no scenario's fixture state can affect another's
  assertions.

## Compatibility considerations
New test file; no existing test module imports it. Adding it does not change any
existing test's behavior.

## Security considerations
Tests use `tmp_path`-rooted git-initialized fixtures only — no writes outside
pytest's managed temporary directory, no network access. T5's containment-escape
attempt is itself a security-relevant test case, confirming the tool rejects
rather than permits a traversal attempt.

## Rollback considerations
New file only; rollback is deleting `tests/tools/test_rename_doc.py`. No other
test or module depends on it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_rename_doc.py` | Unit | `uv run pytest tests/tools/test_rename_doc.py -v` | All of T1-T5 pass |
| `tests/tools/test_rename_doc.py` | Regression | `uv run pytest tests/tools/ -v` | No new failures (note: `tests/tools/test_check_agent_docs_consistency.py` has a pre-existing, unrelated collection error — not this file's responsibility) |
| `tools/rename_doc.py` + this file | Coverage | `uv run coverage run -m pytest tests/`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% diff coverage on changed lines |

## Completion criteria
- `tests/tools/test_rename_doc.py` exists and covers T1 (multi-file rename with
  both link conventions), T2 (title-rewrite flag), T3 (non-link prose
  reporting), T4 (dry-run vs. apply parity), and T5 (`docs/`-containment
  enforcement).
- `uv run pytest tests/tools/test_rename_doc.py -v` passes with no failures
  (requires `tools/rename_doc.py` from seq 01 of this Plan to exist first).

## Out of scope
- Reference-style `[ref]: path` link definitions (UNK-01).
- ADR-ID renaming (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-155203 | 20260901-155203 | `tools/rename_doc.py` (seq 01) already existed; verified against current source before writing tests |
| 2 | Add or update tests per Validation plan | Completed | 20260901-155203 | 20260901-155203 | `tests/tools/test_rename_doc.py` created, covering T1-T5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-155203 | 20260901-155203 | ruff format/check + mypy clean; `pytest tests/tools/test_rename_doc.py -v` 5/5 passed; `pytest tests/tools/ -v --continue-on-collection-errors` 83 passed, 1 pre-existing unrelated collection error (`test_check_agent_docs_consistency.py`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-155203 | 20260901-155203 | N/A: no `docs/00_index.md` task-scope row matches `tests/tools/test_rename_doc.py` |

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
- **Source issue**: `issues/20260831-194739_tool005_rename_doc_and_update_references.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111505_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114954
- **Related target files**: `tests/tools/test_rename_doc.py`
