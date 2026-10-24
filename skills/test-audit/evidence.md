# Test Audit — Result Classification, Evidence Criteria, and Traceability IDs

Load this file at Step 0 (unconditionally). It covers the classification vocabulary
from Step 3 onward, the Step 4 evidence procedure, and the Steps 6-7 ID scheme.

---

## Result Classification

Classify every executed or attempted command using exactly one of these five results —
the vocabulary defined in `rules/ai-execution.md` Repository Tool Usage rule 11, used
consistently in Steps 2-4 and in `report-template.md`'s Report Template section `# 2`:

- **Pass** — ran to completion with no failures, and collected at least one test case
  (per `rules/ai-execution.md` Repository Tool Usage #8, a 0-collected, exit-0 run is
  not evidence of a passing suite — reclassify it as `Blocked` or `Not available` with
  the collection error as the reason instead).
- **Fail** — ran to completion with one or more failures.
- **Partial** — ran, but some sub-cases were skipped, xfail, or otherwise incomplete;
  state exactly what was skipped and why.
- **Not available** — cannot run in this environment as designed (e.g. requires a
  production-only resource with no safe local/emulated equivalent). A structural
  limitation, not a fixable blocker.
- **Blocked** — could run in principle, but a specific missing or unavailable
  environment, service, or credential currently prevents it. Record exactly what is
  missing.

`Not available` or `Blocked` MUST NOT be reported as `Pass`. An unexecuted or partially
executed check has no result other than one of the five above — MUST NOT infer `Pass`
from a similar command's success, from the absence of an error, or from partial output.

### Commands that were never executed

A command Step 2 did not clear (`safety.md`) is never run, but it still gets one Result
and appears in the report, so that nothing is silently dropped:

| Step 2 classification | Result in the report | Reason to record |
|---|---|---|
| `Blocked` | `Blocked` | the specific missing environment, service, or credential |
| `Not runnable` | `Not available` | the structural limitation |
| `Prohibited` | `Not available` | the Prohibited condition that applies |

---

## Evidence Criteria for Root Cause and Flaky Classification (Step 4)

MUST NOT classify a failure's determinism or root cause from a single run or from
intuition. Apply this evidence procedure for every `Fail` result from `workflow.md`
Step 3.

### Deterministic vs. flaky

- Re-run the failing test in isolation at least 3 times, or use the repository's own
  flaky-detection tooling if one is configured (e.g. `pytest-rerunfailures`) — the
  repository-defined tool SHOULD be preferred over a manual loop when one exists. When
  using such a tool, record each attempt's result, not only the final one.
- When `pytest-randomly` is active (the pytest header shows `Using --randomly-seed=N`),
  the test order changes every run. Also re-run the failing test with the same seed
  recorded in Step 3 (`--randomly-seed=N`) and once with `-p no:randomly`.
- All runs fail identically (same assertion/exception) → `Deterministic`.
- Results vary across runs → `Flaky`; record the observed ratio (e.g. "failed 2/3
  runs") as evidence.
- Fails only under the recorded seed, or only with randomization → `Flaky
  (order-dependent)`; record the seed as evidence.
- Only a test that failed in Step 3 is re-run here. A flaky test that passed in Step 3
  is not detected by this audit; state that limit under `# 9` of the report.
- If re-running is unsafe or not possible (the test is `Blocked`/`Not runnable` above)
  → `Flaky determination: Needs confirmation` — MUST NOT guess.

### Root cause

- Classify as one of: production code bug / test code bug / environment or setup
  issue / needs confirmation.
- A classification other than "needs confirmation" requires a cited concrete location
  (function, method, or config key — see `skills/DESIGN.md` No source-code line
  numbers) that the evidence points to, using `skills/DESIGN.md` Evidence labels
  (`Explicit in code`, `Strongly implied by code`, `Needs confirmation`, etc.) to state
  confidence.
- If the evidence does not clearly point to one category, classify as `needs
  confirmation` rather than guessing — MUST NOT default to "production code bug" or any
  other category by convention.

Keep stack trace summaries to the minimum lines needed; MUST NOT paste full tracebacks.

---

## Finding Categories

Tag each Step 6 Finding with one of the following categories, where applicable:
- Existing test failure
- Flaky test risk
- Environment dependency problem
- Missing test coverage
- Test/design inconsistency
- Test/code inconsistency
- Weak assertion quality
- Missing negative-path test
- Missing boundary-condition test
- Missing recovery/fallback test
- Missing integration test
- Missing regression test

---

## Finding, Task, and Test Case IDs (Traceability)

Every artifact produced from Step 6 onward is identified and cross-linked
(evidence → task → test case):

- **Finding ID** (`F-{NNN}`, zero-padded 3 digits, assigned in Step 6, sequential
  across the whole cycle regardless of source step): one per consolidated finding — an
  execution failure (from Step 4), a coverage gap, or an inconsistency (both from
  `discovery.md` Step 5).
- **Task ID** (`T-{NNN}`, assigned in Step 7): each Task's record MUST list
  `Addresses: F-{NNN}[, F-{NNN} ...]` — the Finding(s) it resolves. A Finding with no
  Task addressing it by the end of Step 7 is a gap in the plan — report it in Step 7,
  MUST NOT silently drop it.
- **Test Case ID** (`TC-{NNN}`, assigned in Step 7): each proposed test case's record
  MUST list `Task: T-{NNN}` and, when it targets a specific Finding directly,
  `Finding: F-{NNN}`.

`report-template.md`'s Report Template includes a Traceability table (# 7) built from
these links — MUST NOT re-derive the links there; carry them forward from Steps 6-7.

Reference findings by their Finding ID in Steps 6-7 and in the final report, rather
than re-quoting full evidence or source excerpts already recorded in
`discovery.md`/this file.
