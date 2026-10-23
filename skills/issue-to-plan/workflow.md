# Issue To Plan — Detailed Workflow

## Workflow position

See `routing.md`, section 'Document workflow directories', for the full pipeline.

- Input: `issues/{filename}.md`
- Output: `plans/{timestamp}_{slug}.md` (`{slug}` is the Issue filename's slug)
- Optional outputs: `issues/{timestamp}_unknowns.md`, `issues/{timestamp}_risks.md`
- Archive destination: `issues/done/`
- Workflow phase: `issue-to-plan`

No standalone requirement document (`requires/*.md`) is produced. Evidence verification
and planning happen in one continuous cycle, Steps 1-10 below.

## Allowed file operations

This is a document-only phase. Allowed operations:
- Create the work plan document in `plans/`.
- Create unresolved unknown or risk items as issue files in `issues/` when required by
  Step 6.
- Move the processed Issue file to `issues/done/` once Step 9's validation passes —
  no human approval is required for this move.
- See `skills/issue-to-plan/SKILL.md` Purpose and `skills/DESIGN.md`, section
  "Analysis-only phase constraint".
- MUST NOT modify files outside `plans/`, `issues/`, and the Issue file being moved
  (`issues/` -> `issues/done/`) — see `AGENTS.md` Global Rule 5.

## Toolchain

Tools used by both paths: `rg`/`fd`/`ast-grep` (symbol/file search), `radon`/`vulture`/
`semgrep`/`bandit`/`diff-cover`/`pytest-testmon` (validation quality baseline, Step 5).
Path B's additional architecture/dependency/historical/operational analysis tools are
listed in `workflow-path-b.md` — loaded only when Step 3 classifies Path B, not here.

Repository scaffolding/archival tools (see `tools/TOOL_DESCRIPTIONS.md` for usage):
`tools/generate_workitem.py --kind plan|unknowns|risks` (Step 5 Plan skeleton; Step 6
Unknown/Risk issue skeleton) and `tools/manage_workitem_stage.py close-issue` (Step 10,
`git mv`-based archival move). Per `rules/ai-execution.md` Repository Tool Usage, prefer
these over the equivalent manual command when they cover the need; each Step below
states the fallback if the tool is unavailable or refuses.

---

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-10, ending with the move to `issues/done/` in Step 10 (gated on Step 9's
validation passing, not on human approval) before starting Step 1 for the next file.

Additional context-hygiene guidance specific to this workflow:
- Perform Step 2 (verifying claims in the Issue against current source) sequentially.
  Retain only a concise confirmation or correction, not full file contents.
- Process each Steps 1-10 cycle sequentially — investigation MUST NOT carry from one
  file's cycle into the next (cycles do not run in parallel — see `rules/ai-execution.md`
  Global Safety Restrictions (Base)).
  This isolation applies to conclusions and investigation state, not to re-running an
  identical read-only command against a file confirmed unchanged — see
  `rules/ai-execution.md` Tool Usage for when such a command may be skipped.

Apply `rules/ai-execution.md` Context Reading and Progress Reporting (Base) for the per-step report
cadence.

### Progress recording during Steps 3-6

Report an interim update only when a sub-investigation's outcome is Blocking (see Step
6), contradicts the Issue's claim, or surfaces an item with no suitable Plan destination
(Step 4); MUST NOT report a routine, expected verification step.

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`,
`rules/filename-collision.md`, `templates/traceability.md`,
`templates/requirement-traceability.md`, `templates/execution-status.md`,
`templates/issue.md`, `templates/plan.md`, `skills/DESIGN.md` (Output language,
Change-impact table, Out-of-scope paths, Tool availability guard), `SKILL.md` (this
skill), and this file. Load `templates/unknowns-issue.md` / `templates/risks-issue.md` at
Step 6, only when a standalone Unknown/Risk file is actually filed.
MUST NOT load `workflow-path-b.md` here — see Step 5, which loads it only once Step 3
determines Path B.

Apply `rules/ai-execution.md` Context Reading for reuse-vs-reload of previously loaded
shared files across cycles.

If a required file is missing, unreadable, or contradictory, apply
`rules/ai-execution.md`, section 'Required File Validation'.

---

## Step 1: Identify Target Issues

Apply `rules/workflow-lifecycle.md` Target Validation (Step 1) and `rules/ai-execution.md`
Sequential Target Processing (Base). Workflow-specific: input path `issues/{filename}.md`;
archive directory `issues/done/`.

---

## Step 1b: Check for Existing Plans

Before creating a new Plan, verify whether one already exists for this Issue, to prevent
duplicate plans when multiple agents process the same Issue concurrently.

- Use a content-based check, not a filename glob (Plan filenames use the Plan-*generation*
  timestamp, never the Issue's ID or timestamp): for the current Issue's
  repository-relative path (`{issue_path}`), search for an exact
  `- **Source issue**: {issue_path}` line inside the `## Traceability` section of any
  file in `plans/*.md` or `plans/done/*.md` (e.g.
  `grep -rl -- "- \*\*Source issue\*\*: {issue_path}" plans/*.md plans/done/*.md`).
- **If a matching plan exists**: MUST NOT create a duplicate Plan, and MUST NOT edit the
  existing Plan. Record the existing plan's path in this cycle's report (Step 9's
  existing-Plan form below). Then branch on that Plan's state:
  - In `plans/done/`, or in `plans/` with `Freeze status` read back as `Frozen`: note that
    this Issue has been addressed elsewhere, skip Steps 2-8, emit Step 9's reduced report,
    and proceed to Step 10's existing-Plan case to move the Issue to `issues/done/`.
  - In `plans/` with `Freeze status` `Draft` (or any state other than `Frozen`): MUST NOT
    move the Issue. Resume at Step 8 against that Plan (8a and 8b); the Issue moves only
    after Step 8 reports `Pass` and the section is `Frozen`. If Step 8 cannot reach
    `Pass`, report `Blocked` and leave the Issue in `issues/`.
- **If no matching plan exists**: proceed to Step 2 normally.
- Only check `plans/` and `plans/done/`; MUST NOT check `issues/done/` for archived plans
  (already completed, irrelevant to duplicate detection).

---

## Step 2: Assess the Current Issue

- Read the current Issue file in full.
- Verify any factual claims against current source (affected files, whether the
  described problem still reproduces).
- Apply `rules/ai-execution.md` Adversarial Verification (Base) to the Issue's claims:
  whether the described problem has already been fixed elsewhere, whether the named
  files/symbols/line numbers still exist as stated, whether a claimed dependency or
  side effect is missing or overstated, and whether two claims within the same Issue
  (or against a related `plans/`/`implementations/` document) contradict each other.
  Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: MUST NOT re-run a
  check already performed against the same file/claim at its current content within
  this cycle.
  Stop once every field extracted per `templates/issue.md` (Step 2's extraction list,
  below) has been checked against at least one concrete source (a file, test, or existing
  Plan/Implementation document), and no new disconfirming evidence was found in the last
  full pass over that field list. This complements, and does not replace,
  `rules/workflow-lifecycle.md`'s workflow-level Completion Criteria, which gates the
  whole cycle.
- Extract the fields defined in `templates/issue.md` (the canonical Issue shape shared
  with `skills/issue-creator`), by that template's own names: title, Priority, Summary,
  Background, Problem, Reason for Change, Implementation Intent, Target Files or Areas,
  Required Changes, Constraints, Acceptance Criteria, Testing Expectations, Documentation
  Impact, Out of Scope, Dependencies, Unresolved Questions, and AI Implementation
  Instruction. Treat an explicit `N/A` field as `Explicit in issue`, not as missing
  information.
- Classify each extracted item as one of: `Explicit in issue`, `Confirmed by repository
  evidence`, `Derived from confirmed evidence`, `Needs confirmation`. MUST NOT invent
  missing requirements.
- If adversarial verification surfaces an unconfirmed item or inconsistency between
  the Issue and current source, MUST NOT silently reconcile it — classify it per the
  rule above (`Needs confirmation` if unresolved; `Confirmed by repository evidence` /
  `Derived from confirmed evidence` if resolved) and write the corrected understanding
  into the Plan (Step 5), not the Issue's original, possibly stale claim. After
  reclassifying, re-check only the field(s) the finding affects against this same
  evidence; MUST NOT restart Step 2's full field-by-field pass.
  Apply `rules/workflow-lifecycle.md` Correction-and-Recheck Cycle Bound; the
  `{artifact}` in that bound's `Blocked` message is "Plan". If a clean `Pass` is not
  reached within that bound, the summary MUST list every remaining
  unresolved issue, not only the last one encountered.
- Any item classified `Needs confirmation` carries forward to Step 6 as an Unknown by
  name — MUST NOT re-derive it there. This classification is also the source for the
  Requirement Traceability table's Status column in Step 7.
- If the Issue is already resolved, cannot be reproduced, or no longer applies: report
  the supporting evidence, MUST NOT create a Plan, skip Steps 3-8 (there is no Plan to
  analyze, validate, or freeze), emit Step 9's reduced no-Plan report, and proceed to
  Step 10's no-Plan case to move it to `issues/done/` (same `git mv`-only procedure, no separate path).
- If the Issue is too vague to act on (no identifiable target files or problem
  statement), stop and ask the user for clarification before proceeding.

---

## Step 3: Inspect Related Files — Task-Size Classification

Classify the Issue as Path A or Path B per `SKILL.md`'s Routing (AI Task Size
Assessment) section, **before** inspecting. That classification is provisional: reclassify
as `SKILL.md` Routing says if the inspection reveals a Path B criterion.

- **Path A**: limit this step to direct verification of the target files and their
  immediate dependencies. For each target file, take `<path>` as its repository-relative
  path (e.g. `scripts/agent/foo.py`) and `<dotted>` as that path with the leading
  `scripts/` and the `.py` suffix removed and `/` replaced by `\.` (e.g. `agent\.foo`) —
  run the commands below once per target file, not once for the whole Issue:

  ```bash
  rg "^from|^import" <path> | sort -u
  rg "from <dotted> import|import <dotted>" scripts/ | sort -u
  ```

  `rg` uses Rust regex: alternation is a bare `|`, and `\|` matches a literal pipe. The
  second command does not match `from <package> import <name>` or relative-import forms,
  so zero matches means "none found by this pattern", not proof of no callers.
  Zero matches from the first command means the target file has no imports — confirm
  this by checking the file exists and is non-empty (per Repository Tool Usage #8)
  before treating it as evidence of "no dependencies," rather than a failed pattern
  match against the wrong path.

- **Path B**: perform the full inspection — source files, tests, configuration,
  documentation, callers and callees, dependencies, data ownership, side effects, error
  handling, compatibility constraints, and security constraints. This inspection feeds
  the broader analysis in Step 5.
  In Step 5, where `workflow-path-b.md` is loaded, stop each of the four analysis
  dimensions (Architecture analysis, Dependency graphing,
  Historical analysis, Operational dependency inspection — see
  `workflow-path-b.md`) once its listed toolchain command(s) have been run once against
  the relevant target and their output reviewed; MUST NOT re-run the same command against
  the same target without a changed input, per `rules/ai-execution.md` Tool Usage. This
  is consistent with, not a change to, `workflow-path-b.md`'s "once all four analyses
  above are complete" gate.

Read only the section(s) located via `rg`/grep for the target symbol or claim, unless
that section alone omits context the claim depends on (e.g. a decorator, base class, or
module-level state defined elsewhere in the same file) — in that case read the full file.
Record the Path A/B decision for reuse in Step 5.

Apply `rules/workflow-lifecycle.md` Evidence-Only vs. Target Files: only
modification-target files belong in the Plan's `Implementation Target Files` table
(Step 5); evidence-only files belong in `Reference Files` (also Step 5) — MUST NOT merely
cite them in prose.

---

## Step 4: Map Issue Information to Plan Information

Create an explicit mapping before writing the Plan:

| Issue item | Plan destination |
|---|---|
| Title, Summary | Goal |
| Priority | Priority |
| Target Files or Areas | Implementation Target Files, Reference Files (Affected areas and Traceability's Related target files are derived from Implementation Target Files, not mapped independently) |
| Background | Background |
| Problem | Problem |
| Reason for Change | Reason for Change |
| Implementation Intent | Implementation Intent, Design |
| Required Changes | Requirements, Implementation steps |
| AI Implementation Instruction | Implementation steps (as per-step constraints) |
| Acceptance Criteria | Acceptance Criteria, Validation plan |
| Testing Expectations | Tests, Validation plan |
| Documentation Impact | Documentation Impact |
| Constraints | Scope, Assumptions, Risks |
| Out of Scope | Scope (Out-of-Scope) |
| Dependencies | Scope (Dependencies), Risks (when an ordering dependency can fail) |
| Unresolved Questions | Unknowns |
| Repository evidence (Step 2/3) | Design, Risks, Validation plan |
| Source Issue path | Traceability |

No requirement information may remain unmapped. If information has no suitable
destination, add an appropriate Plan section instead of discarding it. This mapping runs
identically for Path A and Path B; classification reduces analysis depth (Steps 3 and
5), not mapping completeness.

A Step 2 item classified `Needs confirmation` MUST NOT be written into the Plan's
Assumptions section as if verified — route it to Unknowns (Step 6) instead. Assumptions
are for judgment calls made during analysis, not for unverified Issue claims.

---

## Step 5: Create the Plan

Using the Path A/B classification from Step 3:

- **Path A**: skip architecture analysis, dependency graphing, historical analysis, and
  operational dependency inspection. Still establish the validation quality baseline
  (radon/vulture/semgrep/bandit/diff-cover, lightweight or full as installed) — this
  baseline is not skipped (see `SKILL.md` Path A).
- **Path B**: load `workflow-path-b.md` now and perform all four of its analyses
  (architecture, dependency graphing, historical, operational dependency inspection)
  before creating the Plan.

#### Validation quality analysis (baseline — run regardless of Path A/B)

```bash
radon cc <path> -s    # once per target file under scripts/ (<path> as in Step 3)
vulture scripts/ --min-confidence 80
bandit -r scripts/ -c pyproject.toml
```

Per `rules/ai-execution.md` Repository Tool Usage #8, an exit-0 run reporting zero
findings is evidence only if the target path was actually scanned; confirm the target
file/directory exists before recording "no findings" as a baseline value.

See `rules/toolchain.md` section 7 for the diff-cover baseline command sequence (run
without `--fail-under` here, just to record the current number). The Plan MUST include
raising it to the threshold defined in `rules/toolchain.md` Completion checklist.

#### Generate the Plan

- Output language: see `skills/DESIGN.md` §Output language.
- Determine the timestamp by running: `date +%Y%m%d-%H%M%S`.
- Derive `{slug}` from the Issue's filename `{timestamp}_{id}_{slug}.md` (see
  `skills/issue-creator/SKILL.md` Issue Filename Generation): everything after the second
  `_`, copied unchanged. An Issue file without that shape (e.g. a
  `{timestamp}_unknowns.md` follow-up file) uses everything after its leading timestamp.
  The slug MUST match `[a-z0-9_-]+`; otherwise stop and report `Blocked`.
- Save as `plans/{timestamp}_{slug}.md`. If that path already exists, use the lowest
  available zero-padded sequence (`plans/{timestamp}_01_{slug}.md`,
  `plans/{timestamp}_02_{slug}.md`, ...), applying `rules/filename-collision.md`
  Collision Retry Bound.
- Optionally scaffold the empty file first with `uv run python
  tools/generate_workitem.py --kind plan --source-issue issues/{filename}.md` — it
  derives `{slug}` as above and reproduces `templates/plan.md`'s current field order
  exactly. The tool refuses (non-zero exit, no write) on a path collision
  rather than auto-incrementing; treat that refusal as the trigger for the zero-padded
  sequence rule above (retry with `--seq {NN}`), not as a workflow failure.
  After a `0` exit, independently verify the reported output path exists and contains
  the expected `## ` section headings before filling in its content — per
  `rules/ai-execution.md` Repository Tool Usage item 8, a `0` exit alone MUST NOT be
  treated as proof the file was written correctly.
- Use the section order and structure from `SKILL.md` Output format.
- Assign every requirement a stable ID (`REQ-001`, `REQ-002`, ...). Each Acceptance
  criterion, Test, and Implementation step MUST reference its related Requirement ID.
- Populate `Implementation Target Files` and `Reference Files` per `templates/plan.md`:
  one explicit repository-relative file path per row — never a directory, glob
  pattern, component/module name, file group, or a vague phrase such as "related
  files" or "as necessary". Give a test, configuration, schema, migration, deployment,
  or documentation file its own row when it requires modification, rather than folding
  it into the row for the source file it accompanies. Every `Repository Evidence`
  entry MUST cite what Step 3's inspection actually found — MUST NOT infer it.
- Generate the `Affected areas` table per `templates/plan.md`: one row for every
  `Implementation Target Files` row, so that the `File` column is a subset of those rows,
  with all six columns populated (`File`, `Change`, `Blast Radius`, `Churn (30d)`,
  `Bus Factor`, `deploy.sh Impact`). `Change` is `Modify`, `Create`, or `Delete`;
  `Blast Radius` is a qualitative `Low`, `Medium`, or `High`; `deploy.sh Impact` always
  states a value from `skills/DESIGN.md` Change-impact table. Path A: judge
  `Blast Radius` qualitatively from Step 3's direct verification and mark `Churn (30d)`
  and `Bus Factor` `N/A`. Path B: take `Blast Radius` from the dependency graphing and
  `Churn (30d)` and `Bus Factor` from the historical analysis in `workflow-path-b.md`,
  and mark a column `N/A` when the tool that would fill it is unavailable.
- Generate the `Risks` section: extract a potential risk from each Constraint and each
  repository evidence finding mapped to Risks in Step 4, and write each as
  `- **Risk**: {description} → **Mitigation**: {description}`. This step writes the
  Plan's inline `Risks` section; Step 6 refines that same section and files
  `issues/{timestamp}_risks.md` only for a Risk that still lacks a complete mitigation.
  A separate file never replaces the inline section.
- Every claim MUST be backed by evidence gathered above (for Path A, by Step 3's direct
  verification).
- Implementation steps MUST be small enough to be independently revertable.
- A deploy step MUST be included if `scripts/`/`config/` changes; an MCP service map
  update MUST be included if a new server is added.
- MUST NOT include speculative steps — only steps required by the stated goal.
- The Plan MUST be detailed enough for the next pipeline phase (per Workflow position
  above) to produce file-level implementation procedures. MUST NOT implement anything.
- Populate the `### Execution Status` table (see `templates/execution-status.md`) with
  one row per Implementation step just written above — same numbering, each
  `Description` a short restatement of that step, `Status` set to `Pending`, and
  `Started`/`Completed` left as `—`. Per `templates/execution-status.md` Notes, MUST NOT
  leave the template's single placeholder row in a Plan that already lists its
  concrete Implementation steps in this same Step. This is initial population only;
  advancing a row past `Pending` is `plan-to-implementation-procedure`'s and
  `code-implementation`'s responsibility, not this skill's.

---

## Step 6: Analyze Unknowns and Risks

- Write any generated `issues/{timestamp}_unknowns.md` / `issues/{timestamp}_risks.md`
  file in English (see `SKILL.md` Core Execution Rules), same as the Plan. These names
  are a deliberate exception to `skills/issue-creator`'s `{timestamp}_{id}_{slug}.md`
  convention: they follow `templates/unknowns-issue.md` / `templates/risks-issue.md`. Optionally
  scaffold the empty file first with `uv run python tools/generate_workitem.py --kind
  unknowns` / `--kind risks` — it reproduces `templates/unknowns-issue.md` /
  `templates/risks-issue.md`'s current field order exactly. The tool refuses (non-zero
  exit, no write) on a base-path collision rather than auto-incrementing; on that
  refusal, retry once with `--seq {NN}` matching the zero-padded sequence rule below,
  not as a workflow failure.
  After a `0` exit, independently verify the reported output path(s) exist and contain
  the expected `## ` section headings before filling in their content — same
  verification as Step 5, per `rules/ai-execution.md` Repository Tool Usage item 8.
- Include the items carried forward from Step 2's `Needs confirmation` classifications
  as Unknowns, in addition to any Unknowns identified during Steps 3-5.
- Resolve Unknowns only when supported by repository evidence.
- If a blocking ambiguity remains (`BLOCKING: True`), stop and request clarification; the cycle ends `Blocked` and the Issue stays in `issues/` (no move).
- Record non-blocking Unknowns in the Plan's Unknowns table
  (`ID | Unknown Description | Evidence Missing | Resolution Path | Blocking?`). Only
  create `issues/{timestamp}_unknowns.md` (GitHub Issue Markdown format, one issue per
  section) when at least one Unknown is `BLOCKING: True` or otherwise requires
  standalone tracking beyond the Plan's inline table.
- Analyze every Risk and add a mitigation (Risk + likelihood + mitigation). Only file
  `issues/{timestamp}_risks.md` the same way when at least one Risk lacks a complete
  mitigation and needs separate follow-up.
- MUST NOT create either file with placeholder or empty content — if the Plan's inline
  table fully captures every Unknown/Risk, MUST NOT also file a separate issue for it.
- **Completed when**: every Unknown surfaced in Step 2/3/5 is resolved (backed by
  repository evidence) or recorded in the Unknowns table with a Resolution Path, and every
  Risk has a mitigation or is filed to `issues/{timestamp}_risks.md`. MUST NOT keep
  investigating a non-blocking Unknown once a plausible Resolution Path is recorded;
  further confirmation belongs to the implementation phase.
- Apply `rules/workflow-lifecycle.md` Requirement Reference Format when an Unknown/Risk
  issue file (or the Step 7 Requirement Traceability table) references a Requirement.
- Reuse the base timestamp from Step 5 (`date +%Y%m%d-%H%M%S`) for both files — MUST NOT
  regenerate.
- If either path already exists, apply the same lowest-available zero-padded sequence
  rule as Step 5 (`issues/{timestamp}_01_unknowns.md`, `issues/{timestamp}_01_risks.md`,
  ...). An existing file MUST NOT be overwritten.
  The same 3-attempt bound and stop-and-report behavior from Step 5 apply here: after 3
  collisions on either path, stop and report `Blocked: repeated filename collision —
  {path}` for the colliding path.
- Each generated Unknown or Risk issue MUST include a Traceability section (per
  `templates/unknowns-issue.md` / `templates/risks-issue.md` — a deliberately
  narrower field subset than `templates/traceability.md`'s, since these trace to
  exactly one Issue and one Plan): Source issue = current
  Issue path; Source plan = the Step 5 Plan file.

---

## Step 7: Add Traceability

- Fill the Traceability section using `templates/traceability.md`'s structure:
  Workflow phase `issue-to-plan`; Source issue = the Issue path; Source requirement =
  `N/A: no standalone requirement document is generated`; Source plan =
  `N/A: this document is the generated plan`; Source implementation procedure =
  `N/A: not applicable in this phase`; Generated at = the Step 5 timestamp; Related
  target files = the affected paths.
- Add the "Requirement Traceability" subsection immediately after those fields, using
  `templates/requirement-traceability.md`'s column format (Requirement ID, Source Issue
  section or evidence, Target file, Implementation step, Acceptance criterion, Test or
  validation item, Status). Status is the Step 2 evidence classification for that
  Requirement.

---

## Step 8: Validate Information Completeness

This step has three sub-steps, applied in order: verify completeness and traceability
(8a), validate and freeze the target-file inventory (8b), then report the outcome (8c).

### Step 8a: Verify information completeness and traceability

Verify the Plan preserves: title/priority, target files, background, problem, reason for
change, implementation intent, implementation instructions, acceptance criteria, tests,
documentation impact, constraints/out-of-scope items, dependencies, assumptions,
unknowns, risks/mitigations, and Source Issue traceability.

Verify the Requirement Traceability subsection has at least one row per Requirement ID
(one per target file it affects) with all columns filled, including a Status entry
from Step 2.

Verify every Requirement ID is traceable to its Issue source/evidence, an implementation
step, an acceptance criterion, and a test/validation item.

Verify the `Affected areas` table: every row's `File` is one of the
`Implementation Target Files` rows, and all six columns (`File`, `Change`,
`Blast Radius`, `Churn (30d)`, `Bus Factor`, `deploy.sh Impact`) are populated or
marked `N/A`.

Verify the `Risks` section: every Risk entry has a corresponding Mitigation.

Run `uv run python tools/check_workitem_structure.py --file plans/{filename}.md` on the
filled Plan (per `routing.md` Tools → "When to run which tool"). It checks only that every
required `## ` section is present; the content checks above still apply.

**Completed when**: every item in the preserved-information list above is present in the
Plan, and every Requirement ID is traceable to all four of its required links. The
`Affected areas` and `Risks` checks above MUST also pass, and the structure checker
reports no findings.

### Step 8b: Validate and freeze Implementation Target Files

Apply `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) — Initial validation, to every row of `Implementation Target Files`, including
that section's additional checks. Mark the section `Frozen` only when every row is
`Verified` and those additional checks pass. MUST NOT report `Pass` while any row
remains `Needs confirmation` or the section is not `Frozen`.

**Completed when**: every row is `Verified` and the section is marked `Frozen`.

### Step 8c: Report the outcome and re-entry

Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
is unmapped or untraceable, or `Implementation Target Files` is not `Frozen`, MUST NOT
report `Pass` or `Completed`.

If reaching `Pass` requires more than 3 consecutive correction-and-recheck cycles (see
Step 2's cycle bound above), stop and report `Blocked` per that bound rather than
cycling through Step 2/Step 8 indefinitely.

If Step 8 reports `Fail` or `Partial`, resume from the Step matching the failure's cause,
not from Step 5 (full Plan regeneration), unless the cause is shown to invalidate multiple
sections:

| Failure cause | Re-entry Step |
|---|---|
| A Requirement field is unmapped | Step 4 (Issue→Plan field mapping) |
| A Requirement is untraceable | Step 7 (Requirement Traceability) |
| An `Implementation Target Files` row fails Plan Freeze validation, or the section's additional checks fail (path in both sections, non-file row) | Correct that row per `rules/workflow-lifecycle.md`'s Revalidation procedure, then re-run only this Step's freeze check |
| The section is not `Frozen` for any other reason (e.g. a row remains `Needs confirmation`) | Resolve the cause per `rules/workflow-lifecycle.md` Initial validation (re-verify, correct, or route to `Unknowns`), then re-run Step 8b |

A not-`Frozen` Plan is never a terminal state for the Issue: MUST NOT proceed to Step 10 or
move the Issue to `issues/done/`. The Issue stays in `issues/`, and Step 8 is re-run
(8a and 8b) after each correction until it reports `Pass`. If the 3-cycle bound above is
reached, report `Blocked`; the Issue still stays in `issues/`, and a later run may
re-enter at Step 8 against the existing Plan instead of regenerating it.

Corrections are scoped to the affected section(s) by default.

If Step 8 (or an earlier Step's revalidation) requires correcting the Plan document via
Edit, see `rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether
`AGENTS.md` Rollback Directive applies (it does not) and how a repeated-correction risk is
bounded instead.

Before delivering, cross-check (MUST NOT re-derive): goal is one sentence and verifiable;
scope has explicit in/out boundaries; assumptions are falsifiable; no blocking Unknowns
remain unresolved; claims are backed by tool evidence; implementation steps are
independently revertable with a deploy step if production files change; validation plan
has a full table; risks are stated with mitigations.

---

## Step 9: Final Validation

When no Plan was generated this cycle, report only: the Issue path; the case (`already
resolved / no longer applies` with the supporting evidence, or `existing Plan` with that
Plan's path and its `Frozen` read-back); and the Issue pending move. The Plan-specific
fields below do not apply.

Otherwise report: generated Plan path; generated Unknown/Risk files (or `None`); number of
Requirements; number of `Implementation Target Files` rows; Path A/B classification
(one word; rationale is in the Plan's Design section, MUST NOT restate);
information-completeness result; traceability result; `Implementation Target Files`
freeze status (`Frozen` / not `Frozen` with reason); unresolved items count; and the
Issue pending move. MUST NOT restate the Requirement Traceability evidence-classification
breakdown (already in the Plan's table).

Per `rules/ai-execution.md` Progress Reporting (Base), read every value above back from
where it was recorded (e.g. Path A/B from Step 3's record, freeze status from Step 8's
validation) rather than re-deriving it, unless the source is known to have changed.

No human approval is required for the move to `issues/done/`, per
`rules/workflow-lifecycle.md` Validation Reporting — proceed to Step 10 once Step 8 is
`Pass` and all required validations are `Pass`.

If `Implementation Target Files` is not `Frozen`, or Step 8 is `Fail`, `Partial`, or
`Blocked`, MUST NOT proceed to Step 10 and MUST NOT move the Issue. For `Fail`/`Partial`,
resume from the Step named in Step 8's cause → re-entry-Step table above, then re-run
Step 8 before reconsidering Step 10. For `Blocked`, stop and report; the Issue stays in
`issues/`.

---

## Step 10: Move the Issue

This step MUST NOT be skipped. Apply `rules/workflow-lifecycle.md` Archival Move
(issue-to-plan section) — same before/after verification checklist and `Blocked`-on-
failure rule.

- Gate, by case:
  - Plan generated this cycle: move once Step 9 confirms information completeness is
    `Pass` and all required validations are `Pass`, and — read back from the Plan file,
    not assumed — the Plan's `Implementation Target Files` `Freeze status` is `Frozen`
    and no `BLOCKING: True` Unknown remains unresolved. If any of these does not hold
    (Plan is `Draft`, or the cycle is `Blocked`), MUST NOT move the Issue.
  - No-Plan case (Step 2 found the Issue resolved / no longer applicable): move once the
    supporting evidence has been reported. No Plan exists, so the `Frozen` and
    Step 8 checks do not apply.
  - Existing-Plan case (Step 1b): move only when that Plan is in `plans/done/` or reads
    back `Frozen` in `plans/`.
- Prefer `uv run python tools/manage_workitem_stage.py close-issue
  issues/{filename}.md`. If the Issue file has uncommitted changes, the tool commits
  it first (`chore: auto-commit ...`); pass `--stage-only` to stage it instead, so the
  rename lands in the next real commit. It then performs the same
  `git mv issues/{filename}.md issues/done/{filename}.md` move.
- The tool refuses (non-zero exit, no move) if the source is missing, the destination
  already exists, or a Plan in `plans/` for this Issue is not `Frozen`. MUST NOT work
  around the last refusal with `--force`; resume at Step 8 instead. An Issue with no
  matching Plan moves normally. The direct command below does not run the `Frozen`
  check, so the gate above applies to it too. Fall back to it only if the tool is
  unavailable.
- Direct command (fallback): `git mv issues/{filename}.md
  issues/done/{filename}.md`. No `mv`, `cp` + `rm`, file-copy APIs, or other
  fallback beyond these two.
- Report `Completed` only after successful verification.

**This cycle is complete when, and only when**: the move above has succeeded and been
verified (both locations checked, per Archival Move), or this Issue's cycle ended in a
`Blocked` state per Step 2/3/8's own stop conditions — in either case, emit this
cycle's Step 9 report once, then (per Multi-file processing) begin Step 1 for the next
target Issue, or end the batch if none remain.

---

## Out of Scope

See `rules/workflow-lifecycle.md` Global Safety Restrictions for the full list.
(Source code / `docs/*.md` scope: `skills/DESIGN.md` Analysis-only phase constraint,
declared in `SKILL.md` Purpose. File-scope restrictions: declared above in Allowed
file operations. Not repeated here.)

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
