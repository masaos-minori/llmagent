# Plan: `check_docs_structure.py` — refuse glob patterns that match no files

## Goal
- Make `tools/check_docs_structure.py` exit non-zero with a message naming the unmatched glob
  pattern(s) whenever any supplied glob matches zero files, so a mistyped pattern can never
  produce a green "All checks passed" run that checked nothing.

## Priority
Medium

## Scope
- **In-Scope**: glob-match counting and the empty/partial match failure path in `main()` of
  `tools/check_docs_structure.py`; regression tests; `tools/TOOL_DESCRIPTIONS.md` entry update;
  `docs/00_governance/governance_04_documentation-checks.md` §8 update.
- **Out-of-Scope**: changing `MAX_SIZE` or any `SIZE_EXCEPTIONS` entry; changing which checks the
  tool performs or adding new checks; changing the CI workflow invocation; glob normalization that
  silently rewrites a pattern (e.g. `23_agent/*` into `docs/23_agent/*`).
- **Dependencies**: `plans/20261023-072425_plan.md` — closed (located at
  `plans/done/20261023-072425_plan.md`; its rows were corrected to the `docs/`-prefixed glob form).
  No open dependency.

## Background
Found while converting `plans/20261023-072425_plan.md` into implementation procedures on
2026-10-24: reproducing a Plan-cited checker finding with the pattern written relative to `docs/`
(`"23_agent/agent_13_*.md"`) produced exit 0 and "All checks passed" because the pattern matched
nothing. Re-verified on 2026-10-24: the run reproduces (exit 0, `All checks passed`);
`Path(".").glob` counts are 0 for the bad pattern, 1 for `docs/23_agent/agent_13_*.md`, 172 for
`docs/**/*.md`.

## Problem
`main()` resolves each supplied glob against `ROOT_DIR` (`tools/check_docs_structure.py`, glob
resolution block in `main()`), then prints `All checks passed` to stderr and returns 0 with no
count of how many files were checked (exit path at the end of `main()`). Any caller writing the
pattern relative to `docs/` instead of the repo root gets a green run that checked nothing.
Current CI invocations pass `docs/**/*.md`
(`.github/workflows/governance-docs-consistency.yml`, two invocations), so CI is not affected
today; the failure mode is local runs, procedures, and ad-hoc commands copied from documents.

## Reason for Change
The checker is the gate several procedures and plans cite as evidence. A green run that checked
zero files is indistinguishable from a green run that checked 172, so the evidence is not
trustworthy unless the empty-match case is refused.

## Implementation Intent
In `main()`, track which supplied patterns matched at least one file. After the normal per-file
validation output (unchanged), if any supplied pattern matched zero files, print a distinct message
naming the unmatched pattern(s) and return a non-zero exit code. Keep every other behavior — exit
codes for non-empty runs, stdout/stderr split, per-file finding format, and the
`docs/**/*.md` default — identical.

## Requirements
- `REQ-001`: `main()` reports unmatched glob patterns with a message of the form
  `no files matched the given glob(s): {patterns}` (stderr) and returns non-zero when at least one
  supplied pattern matches no file (including the all-patterns-empty case).
- `REQ-002`: Per-file findings from patterns that did match are still printed and counted exactly
  as today; the failure report is additive, not a replacement (mixed valid+invalid glob runs fail
  on findings and also report the unmatched pattern).
- `REQ-003`: Non-empty (all patterns matched) runs keep their current exit codes, output format,
  and the implicit `docs/**/*.md` default when no glob is given.
- `REQ-004`: Regression tests cover: zero-match globs (non-zero exit + message), one valid file
  (pass), and a mix of a valid and an invalid glob (failure on the valid file's findings plus the
  unmatched-pattern report); existing tests are untouched.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` and `docs/00_governance/governance_04_documentation-checks.md`
  state that an empty/partial match set is an error.

## Implementation Target Files
**Freeze status**: Frozen (validated 2026-10-24 per `rules/workflow-lifecycle.md` Implementation
Target Files Validation (Plan Freeze) — all rows `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_docs_structure.py` | Modify glob resolution and `main()` exit path | Add per-pattern match tracking and the unmatched-pattern failure message + non-zero return | REQ-001, REQ-002, REQ-003; AC-1, AC-2 | Reproduced 2026-10-24: `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` → exit 0, `All checks passed`; glob resolution block and exit path in `main()` read directly | `tests/tools/test_check_docs_structure.py` | Verified |
| `tests/tools/test_check_docs_structure.py` | Add regression tests | New tests for zero-match globs, one valid file, and mixed valid/invalid globs | REQ-004; AC-3 | File exists; imports `MAX_SIZE` (line 21) and `SIZE_EXCEPTIONS` (line 22) from `tools.check_docs_structure`; `TestCheckSizeExceptions` uses `next(iter(SIZE_EXCEPTIONS.items()))` (measured 2026-10-24) | this file | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update tool entry | The `check_docs_structure.py` entries must state that an empty match set is an error | REQ-005; AC-4 | Entry rows exist in the summary table and the detail table; neither mentions empty-match behavior (grep 2026-10-24) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Update §8 description and usage | §8 documents this checker's validation list and usage; the new failure mode must be stated there (Issue claimed no docs chapter describes the checker — corrected by verification) | REQ-005; AC-2, AC-4 | §8 "Documentation Structure Validation (`check_docs_structure.py`)" lists the checks and usage commands with no empty-match statement (read 2026-10-24) | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_content_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.github/workflows/governance-docs-consistency.yml` | Confirms the two CI invocations pass `docs/**/*.md` (non-empty match set, 172 files measured); the invocation must stay unchanged | `tools/check_docs_structure.py`; REQ-003 |
| `tools/run_validation_gates.py` | The `check_docs_structure` gate command carries the literal placeholder `[glob ...]`; `Gate.requires_context` / `run_gate()` classify such gates as `Not available` and never auto-invoke them, so the fix cannot make this gate fail | `tools/check_docs_structure.py`; REQ-003 |
| `tools/_front_matter_schema.py` | The only in-`tools/` import of `check_docs_structure.py` (grimp graph: no `tools/` module imports `check_docs_structure`; it imports `tools._front_matter_schema`); unmodified | `tools/check_docs_structure.py`; REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` exits
  non-zero and reports that no file matched the given glob.
- AC-2 (REQ-003, REQ-005): `uv run python tools/check_docs_structure.py "docs/**/*.md"` keeps its
  current behavior and reports no findings at HEAD (baseline measured 2026-10-24: exit 0,
  `All checks passed`, 172 files matched).
- AC-3 (REQ-004): `uv run pytest tests/tools/test_check_docs_structure.py -q` passes, including
  the new empty-match and mixed-glob cases.
- AC-4 (REQ-005): `uv run python tools/check_tool_descriptions_sync.py` reports no drift after the
  description update. (Issue AC-4 named `tools/check_tool_descriptions.py`; verified tool name is
  `tools/check_tool_descriptions_sync.py`.)

## Tests
- Unit test (REQ-001, REQ-004): zero-match glob → non-zero exit and stderr message naming the
  pattern.
- Unit test (REQ-003, REQ-004): one valid single-file glob → exit 0, `All checks passed`
  preserved.
- Unit test (REQ-002, REQ-004): mix of a valid glob (file with a structural finding) and an
  invalid glob → the run still fails on the valid file's finding and also reports the unmatched
  pattern.
- Regression (REQ-004): the existing test file (including `TestCheckSizeExceptions`, which reads
  `SIZE_EXCEPTIONS`/`MAX_SIZE` module constants) passes unchanged.
- Lint (REQ-001): `uv run ruff check tools/check_docs_structure.py` and
  `uv run ruff format --check tools/check_docs_structure.py` clean.

## Documentation Impact
Required, two entries, driven by REQ-005:
- `tools/TOOL_DESCRIPTIONS.md`: the `check_docs_structure.py` summary row and detail row state that
  an empty (or partial) match set is an error.
- `docs/00_governance/governance_04_documentation-checks.md` §8: the validation list/usage gains
  the empty-match refusal statement. Per `docs/00_index.md` the governance checker chapter is the
  owning chapter for this tool; no other docs chapter describes this checker's exit behavior.

## Assumptions
- The Issue's own stated assumption — a partially-matching set gets the same failure treatment as
  an all-empty set (fail, not warn) — is adopted as the plan's design decision (see Design). No
  contradicting repository evidence was found; the choice stays owner-revisable (UNK-01).
- The `check_docs_structure` gate row in `tools/run_validation_gates.py` keeps its `[glob ...]`
  placeholder command unchanged (verified `Not available` classification; no change needed).
- No new GV rule row is added to `governance_04`'s GV table: the empty-match refusal is an
  invocation-usage contract, not a docs-validation rule; the §8 prose and usage block carry it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Partial match (some globs match, some do not): fail vs warn. Issue states the fail assumption and asks to confirm it | No recorded owner decision beyond the Issue's assumption | Adopted as fail in this Plan's Design; owner may downgrade to warn during implementation without changing REQ-001 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_docs_structure.py` | Modify | Medium | 23 | High (single author, 90d git log) | not applicable (`tools/` has no deploy.sh copy line; deploy.sh syncs `scripts/`, `config/`, `schemas/`, `tests/`, `docs/`) |
| `tests/tools/test_check_docs_structure.py` | Modify | Low | 12 | High (single author, 90d git log) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 66 | High (single author, 90d git log) | not applicable (`tools/` has no deploy.sh copy line) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low | 63 | High (single author, 90d git log) | not applicable (rsynced) |

## Design
- **Task size**: classified Path A from the Issue's target list (3 files); reclassified Path B at
  inspection after adversarial verification showed a fourth modification target
  (`governance_04_documentation-checks.md` §8 — the Issue's "no `docs/` chapter describes this
  checker" claim is false). Path B analysis performed with available tools: grimp import graph
  (`pyan3`/`pydeps`/`ctags`/`git-fame` not available; `rg` and `git log` fallbacks used and
  recorded per `skills/DESIGN.md` Tool availability guard).
- **Architecture**: `tools/` is outside the `.importlinter` contracts (all contract
  `source_modules` are `scripts/` layer packages), so the change cannot violate a layer boundary.
  `check_docs_structure.py` is a CLI entry point (`main()` + `sys.exit`); its only in-`tools/`
  import is `tools._front_matter_schema`; no `tools/` module imports it. The only Python importer
  in the repository is `tests/tools/test_check_docs_structure.py` (`from tools.check_docs_structure
  import ...`).
- **Call sites**: CI passes `docs/**/*.md` (non-empty, 172 files); the `run_validation_gates.py`
  gate is placeholder-classified and never auto-run; `docs/` and `tools/TOOL_DESCRIPTIONS.md`
  references are prose. No runtime service, port, DB, or config dependency — `tools/` is not
  deployed. Operational inspection (`ss`, DB locks, `pip-audit`) not applicable: no service or
  dependency change.
- **Failure semantics (decision)**: after resolving all patterns, collect the unmatched pattern
  list. Run the normal per-file validation over the matched files exactly as today. Then, if the
  unmatched list is non-empty (covering both the all-empty and partial cases), print
  `no files matched the given glob(s): {patterns}` to stderr and return 1, in addition to any
  findings already emitted. One insertion point at the end of `main()`; no individual check is
  altered. The message names the unmatched patterns so the caller sees the mistake.
- **Default glob**: `docs/**/*.md` stays the implicit default when no glob is given (current
  behavior; CI and the governance-04 usage block depend on it).
- **Validation baseline** (recorded 2026-10-24): `radon cc tools/check_docs_structure.py` max
  grade A (complexity 3); `vulture scripts/ --min-confidence 80` → 3 pre-existing findings, all
  outside `tools/` (recorded, out of scope); `bandit -r scripts/ -c pyproject.toml` → Low 46,
  Medium 0, High 0; `diff-cover coverage.xml --compare-branch=master` on the existing
  2026-10-19 `coverage.xml` → "No lines with coverage information in this diff" (no measurable
  baseline). The implementation phase must regenerate coverage per `rules/toolchain.md` section 7
  and reach the ≥ 90% diff-cover threshold on changed lines.

## Implementation steps
1. **Phase 1: Failing regression tests first**
   - [ ] Add three tests to `tests/tools/test_check_docs_structure.py`: zero-match globs (non-zero
     exit + message naming the pattern), one valid single-file glob (pass preserved), and a mixed
     valid/invalid glob (fails on the valid file's finding and reports the unmatched pattern)
     (REQ-004; `tests/tools/test_check_docs_structure.py`). Expect these tests to fail against the
     current tool.
2. **Phase 2: Core logic — unmatched-glob failure in `main()`**
   - [ ] In `tools/check_docs_structure.py`, track which supplied patterns matched at least one
     file; after the existing per-file and ADR validation output, if any pattern is unmatched,
     print `no files matched the given glob(s): {patterns}` to stderr and return 1 (REQ-001,
     REQ-002, REQ-003; `tools/check_docs_structure.py`).
   - [ ] Run `uv run pytest tests/tools/test_check_docs_structure.py -q` — all tests pass
     (REQ-004).
3. **Phase 3: Documentation sync and verification**
   - [ ] Update the `check_docs_structure.py` summary and detail entries in
     `tools/TOOL_DESCRIPTIONS.md` to state the empty/partial-match error (REQ-005;
     `tools/TOOL_DESCRIPTIONS.md`).
   - [ ] Update §8 of `docs/00_governance/governance_04_documentation-checks.md` (validation list
     and usage) with the same statement (REQ-005;
     `docs/00_governance/governance_04_documentation-checks.md`).
   - [ ] Verification pass: AC-1/AC-2 invocations, `uv run python tools/check_tool_descriptions_sync.py`,
     docs gates required by `routing.md` for a `docs/*.md` edit (`check_docs_quality.py`,
     `check_docs_structure.py "docs/**/*.md"`, `check_docs_content_policy.py`), and the
     `rules/toolchain.md` sequence (`ruff format`/`check`, `mypy --no-namespace-packages scripts/`,
     `bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`,
     `uv run pytest`, coverage + diff-cover ≥ 90 on changed lines, `uv run pre-commit run
     --all-files`). Deploy step: not applicable — no `scripts/`/`config/` change; `tools/` has no
     deploy.sh copy line (`skills/deploy/SKILL.md` hand-off not needed).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_structure.py` | Unit (new tests) + manual CLI | `uv run pytest tests/tools/test_check_docs_structure.py -q`; `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"`; `uv run python tools/check_docs_structure.py "docs/**/*.md"` | New tests pass; bad glob exits non-zero naming the pattern; `docs/**/*.md` run keeps exit 0 / no findings |
| `tools/check_docs_structure.py` | Lint | `uv run ruff format --check tools/check_docs_structure.py`; `uv run ruff check tools/check_docs_structure.py` | Clean |
| `tests/tools/test_check_docs_structure.py` | Regression | `uv run pytest tests/tools/test_check_docs_structure.py -q` | Existing tests (`TestCheckSizeExceptions` included) pass unchanged |
| `tools/TOOL_DESCRIPTIONS.md` | Drift check | `uv run python tools/check_tool_descriptions_sync.py` | No drift |
| `docs/00_governance/governance_04_documentation-checks.md` | Docs gates | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py "docs/**/*.md"`; `uv run python tools/check_docs_content_policy.py` | No findings |
| Whole change | Full sequence | `rules/toolchain.md` sequence incl. `uv run pytest`, coverage + `diff-cover` ≥ 90%, `uv run pre-commit run --all-files` | No new failures; diff coverage ≥ 90% on changed lines |

## Risks
- **Risk**: all four target files are high-churn (23/12/66/63 commits in 30 days) with a single
  author (high bus factor) — concurrent edits could collide. → **Mitigation**: small, independently
  revertable steps; `plan-to-implementation-procedure` Step 2 revalidates every row against the
  current tree before generating procedures.
- **Risk**: CI/pre-commit relies on the tool's current exit-code contract. → **Mitigation**: CI
  invocations pass `docs/**/*.md` (match set of 172 files measured); REQ-003 and its tests pin the
  non-empty-run behavior.
- **Risk**: existing tests import `SIZE_EXCEPTIONS`/`MAX_SIZE` module constants directly. →
  **Mitigation**: change is scoped to `main()`'s glob resolution/exit path only; the whole existing
  test file is re-run as a regression item.
- **Risk**: `tools/run_validation_gates.py` names this checker with a `[glob ...]` placeholder
  command; a naive fix could make that gate fail. → **Mitigation**: verified — the gate is
  classified `Not available` (placeholder `requires_context`) and never auto-invoked; a mixed-glob
  regression test locks the failure semantics regardless.
- **Risk**: ad-hoc callers that relied on a vacuous pass (e.g. commands copied from documents with
  `docs/`-relative globs) start failing. → **Mitigation**: this is the issue's intent — the failure
  is explicit, names the pattern, and is documented in both tool-description locations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add failing regression tests (`tests/tools/test_check_docs_structure.py`) | Pending | — | — | REQ-004 |
| 2 | Phase 2: unmatched-glob failure path in `main()` (`tools/check_docs_structure.py`) | Pending | — | — | REQ-001, REQ-002, REQ-003 |
| 3 | Phase 3: docs sync (`tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`) + full validation pass | Pending | — | — | REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan generation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-214856
- **Related target files**: `tools/check_docs_structure.py`, `tests/tools/test_check_docs_structure.py`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem + Required Changes; reproduced exit 0 on 0-match glob (2026-10-24) | `tools/check_docs_structure.py` | Phase 2 | AC-1 | unit test: zero-match globs | Confirmed by repository evidence |
| REQ-002 | Testing Expectations (mixed glob case); `main()` output structure read 2026-10-24 | `tools/check_docs_structure.py` | Phase 2 | AC-1, AC-2 | unit test: mixed valid/invalid globs | Confirmed by repository evidence |
| REQ-003 | Constraints; CI invocation lines read 2026-10-24; baseline `docs/**/*.md` run exit 0 | `tools/check_docs_structure.py` | Phase 2 | AC-2 | unit test: one valid file; manual AC-2 invocation | Confirmed by repository evidence |
| REQ-004 | Required Changes + Testing Expectations; existing test file read 2026-10-24 | `tests/tools/test_check_docs_structure.py` | Phase 1, Phase 2 | AC-3 | `uv run pytest tests/tools/test_check_docs_structure.py -q` | Explicit in issue |
| REQ-005 | Documentation Impact (corrected: §8 of governance_04 exists); TOOL_DESCRIPTIONS entries read 2026-10-24 | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-4 | `uv run python tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| REQ-005 | §8 of governance_04 read 2026-10-24 (Issue claim "no docs chapter" disconfirmed) | `docs/00_governance/governance_04_documentation-checks.md` | Phase 3 | AC-4 | docs gates in Validation plan | Confirmed by repository evidence |
