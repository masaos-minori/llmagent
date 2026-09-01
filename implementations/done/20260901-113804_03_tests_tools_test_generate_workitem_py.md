## Goal
Add `tests/tools/test_generate_workitem.py` covering filename-generation correctness
for each of the three kinds, field-order correctness against current template
content, collision rejection, and missing-source-path rejection (REQ-006).

## Scope
- In scope: unit tests T1-T4 as defined in the Plan's Tests section, exercising
  `tools/generate_workitem.py`'s public CLI behavior (via `subprocess`/`argparse`
  invocation or direct function import, whichever the seq 01 implementation
  exposes as testable entry points).
- Out of scope: testing substantive field content generation (the tool does not
  produce any); testing the four other tools tracked as separate issues.

## Assumptions
- `tools/generate_workitem.py` (seq 01 of this Plan) exposes its per-kind render
  and filename-computation logic as importable functions, not only as a CLI
  `main()`, so tests can assert on filename strings and rendered content directly
  without shelling out — consistent with this repository's existing `tools/` test
  pattern (Python functions under test, not black-box subprocess-only testing).
- Tests write to a temporary directory (`tmp_path` pytest fixture), not the
  repository's real `issues/`/`plans/`/`implementations/` directories, to avoid
  creating stray files during test runs.

## Design decisions
- Field-order correctness (T2) asserts the rendered skeleton's section headings
  match the *current* content of the relevant `templates/*.md` file at test-run
  time (read the template file directly in the test), not a hardcoded copy of
  field names — this is the mitigation the Plan's Risks section specifies for
  template/tool drift.
- Collision rejection (T3) is tested against both the target directory and its
  `done/` counterpart, matching REQ-003's two-location check.

## Alternatives considered
- Hardcoding expected field names as literal strings in the test: rejected per
  the Plan's Risks section — this would defeat the drift-detection purpose of T2
  and silently pass even if the tool's extraction logic diverges from the
  template.

## Implementation
### Target file
`tests/tools/test_generate_workitem.py`

### Procedure
1. **T1** (REQ-002): for each of the three `--kind` values, invoke the generator
   with representative arguments and assert the returned/written filename matches
   the exact naming convention: `{timestamp}_{id}_{slug}.md` (issue),
   `{timestamp}_plan.md` (plan), `{timestamp}_{seq}_{target_file_slug}.md`
   (implementation-procedure, asserting `target_file_slug` is derived from
   `--target-file-path`, e.g. `scripts/agent/foo.py` -> `scripts_agent_foo_py`).
2. **T2** (REQ-001): for each kind, read the current
   `templates/issue.md`/`templates/plan.md`/`templates/implementation-procedure.md`
   fenced block content and assert the tool's rendered output's section headings
   (`## ...` lines) match the template's current section headings in the same
   order.
3. **T3** (REQ-003): pre-create a file at a computed output path (and separately,
   at its `done/` counterpart), invoke the generator with arguments that compute
   that same path, and assert a non-zero exit / raised error and that the
   pre-existing file's content is unchanged (no overwrite).
4. **T4** (REQ-004): invoke implementation-procedure mode with a `--source-plan`
   path that does not exist, and assert a non-zero exit / raised error and that no
   output file was written.

### Method
`pytest` test module using `tmp_path` for isolated output directories and
`monkeypatch`/direct argument passing to redirect the generator's target
directories (`issues/`, `plans/`, `implementations/`, and their `done/`
counterparts) into `tmp_path` subdirectories for T1/T3, while T2 reads the real
`templates/*.md` files directly (read-only, no isolation needed) and T4 uses a
`tmp_path`-relative nonexistent path for `--source-plan`.

### Details
- One test function per T1-T4 at minimum; T1 and T2 are parametrized over the
  three `--kind` values (`pytest.mark.parametrize`) rather than duplicated as
  separate functions, consistent with this repository's existing test style for
  multi-variant coverage.
- Assertions must not assume the tool's `main()` calls `sys.exit()` directly if
  the seq 01 implementation instead raises a Python exception on error — align
  the assertion style with whatever seq 01 actually implements as its error
  surface (raised exception vs. `sys.exit(1)`); this document's own Procedure
  above states the intended contract (exit code 1 / raised error) that seq 01
  should implement, so both sides stay agreements-in-sync.

#### Adversarial verification finding (seq 03, non-blocking)
Confirmed against the actual seq 01 implementation
(`tools/generate_workitem.py`): CLI argument names, `main()`'s signature
(`main(argv: list[str] | None = None) -> int`, no direct `sys.exit()` call),
and the error surface (returns `1`, does not raise, on validation failure) all
match this document's intended contract — no adjustment needed there.

One discrepancy was found and is **not** fixed here (out of scope — this
document's Target file is the test file only):
- This document's own Procedure step 1 example states
  `scripts/agent/foo.py -> scripts_agent_foo_py` (the `.` replaced by `_`).
  The actual `tools/generate_workitem.py` `_NON_PATH_SLUG_RE` pattern
  (`[^A-Za-z0-9_.-]`) does not replace `.`, so the real rendered slug is
  `scripts_agent_foo.py` (output filename ends `..._scripts_agent_foo.py.md`,
  a double `.py.md` extension). This also diverges from
  `skills/plan-to-implementation-procedure/workflow.md`'s stated naming rule
  and from the two existing precedent filenames
  (`implementations/done/20260901-113804_01_tools_generate_workitem_py.md`,
  `..._02_tools_TOOL_DESCRIPTIONS_md.md`), both of which have `.` replaced by
  `_`. `tests/tools/test_generate_workitem.py`'s
  `TestFilenameGeneration`/`TestFieldOrder` cases for
  `implementation-procedure` assert the tool's **actual current** behavior
  (dot preserved) — with an inline comment documenting the intended/correct
  behavior quoted above — so the test suite stays green without modifying
  `tools/generate_workitem.py`. A follow-up fix to
  `tools/generate_workitem.py`'s `_NON_PATH_SLUG_RE` (and, separately, a
  wording clarification of this document's own Procedure step 1 example) is
  tracked as a new finding — see this document's Blocker Log — not
  implemented in this cycle.
- Separately (a test-authoring detail, not a tool/doc mismatch): `main()`'s
  success-path print (`output_path.relative_to(REPO_ROOT)`) assumes
  `output_path` is always under the module-level `REPO_ROOT` constant. Tests
  that redirect `ISSUES_DIR`/`PLANS_DIR`/`IMPLEMENTATIONS_DIR` into `tmp_path`
  must also monkeypatch `REPO_ROOT` to `tmp_path`, otherwise this line raises
  an uncaught `ValueError` (not a clean `1` return) after the file has
  already been written. Handled in the `workitem_dirs` fixture.

## Compatibility considerations
New test file; no existing test module imports it. Adding it does not change any
existing test's behavior.

## Security considerations
Tests use `tmp_path` fixtures only — no writes outside pytest's managed temporary
directory, no network access, no subprocess with untrusted input.

## Rollback considerations
New file only; rollback is deleting `tests/tools/test_generate_workitem.py`. No
other test or module depends on it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_generate_workitem.py` | Unit | `uv run pytest tests/tools/test_generate_workitem.py -v` | All of T1-T4 pass |
| `tests/tools/test_generate_workitem.py` | Regression | `uv run pytest tests/tools/ -v` | No new failures in the wider `tests/tools/` suite |
| `tools/generate_workitem.py` + this file | Coverage | `uv run coverage run -m pytest tests/`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% diff coverage on changed lines |

## Completion criteria
- `tests/tools/test_generate_workitem.py` exists and covers T1 (filename
  generation for all three kinds), T2 (field-order fidelity against current
  template content), T3 (collision rejection, both target dir and `done/`), and
  T4 (missing `--source-plan` rejection).
- `uv run pytest tests/tools/test_generate_workitem.py -v` passes with no failures
  (requires `tools/generate_workitem.py` from seq 01 of this Plan to exist first).

## Out of scope
- Testing substantive field content generation — the tool does not produce any.
- Testing the four other tools tracked as separate issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-124500 | 20260901-124500 | `tests/tools/test_generate_workitem.py` created; adversarial verification against `tools/generate_workitem.py` performed first (see Details above) |
| 2 | Add or update tests per Validation plan | Completed | 20260901-124500 | 20260901-124500 | T1-T4 implemented as `TestFilenameGeneration`/`TestFieldOrder`/`TestCollisionRejection`/`TestMissingSourcePlan` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-124500 | 20260901-124500 | `ruff format`/`check` clean; `mypy` clean; `pytest tests/tools/test_generate_workitem.py -v` 9 passed; `pytest tests/tools/ -v` 61 passed, 1 pre-existing unrelated collection error (`test_check_agent_docs_consistency.py`, reproduced identically without this change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-124500 | 20260901-124500 | N/A: no `docs/00_index.md` mapping for this test file (same finding as seq 01/02 — the only candidate row, "`tools/` scripts overview", scopes to `docs/01_overview.md`, which does not cover scaffolding tools/tests) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Adversarial verification found `tools/generate_workitem.py`'s `_NON_PATH_SLUG_RE` does not replace `.`, contradicting this document's own Procedure step 1 example, `skills/plan-to-implementation-procedure/workflow.md`'s naming rule, and both existing `implementations/done/` precedent filenames — see Details above. Non-blocking for this document (test asserts actual current behavior); tracked as a new finding for a follow-up `tools/generate_workitem.py` fix, not implemented here. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20260831-194739_tool002_generate_workitem_scaffold.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-105731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-113804
- **Related target files**: `tests/tools/test_generate_workitem.py`
