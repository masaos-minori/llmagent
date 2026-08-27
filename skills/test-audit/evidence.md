# Test Audit — Result Classification, Evidence Criteria, and Traceability IDs

Load this file at Step 0 (unconditionally). It covers the classification vocabulary
used from Step 3 onward, the evidence procedure Step 4 applies, and the ID scheme
Steps 6-7 use for traceability.

---

## Result Classification

Classify every executed or attempted command using exactly one of these five results —
used consistently in Steps 2-4 and in `report-template.md`'s Report Template Section 2:

- **Pass** — ran to completion with no failures.
- **Fail** — ran to completion with one or more failures.
- **Partial** — ran, but some sub-cases were skipped, xfail, or otherwise incomplete;
  state exactly what was skipped and why.
- **Not runnable** — cannot run in this environment as designed (e.g. requires a
  production-only resource with no safe local/emulated equivalent). A structural
  limitation, not a fixable blocker.
- **Blocked** — could run in principle, but a specific missing or unavailable
  environment, service, or credential currently prevents it. Record exactly what is
  missing.

Never report `Not runnable` or `Blocked` as `Pass`. An unexecuted or partially executed
check has no result other than one of the five above — do not infer `Pass` from a
similar command's success, from the absence of an error, or from partial output.

---

## Evidence Criteria for Root Cause and Flaky Classification (Step 4)

Do not classify a failure's determinism or root cause from a single run or from
intuition. Apply this evidence procedure for every `Fail` result from `workflow.md`
Step 3.

### Deterministic vs. flaky

- Re-run the failing test in isolation at least 3 times, or use the repository's own
  flaky-detection tooling if one is configured (e.g. `pytest-rerunfailures`) — prefer
  the repository-defined tool over a manual loop when one exists.
- All runs fail identically (same assertion/exception) → `Deterministic`.
- Results vary across runs → `Flaky`; record the observed ratio (e.g. "failed 2/3
  runs") as evidence.
- If re-running is unsafe or not possible (the test is `Blocked`/`Not runnable` above)
  → `Flaky determination: Needs confirmation` — do not guess.

### Root cause

- Classify as one of: production code bug / test code bug / environment or setup
  issue / needs confirmation.
- A classification other than "needs confirmation" requires a cited concrete location
  (function, method, or config key — see `skills/DESIGN.md` No source-code line
  numbers) that the evidence points to, using `skills/DESIGN.md` Evidence labels
  (`Explicit in code`, `Strongly implied by code`, `Needs confirmation`, etc.) to state
  confidence.
- If the evidence does not clearly point to one category, classify as `needs
  confirmation` rather than guessing — do not default to "production code bug" or any
  other category by convention.

Keep stack trace summaries to the minimum lines needed to identify the cause; do not
paste full tracebacks.

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

Every artifact this workflow produces from Step 6 onward is identified and
cross-linked so a reader can trace root evidence → task → test case:

- **Finding ID** (`F-{NNN}`, zero-padded 3 digits, assigned in Step 6, sequential
  across the whole cycle regardless of source step): one per consolidated finding — an
  execution failure (from Step 4), a coverage gap, or an inconsistency (both from
  `discovery.md` Step 5).
- **Task ID** (`T-{NNN}`, assigned in Step 7): each Task's record must list
  `Addresses: F-{NNN}[, F-{NNN} ...]` — the Finding(s) it resolves. A Finding with no
  Task addressing it by the end of Step 7 is a gap in the plan — report it in Step 7,
  do not silently drop it.
- **Test Case ID** (`TC-{NNN}`, assigned in Step 7): each proposed test case's record
  must list `Task: T-{NNN}` and, when it targets a specific Finding directly,
  `Finding: F-{NNN}`.

`report-template.md`'s Report Template includes a Traceability table (# 7) built from
these links — do not re-derive the links there; carry them forward from Steps 6-7.

Reference findings by their Finding ID in Steps 6-7 and in the final report, rather
than re-quoting full evidence or source excerpts already recorded in
`discovery.md`/this file.
