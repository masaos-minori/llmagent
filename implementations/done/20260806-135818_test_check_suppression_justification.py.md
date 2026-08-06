# Implementation: tests/tools/test_check_suppression_justification.py (new) — Phase 3: test coverage for the new enforcement tool

## Goal

Provide unit test coverage for `tools/check_suppression_justification.py` so its
pass/fail logic (code presence + em-dash justification, per suppression kind, plus
allowlist pass-through) is verified before the corresponding `.pre-commit-config.yaml`
hook is enabled.

## Scope

**In-Scope:**
- New test file `tests/tools/test_check_suppression_justification.py`, modeled on
  `tests/tools/test_check_no_compat.py`'s structure (synthetic-content tests via
  `tmp_path`, no references to real repo files as fixtures).
- Cover, per the plan's explicit test-case list: bare `noqa` (fail), `noqa` with code but
  no em-dash (fail), `noqa` with code and em-dash (pass); same three cases for
  `type: ignore` and `nosec`; and an allowlisted pre-existing line (pass-through).
- Cover the multi-line/parenthesized-import noqa style already present in the codebase
  (e.g. `scripts/agent/commands/cmd_config.py` lines ~43-45) as a synthetic fixture,
  per the plan's explicit risk mitigation requirement — this must be exercised *before*
  the hook is wired into `.pre-commit-config.yaml`.

**Out-of-Scope:**
- `tools/check_suppression_justification.py` itself — separate implementation procedure.
- Integration-level testing via actual `pre-commit run` — covered by the
  `.pre-commit-config.yaml` procedure's validation plan, not by this unit test file.
- Testing against real repo files — per the `check_no_compat.py` test precedent, all
  fixtures are synthetic (`tmp_path`-based), not references to real source files.

## Assumptions

- `tests/tools/test_check_no_compat.py` is the confirmed structural precedent: imports
  the checked-in `DEFAULT_ALLOWLIST`/`check_compat_patterns`-equivalent functions
  directly from `tools.check_no_compat`, writes synthetic content to `tmp_path` files,
  and asserts on the returned issue list (empty vs. non-empty).
- The new tool's public functions (exact names TBD at implementation time, but expected
  to mirror `check_no_compat.py`'s shape: a per-line/per-file check function returning
  `list[str]`, plus the allowlist set/type) are importable from
  `tools.check_suppression_justification` the same way
  `from tools.check_no_compat import (COMPAT_PATTERNS, check_compat_patterns)` works
  today.
- Test class/function naming follows the existing `test_check_no_compat.py` convention
  (`class TestX: def test_y(self, tmp_path: Path) -> None:` with `@pytest.mark.parametrize`
  used for the repeated code/em-dash presence-matrix cases).

## Design decisions

- Parametrize the 3-kind x 3-state matrix (bare / code-only / code+em-dash) using
  `pytest.mark.parametrize`, mirroring `test_check_no_compat.py`'s existing
  `TestPatternDetection.test_new_pattern_detected_in_synthetic_string` parametrization
  style, rather than writing 9 separate test methods — reduces duplication while keeping
  each case individually identifiable in failure output.
- Keep the allowlist pass-through test and the multi-line-import fixture test as distinct,
  named test methods (not parametrized) since they exercise different code paths
  (allowlist lookup vs. multi-line comment parsing) rather than the same
  code/em-dash matrix.

## Alternatives considered

- Testing against real files under `scripts/`/`tests/` (e.g. asserting specific existing
  lines pass/fail) — rejected: `test_check_no_compat.py`'s precedent uses only synthetic
  `tmp_path` fixtures, avoiding brittleness as real files change over time; the plan's
  test-case list is phrased in terms of synthetic categories (bare/partial/justified/
  allowlisted), not specific file references.

## Implementation

### Target file
`tests/tools/test_check_suppression_justification.py` (new)

### Procedure
1. Create the test file with a module docstring following the
   `tests/tools/test_check_no_compat.py` header convention.
2. Import the relevant public names from `tools.check_suppression_justification` (finalized
   once that module's implementation lands — see its procedure document).
3. Implement the parametrized bare/code-only/code+em-dash matrix for each of `noqa`,
   `type: ignore`, `nosec` (9 cases total, or fewer if parametrization collapses
   equivalent cases).
4. Implement one allowlist pass-through test: synthetic file path added to a test-local
   allowlist set, containing an otherwise-failing line, asserting zero issues returned.
5. Implement one multi-line/parenthesized-import fixture test using content shaped like:
   ```python
   from shared.config_loader import (  # noqa: PLC0415
       _BASE_CONFIG_FILES,
       ConfigLoader,
   )
   ```
   asserting this is correctly flagged as a violation (code present, no em-dash) — not
   silently ignored due to the multi-line parenthesized form, and not a false crash/
   parse error.
6. Do not implement yet — this is a document-only phase; actual file creation happens at
   `prompts/03_implementation.md` time.

### Method
`pytest` unit tests, `tmp_path` fixtures, `pytest.mark.parametrize` — consistent with the
existing `tests/tools/test_check_no_compat.py` style; no new test dependency.

### Details
- Per plan Implementation Steps Phase 3, bullet 2 (verbatim intent): "Add
  `tests/tools/test_check_suppression_justification.py` covering: bare noqa (fail), noqa
  with code but no em-dash (fail), noqa with code and em-dash (pass), same three cases
  for `type: ignore` and `nosec`, and an allowlisted pre-existing line (pass-through)."
- Per plan's stated Risk/Mitigation on false positives: "the accompanying test file ...
  must include a case exercising the multi-line/parenthesized-import noqa style already
  present in the codebase (e.g. `scripts/agent/commands/cmd_config.py` lines 43-45)
  before the hook is wired into `.pre-commit-config.yaml`."
- Test discovery path `tests/tools/` matches the existing sibling files
  `test_check_no_compat.py`, `test_check_mcp_docs_consistency.py`,
  `test_check_agent_docs_consistency.py` — no new `tests/` subdirectory needed.

## Compatibility considerations

- New test file, additive only; no impact on existing test collection or fixtures.

## Security considerations

N/A — test code only, no production security surface.

## Rollback considerations

- Additive new file; rollback is deletion with no other file depending on it.

## Validation plan

- `uv run pytest tests/tools/test_check_suppression_justification.py -v` — all cases
  pass.
- `uv run pytest tests/tools/ -v` — confirm no collection or fixture collision with
  sibling test files in the same directory.
- `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — this test
  file plus `tools/check_suppression_justification.py` together should keep the new
  code's diff-scoped coverage at or above the 90% gate (per plan Validation Plan row: "≥
  90% on changed lines (mainly the new `tools/check_suppression_justification.py`)").

## Out of scope

- `tools/check_suppression_justification.py` implementation — separate procedure.
- `.pre-commit-config.yaml` wiring — separate procedure.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-133908_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-135818
- Related target files: tests/tools/test_check_suppression_justification.py
