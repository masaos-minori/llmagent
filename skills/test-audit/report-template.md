# Test Audit — Final Report Template

Load this file at Step 0 (unconditionally). It defines `workflow.md` Step 8's report
structure, the rules for populating it, and the optional GitHub Issue Drafts output.

---

## Report Template (fixed structure — Step 8 output)

Use exactly these sections, in this order. This is a structural skeleton only — see
Report Content Rules below for how to populate each section; MUST NOT add instructional
prose inside the generated report itself.

```markdown
# 1. Overall Findings
- (3-10 bullets)

# 2. Executed Tests / Validation Commands
- command / purpose / result / notes  (one entry per Step 1 command; a command Step 2
  did not clear carries its mapped Result and reason, per `evidence.md`)

# 3. Existing Test Failures
- Finding ID / test name / file / failure type / likely cause / severity /
  deterministic-or-flaky (with evidence ratio) / root cause / evidence summary

# 4. Missing or Inconsistent Test Cases
- Finding ID / category / affected component / why insufficient / uncovered risk /
  evidence / coverage figure (or `not measured`) / confirmed-or-needs-confirmation

# 5. Implementation Task List
## P1 (Critical)
| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|
## P2 (Important)
| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|
## P3 (Nice to have)
| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|

# 6. Test Cases to Add or Update
- Test Case ID / Task ID / Finding ID (if direct) / target module-feature / purpose /
  setup / input-condition / expected behavior / why necessary / type (unit /
  integration / e2e / regression)

# 7. Traceability
| Finding ID | Category | Severity | Task ID(s) | Test Case ID(s) | Status |
|---|---|---|---|---|---|

# 8. Recommended Execution Order
- ordered Task ID list, one-line rationale each

# 9. Additional Confirmation Items Needed
- (list)
```

---

## Report Content Rules (Step 8)

Populate every section above using IDs and content already established in Steps 1-7;
MUST NOT re-derive or re-analyze.

- **# 1**: summarize overall test-suite health; mention the strongest and weakest
  areas.
- **# 2**: one entry per Step 1 command — executed ones with their Step 3 Result, and
  commands Step 2 did not clear with the Result mapped in `evidence.md` ("Commands that
  were never executed"). For `Pass`, a concise one-line summary; for
  `Fail`/`Partial`/`Blocked`/`Not available`, retain the full relevant detail carried
  from Step 2/3/4 (see `evidence.md` Result Classification).
- **# 3**: one entry per Step 6 Finding whose category is an execution-failure type
  (sourced from Step 4).
- **# 4**: one entry per Step 6 Finding whose category is a gap/inconsistency type
  (sourced from `discovery.md` Step 5); tag each with a Finding Category
  (`evidence.md`).
- **# 5**: one row per Step 7 Task, grouped by Priority per `SKILL.md` Priority and
  Effort; every row's `Addresses` column cites its Finding ID(s).
- **# 6**: one entry per Step 7 test case; every entry cites its Task ID.
- **# 7**: build directly from the Finding ID → Task ID → Test Case ID links recorded
  in Steps 6-7 (`evidence.md` Finding, Task, and Test Case IDs). A Finding with no
  Task, or a Task with no Test Case where one is expected, MUST still appear with the
  gap visible (e.g. `Task ID(s): —`) — MUST NOT omit it.
- **# 8**: order Task IDs and explain why (dependency chain, risk, effort).
- **# 9**: list every unresolved `Needs confirmation` item carried from Steps 4/5, and
  always state the audit's limits: flaky detection covers only tests that failed in
  Step 3 (`evidence.md`), and any command classified `Blocked`/`Not available`.

Determine the report destination from existing repository rules: if the repository
defines a report directory, save the Markdown report there; if no destination is
defined, return the report only in the final response; MUST NOT create a new report
directory without an existing rule.

---

## Optional Extra Output

Generate section `# 10. GitHub Issue Drafts` only when the user explicitly requests it, after
the main report:

```markdown
# 10. GitHub Issue Drafts (English, AI-oriented)
- 1 issue = 1 Task ID
- `P1` items only by default
```

Draft each issue by applying `skills/issue-creator/SKILL.md`, with `templates/issue.md`
as the structure — MUST NOT keep a separate field list here, so a draft can enter
`issue-to-plan` unchanged. Assign each issue's Priority by `skills/issue-creator/workflow.md`
Phase 7, not by copying P1/P2/P3. Cite the Task ID and its Finding IDs in `Background`
and `Traceability`.
