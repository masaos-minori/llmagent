## Goal
- Bring the cost of scrubbing a long string through the content-pattern secrets masker (`mask_args` → `_mask_secrets`) from quadratic to near-linear in the input length, with byte-identical masking output for every input, so that `mask_args({"payload": "x" * 100_000}, [])` completes in under 1 s instead of about 67 s.

## Priority
Medium

## Scope
- **In-Scope**: fix the single superlinear pattern in `scripts/agent/secrets_masker.py` in place; add detection-parity tests against the pre-fix pattern; add a machine-speed-independent scaling regression check; record the per-pattern profile before and after as the change record; hand off to deploy.
- **Out-of-Scope**: adding, removing, or re-targeting secret patterns; changing where masking is invoked; changing the public names or signatures of `_mask_secrets`, `detects_secrets`, `SECRET_PATTERNS`, `mask_args`; excluding the slow test from runs; any change under `scripts/agent/tool_result_formatter.py` (the formatter only applies the masker).
- **Dependencies**: N/A: none (the Issue has no dependencies; no other active Plan targets these two files).

## Background
`tests/agent/test_tool_result_formatter.py::TestMaskArgsContentScrub::test_large_string_terminates` is the slowest test of the suite (67.4 s alone, 97.6 s inside an 8-way parallel run), and being one test it is the floor of the parallel wall time. `mask_args` applies `_mask_secrets` to every string leaf. `_mask_secrets` runs 14 case-insensitive regular expressions over the text. Six modules under `scripts/agent/` import the masker (`diagnostic_store.py`, `http_lifecycle_errors.py`, `http_lifecycle_health_checker.py`, `shared/retry_helper.py`, `startup_mcp_starter.py`, `tool_result_formatter.py`). `mask_args` itself is called from `tool_runner.py` (before logging), `tool_audit.py` (audit writes) and `tool_approval.py` (the masked approval preview, which runs before the user approves a call).

## Problem
One pattern, `SECRET_PATTERNS[13]` (the URL userinfo pattern that starts with the scheme class `[a-z][a-z0-9+.-]*` and requires `://`), scans the whole run of scheme characters from every start position and then fails for lack of `://`. Measured on `"x" * n`: 0.77 s at 5,000 characters, 2.5 s at 10,000, 9.7 s at 20,000 (each doubling costs about 4x). All other patterns together took under 0.05 s at 20,000, and none of ten further shapes (digit run, space run, keyword plus space run, `=` run, `.` run, JWT-prefix run, quote run) made another pattern slow. A long argument therefore delays the approval prompt and the audit write.

## Reason for Change
The cost is both the largest single entry of the test duration profile and a latency risk in production code on the approval and audit path. Fixing the pattern also removes the need to exclude the test from fast loops.

## Implementation Intent
Change `SECRET_PATTERNS[13]` in place so each match attempt starts only at the beginning of a run of scheme characters, and keep the matched text, the preserved prefix group and the masked group identical to the current pattern. Prove identical output with a parity test that keeps the pre-fix pattern as the reference. Pin the cost with a scaling check. Keep the pattern count at 14 and the public contract of `secrets_masker.py` unchanged.

## Requirements
- `REQ-001`: Record the per-pattern timing profile of `SECRET_PATTERNS` on long inputs before and after the change, identify the responsible pattern, and write the root cause in the change record (commit message).
- `REQ-002`: Make the scrub cost near-linear in input length for long runs of scheme characters by changing the responsible pattern in place, with identical masking output for every input; keep `len(SECRET_PATTERNS) == 14` and the signatures of `_mask_secrets` and `detects_secrets`.
- `REQ-003`: Add parity tests proving that the changed pattern and the pre-fix pattern produce identical output on the existing secret forms and on edge forms (leading digits or `+.-` before the scheme, scheme-less text, user-only and user-plus-password userinfo, no `@`).
- `REQ-004`: Add a regression check that fails when the scrub cost becomes superlinear again, without depending on machine speed.
- `REQ-005`: Scrubbing `"x" * 100_000` through `mask_args` completes in under 1 s on the development machine, and every existing test in `tests/agent/test_secrets_masker.py` and `tests/agent/test_tool_result_formatter.py` passes unchanged.
- `REQ-006`: Hand the change off to `skills/deploy/SKILL.md`, since a `scripts/` file changes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Owns detection; holds `SECRET_PATTERNS` and `_mask_secrets` | Rewrite `SECRET_PATTERNS[13]` so scanning starts only at the start of a scheme-character run (REQ-001, REQ-002, REQ-005, REQ-006; AC-001, AC-002, AC-005, AC-006) | REQ-001, REQ-002, REQ-005, REQ-006 / AC-001, AC-002, AC-005, AC-006 | `SECRET_PATTERNS[13]` is the only pattern slower than 0.01 s at 10,000 characters of `"x"`; 0.77 s, 2.5 s, 9.7 s at 5,000, 10,000, 20,000 (checked in Step 2); the module imports only `re` and is imported by six modules under `scripts/agent/` (checked in Step 3) | tests/agent/test_secrets_masker.py, tests/agent/test_tool_result_formatter.py, tests/agent/test_diagnostic_store_security.py | Verified |
| tests/agent/test_secrets_masker.py | Unit tests for the masker | Add the parity tests and the scaling regression check (REQ-003, REQ-004; AC-003, AC-004) | REQ-003, REQ-004 / AC-003, AC-004 | `test_pattern_count_matches_inventory` pins 14 patterns and `test_large_input_terminates` covers only a 10,000-character mixed payload with no cost bound (checked in Step 3); the file already imports `_mask_secrets` and holds the URL-credential cases (checked in Step 3) | tests/agent/test_secrets_masker.py | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/tool_result_formatter.py | `_mask_value` applies the masker to every string leaf and `mask_args` is the acceptance entry point; it stays unchanged | scripts/agent/secrets_masker.py / REQ-005 |
| tests/agent/test_tool_result_formatter.py | `test_large_string_terminates` is kept unchanged and is the end-to-end acceptance check | scripts/agent/secrets_masker.py / REQ-005 |
| tests/agent/test_diagnostic_store_security.py | Consumer of `detects_secrets`; must still pass | scripts/agent/secrets_masker.py / REQ-002 |
| scripts/agent/tool_approval.py | Calls `mask_args` for the approval preview before the user approves; read to state the latency risk | scripts/agent/secrets_masker.py / REQ-001 |
| docs/23_agent/agent_13_reference-api-generated.md | Generated reference table lists `detects_secrets` with its docstring; must not drift | scripts/agent/secrets_masker.py / REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): The change record (commit message) lists the per-pattern timings before and after on `"x"`, digit, space, and dot runs and names `SECRET_PATTERNS[13]` as the cause; after the change no pattern is superlinear on those shapes.
- `AC-002` (REQ-002): `len(SECRET_PATTERNS) == 14` holds; `_mask_secrets`, `detects_secrets`, `SECRET_PATTERNS`, and `mask_args` keep their names and signatures; every existing test in `tests/agent/test_secrets_masker.py`, `tests/agent/test_tool_result_formatter.py`, and `tests/agent/test_diagnostic_store_security.py` passes unchanged.
- `AC-003` (REQ-003): For the fixed secret forms and edge forms and for a deterministic generated corpus, the changed pattern and the pre-fix pattern give identical output; a differing case fails the test and names the input.
- `AC-004` (REQ-004): The scaling check passes after the change and fails when run against the pre-fix pattern (shown once before the fix is applied).
- `AC-005` (REQ-005): `mask_args({"payload": "x" * 100_000}, [])` completes in under 1 s (proposed threshold; the candidate pattern measured about 0.02 s) and returns the payload unchanged.
- `AC-006` (REQ-006): The last implementation step names `skills/deploy/SKILL.md` with its prerequisite (change committed and pushed first; deploying is the user's decision).

## Tests
- Parity tests (REQ-003): a parametrized test over fixed forms (URL with user and password, user only, no `@`, scheme-less text, leading digit or `+.-` before the scheme, uppercase scheme) and a seeded generated corpus over a small alphabet that includes `://`, `@`, `:`, `/`, digits, `+.-`, and letters; each compares the changed pattern's output with the pre-fix pattern kept in the test as the reference.
- Scaling regression check (REQ-004): runs the masker on a long letter run and a long digit run at two sizes, compares the best of several runs by ratio and bounds the absolute time with a margin of at least 50x over the measured post-fix time, so it does not depend on machine speed or on parallel load.
- Existing tests (REQ-002, REQ-005): `tests/agent/test_secrets_masker.py`, `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_diagnostic_store_security.py` unchanged.

## Documentation Impact
N/A: no `docs/` page states masking performance (a `docs/` search for performance terms near the masker found none, checked in Step 3). The generated reference table in `docs/23_agent/agent_13_reference-api-generated.md` stays correct as long as no docstring or signature changes (REQ-002); `uv run python tools/generate_reference_table.py --check` guards it.

## Assumptions
- The pattern can be rewritten in place with identical output. Falsifier: the parity test (AC-003) shows a differing input; then stop and report the trade-off instead of changing detection (Issue AI Implementation Instruction).
- The candidate shape (negative lookbehind on the scheme-character class, then optional leading non-letter scheme characters before the first letter) was checked outside the repository on 200,000 random strings with zero output differences and about 0.02 s at 100,000 characters; the implementation phase re-proves it through AC-003 in the repository.
- The 1 s threshold of AC-005 is kept as proposed; the candidate leaves a 50x margin.
- Docstrings and signatures of `_mask_secrets` and `detects_secrets` stay as they are, so the generated reference table does not drift.
- The full suite currently has three known failures in `tests/mcp_servers` (the mdq tests of `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md`); they are unrelated and are recorded as pre-existing when the full run is made.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an input shape beyond those profiled makes another pattern superlinear | Only letter, digit, space, keyword-plus-space, `=`, `.`, JWT-prefix, quote, and colon-plus-space runs were profiled | Re-run the per-pattern profile in Phase 3 on those shapes; a new finding is filed as a follow-up Issue, not fixed here (Out-of-Scope: patterns other than the responsible one) | False |
| UNK-02 | Realistic maximum size of a string argument in production | No measurement of production tool-call argument sizes | Not needed for acceptance (the fix removes the superlinear term); no action | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Modify | Medium (six importing modules; output unchanged by design) | N/A | N/A | not applicable (rsynced) |
| tests/agent/test_secrets_masker.py | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Cause: repeated start-position scanning by `SECRET_PATTERNS[13]`, not backtracking; a possessive quantifier would not help because every start position still scans to the end of the run.
- Rejected: bounding the scheme length (changes what is detected for long schemes); adding a pattern (breaks the pinned count of 14 and changes the inventory).
- Chosen direction: anchor each attempt to the start of a scheme-character run with a negative lookbehind, and allow leading digits and `+.-` before the first letter so the leftmost match start, and therefore the preserved prefix, stay as today. Alternative kept as a fallback only: a literal `"://"` pre-check in `_mask_secrets`; it removes the measured case but not a long run followed by `://`, so it is not sufficient alone.
- Responsibility boundary unchanged: `secrets_masker.py` owns detection; `tool_result_formatter.py` only applies it.
- Consumer scan (`tools/scan_change_consumers.py --seed SECRET_PATTERNS --seed _mask_secrets`): the six `scripts/agent/` modules and their tests are `not affected: output is identical by REQ-002`; `tests/agent/test_secrets_masker.py` is a target row; `tests/agent/test_diagnostic_store_security.py` and `docs/23_agent/agent_13_reference-api-generated.md` are reference rows; the ADR citation of `startup_mcp_starter.py::McpServerStarter` in `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` is `not affected: no masker behavior change`.
- Validation quality baseline (Step 5): `radon cc` on `scripts/agent/secrets_masker.py` gives `_mask_secrets` A (2) and `detects_secrets` A (1); `vulture scripts/ --min-confidence 80` reports 16 pre-existing unused-variable findings, none in the target file; `bandit -r scripts/ -c pyproject.toml` exits 0 with no medium or high findings. The diff-cover baseline is not run: the target files have no diff against `master` at plan time, so there are no changed lines to measure; the Plan keeps the 90% gate on changed lines (`rules/toolchain.md` Completion checklist).

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: Parity oracle**
   - [ ] Add the parity tests of REQ-003 to `tests/agent/test_secrets_masker.py`, keeping the pre-fix pattern text as the reference; they pass against the current code (REQ-003; tests/agent/test_secrets_masker.py)
2. **Phase 2: Core fix with its regression check**
   - [ ] Add the scaling regression check of REQ-004 and run it once against the unchanged pattern to show it fails (REQ-004; tests/agent/test_secrets_masker.py)
   - [ ] Rewrite `SECRET_PATTERNS[13]` in place per the Design and keep the pattern count at 14 (REQ-002; scripts/agent/secrets_masker.py)
   - [ ] Run the parity tests, the scaling check, and the existing masker and formatter tests (REQ-002, REQ-003, REQ-004, REQ-005; scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py)
3. **Phase 3: Verification and deployment hand-off**
   - [ ] Re-run the per-pattern profile on the shapes of UNK-01 and write the before and after timings and the root cause in the commit message (REQ-001; scripts/agent/secrets_masker.py)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed files and the full suite once (REQ-002, REQ-005; scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py)
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (REQ-006; scripts/agent/secrets_masker.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/secrets_masker.py | Unit: parity, scaling, and existing masker tests | `uv run pytest tests/agent/test_secrets_masker.py tests/agent/test_tool_result_formatter.py tests/agent/test_diagnostic_store_security.py -v` | All pass; `test_large_string_terminates` no longer the slowest test |
| scripts/agent/secrets_masker.py | Profile (not committed) | per-pattern `re.sub` timing on 100,000-character letter, digit, space, and dot runs | No pattern superlinear; total under 1 s |
| scripts/agent/secrets_masker.py | Static checks | `uv run ruff format scripts/agent/secrets_masker.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |
| scripts/agent/secrets_masker.py | Generated reference drift | `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_module_size.py` | Exit 0 |
| tests/agent/test_secrets_masker.py | Static checks | `uv run ruff check tests/agent/test_secrets_masker.py` | Clean |
| Both files | Full suite and coverage | `uv run pytest -m "not integration and not production_paths_allowed"`, then `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No new failures (the three mdq failures are pre-existing); at least 90% on changed lines |

## Risks
- **Risk**: The rewritten pattern masks a different set of strings (a secret becomes unmasked, or extra text gets masked) → **Mitigation**: the parity test compares output with the pre-fix pattern on fixed forms and a generated corpus; if equivalence cannot be shown, stop and report the trade-off.
- **Risk**: The scaling check is flaky under parallel load → **Mitigation**: best-of-several timing, a ratio bound well below the quadratic value, and an absolute bound with at least 50x margin; no machine-specific constant.
- **Risk**: A docstring or signature edit makes the generated reference table drift → **Mitigation**: leave them unchanged and run `generate_reference_table.py --check`.
- **Risk**: The masker is shared by six modules, so a hidden dependence on match offsets breaks one of them → **Mitigation**: only the replacement text (`group(1) + "***MASKED***"`) is used by `_mask_secrets`; the full suite runs once, covering the six modules' tests.
- **Risk**: The pre-fix pattern kept as the test reference goes stale if the pattern list changes later → **Mitigation**: the test comment states the reference is the pre-fix text and that it only guards this equivalence.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add the parity tests against the pre-fix pattern (tests/agent/test_secrets_masker.py) | Completed | — | 20261113-120527 |  |
| 2 | Phase 2: scaling regression check, then rewrite `SECRET_PATTERNS[13]` (tests/agent/test_secrets_masker.py, scripts/agent/secrets_masker.py) | Completed | — | 20261113-120527 |  |
| 3 | Phase 3: profile, validation sequence, full suite, deploy hand-off (scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-101952_01_scripts_agent_secrets_masker.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261113-101952_02_tests_agent_test_secrets_masker.py.md | 1, 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-183807_testspeed002_bound-secret-scrub-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-091430
- **Related target files**: scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (measure per pattern); Background; per-pattern profile (checked in Step 2) | scripts/agent/secrets_masker.py | Phase 3 | AC-001 | Validation plan: profile row | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (rewrite or guard); Constraints; `SECRET_PATTERNS[13]` profile | scripts/agent/secrets_masker.py | Phase 2 | AC-002 | Validation plan: unit tests and static checks rows | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (detection-parity cases); Testing Expectations | tests/agent/test_secrets_masker.py | Phase 1 | AC-003 | Tests: parity tests | Explicit in issue |
| REQ-004 | Issue Required Changes (regression check); Acceptance Criteria | tests/agent/test_secrets_masker.py | Phase 2 | AC-004 | Tests: scaling regression check | Explicit in issue |
| REQ-005 | Issue Acceptance Criteria (under 1 s; existing tests unchanged) | scripts/agent/secrets_masker.py | Phase 2, Phase 3 | AC-005 | Validation plan: unit tests and full suite rows | Explicit in issue |
| REQ-006 | `skills/issue-to-plan/workflow.md` Step 5 (deploy step for `scripts/` changes) | scripts/agent/secrets_masker.py | Phase 3 | AC-006 | Validation plan: static checks row | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-101952 -->