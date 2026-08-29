# Issue To Plan — Detailed Workflow

## Workflow position

```text
issue file (issues/)
  -> work plan document (plans/)   <- this skill
  -> file-level implementation procedure document (implementations/)
  -> implementation, tests, and documentation updates
```

- Input: `issues/{filename}.md`
- Output: `plans/{timestamp}_plan.md`
- Optional outputs: `issues/{timestamp}_unknowns.md`, `issues/{timestamp}_risks.md`
- Archive destination: `issues/done/`
- Workflow phase: `issue-to-plan`

No standalone requirement document (`requires/*.md`) is produced. Evidence
verification and planning happen in one continuous cycle, Steps 1-10 below.

## Allowed file operations

This is a document-only phase. Allowed operations:
- Create the work plan document in `plans/`.
- Create unresolved unknown or risk items as issue files in `issues/` when required by
  Step 6.
- Move the processed Issue file to `issues/done/` once Step 9's validation passes —
  no human approval is required for this move.
- Do not modify source code files.
- Do not update documentation (`docs/*.md`).
- Do not modify files outside `plans/`, `issues/`, and the Issue file being moved
  (`issues/` -> `issues/done/`).

## Toolchain

Tools used by both paths: `rg`/`fd`/`ast-grep` (symbol/file search), `radon`/`vulture`/
`semgrep`/`bandit`/`diff-cover`/`pytest-testmon` (validation quality baseline, Step 5).
Path B's additional architecture/dependency/historical/operational analysis tools are
listed in `workflow-path-b.md` — loaded only when Step 3 classifies Path B, not here.

---

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-10, ending with the move to `issues/done/` in Step 10 — gated on Step 9's
validation passing, not on human approval — before starting Step 1 for the next
file.

Additional context-hygiene guidance specific to this workflow:
- Perform Step 2 (verifying claims in the Issue against current source) sequentially.
  Retain only a concise confirmation or correction, not full file contents.
- Process each Steps 1-10 cycle sequentially — investigation MUST NOT carry from one
  file's cycle into the next; cycles MUST run one at a time, not in parallel.
- Do not summarize shared rules or template content in chat — reference them by file
  name instead.

Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report
cadence.

### Progress recording during Steps 3-6

Report an interim update only when a sub-investigation's outcome is Blocking (see
Step 6), contradicts the Issue's claim, or surfaces an item with no suitable Plan
destination (Step 4) — do not report for a routine, expected verification step.

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`,
`templates/traceability.md`, `templates/requirement-traceability.md`,
`templates/issue.md`, `templates/plan.md`, `SKILL.md` (this skill), and this file.
Do not load `workflow-path-b.md` here — see Step 5, which loads it only once Step 3
determines Path B.

Apply `rules/ai-execution.md` Context Reading for reuse-vs-reload of previously loaded
shared files across cycles in this session.

If a required file is missing, unreadable, or contradictory, apply
`rules/ai-execution.md` Instruction Precedence; if unresolvable, stop and report
`Blocked`. Do not infer missing instructions.

---

## Step 1: Identify Target Issues

Apply `rules/workflow-lifecycle.md` Target Validation (Step 1) and `rules/ai-execution.md`
Sequential Target Processing (Base). Workflow-specific: input path `issues/{filename}.md`;
archive directory `issues/done/`.

---

## Step 1.5: Check for Existing Plans

Before creating a new Plan, verify whether one already exists for this Issue. This prevents
duplicate plans when multiple agents process the same Issue concurrently.

- **If the Issue filename contains an ID** (format: `{timestamp}_{id}_{slug}.md`, e.g.
  `20260828-155804_nc019_git_mcp_command_specific_guards.md`): extract the ID portion
  (`nc019`), then glob `plans/*{issue_id}*plan.md` (case-insensitive match on the ID).
- **If the Issue filename does NOT contain an ID but has a timestamp prefix** (e.g.
  `20260717-171259_nuitka_onefile_packaging_proposal.md`): extract the timestamp portion
  (`20260717-171259`), then glob both `plans/*{timestamp}*plan.md` and
  `plans/done/*{timestamp}*plan.md` (case-insensitive match on the timestamp). A plan
  may exist in `plans/` (active) or `plans/done/` (archived after implementation).
- **If the Issue filename does NOT contain an ID or timestamp** (plain descriptive name,
  e.g. `multi-agent-orchestration-design-plan.md`): this case is outside the scope of
  the issue-creator skill. Do not attempt dedup; proceed to Step 2 normally.
- **If a matching plan exists**: record the existing plan's path in the Traceability section,
  note that this Issue has been addressed elsewhere, and proceed to Step 9/10 to move the
  Issue to `issues/done/` without creating a duplicate Plan.
- **If no matching plan exists**: proceed to Step 2 normally.
- Only check `plans/` and `plans/done/` — do not check `issues/done/` for archived plans
  (those are already completed and irrelevant to duplicate detection).

---

## Step 2: Assess the Current Issue

- Read the current Issue file in full.
- Verify any factual claims against current source (affected files, whether the
  described problem still reproduces).
- **Adversarial verification**: do not stop at confirming the Issue's claims — actively
  look for evidence that would refute or narrow them: whether the described problem has
  already been fixed elsewhere, whether the named files/symbols/line numbers still
  exist as stated, whether a claimed dependency or side effect is missing or
  overstated, and whether two claims within the same Issue (or against a related
  `plans/`/`implementations/` document) contradict each other. Treat this as a search
  for disconfirming evidence, not reconfirmation of prior findings.
- Extract the fields defined in `templates/issue.md` (the canonical Issue shape shared
  with `skills/issue-creator`): title, priority, target files, background, problem,
  reason for change, implementation intent, implementation instructions, constraints,
  acceptance criteria, tests, dependencies, and unresolved questions. Treat an
  explicit `N/A` field as `Explicit in issue`, not as missing information.
- Classify each extracted item as one of: `Explicit in issue`, `Confirmed by repository
  evidence`, `Derived from confirmed evidence`, `Needs confirmation`. Do not invent
  missing requirements.
- If adversarial verification surfaces an unconfirmed item or inconsistency between
  the Issue and current source, do not silently reconcile it — classify it per the
  rule above (`Needs confirmation` if unresolved; `Confirmed by repository evidence` /
  `Derived from confirmed evidence` if resolved) and write the corrected understanding
  into the Plan (Step 5), not the Issue's original, possibly stale claim.
- Any item classified `Needs confirmation` carries forward to Step 6 as an Unknown by
  name — do not re-derive it there. This classification is also the source for the
  Requirement Traceability table's Status column in Step 7.
- If the Issue is already resolved, cannot be reproduced, or no longer applies: report
  the supporting evidence, do not create a Plan, and proceed to Step 9/10 to move it to
  `issues/done/` (same `git mv`-only procedure, no separate path).
- If the Issue is too vague to act on (no identifiable target files or problem
  statement), stop and ask the user for clarification before proceeding.

---

## Step 3: Inspect Related Files — Task-Size Classification

Classify the Issue as Path A or Path B per `SKILL.md`'s Routing (AI Task Size
Assessment) section, **before** inspecting.

- **Path A**: limit this step to direct verification of the target files and their
  immediate dependencies:

  ```bash
  rg "^from|^import" scripts/<module>.py | sort -u
  rg "from <module> import\|import <module>" scripts/ | sort -u
  ```

- **Path B**: perform the full inspection — source files, tests, configuration,
  documentation, callers and callees, dependencies, data ownership, side effects, error
  handling, compatibility constraints, and security constraints. This inspection feeds
  the broader analysis in Step 5.

Read only relevant sections unless the full file is required for an accurate
conclusion. Record the Path A/B decision for reuse in Step 5.

Track files inspected only for evidence separately from files planned for
modification. Only modification-target files belong in the Plan's `Implementation
Target Files` table (Step 5); evidence-only files belong in `Reference Files` (also
Step 5) — do not merely cite them in prose.

---

## Step 4: Map Issue Information to Plan Information

Create an explicit mapping before writing the Plan:

| Issue item | Plan destination |
|---|---|
| Title | Goal |
| Priority | Priority |
| Target files | Implementation Target Files, Reference Files (Affected areas and Traceability's Related target files are derived from Implementation Target Files, not mapped independently) |
| Background | Background |
| Problem | Problem |
| Reason for change | Reason for change |
| Implementation intent | Implementation intent, Design |
| Implementation instructions | Requirements, Implementation steps |
| Acceptance criteria | Acceptance criteria, Validation plan |
| Tests | Tests, Validation plan |
| Documentation Impact | Documentation Impact |
| Constraints | Scope, Assumptions, Risks |
| Unresolved questions | Unknowns |
| Repository evidence (Step 2/3) | Design, Risks, Validation plan |
| Source Issue path | Traceability |

No requirement information may remain unmapped. If information has no suitable
destination, add an appropriate Plan section instead of discarding it. This mapping step
runs identically for Path A and Path B — task-size classification does not reduce
mapping completeness, only analysis depth (Steps 3 and 5).

A Step 2 item classified `Needs confirmation` must not be written into the Plan's
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
radon cc scripts/<module>.py -s
vulture scripts/ --min-confidence 80
bandit -r scripts/ -c pyproject.toml
```

See `rules/toolchain.md` section 7 for the diff-cover baseline command sequence (run
without `--fail-under` here, just to record the current number). The Plan must include
raising it to ≥ 90%.

#### Generate the Plan

- Write the entire Plan in English (see `SKILL.md` Core Execution Rules) — every
  section's body text, not only headings, regardless of the chat language.
- Determine the timestamp by running: `date +%Y%m%d-%H%M%S`.
- Save as `plans/{timestamp}_plan.md`. If that path already exists, use the lowest
  available zero-padded sequence (`plans/{timestamp}_01_plan.md`,
  `plans/{timestamp}_02_plan.md`, ...). An existing file MUST NOT be overwritten.
- Use the section order and structure from `SKILL.md` Output format.
- Assign every requirement a stable ID (`REQ-001`, `REQ-002`, ...). Each Acceptance
  criterion, Test, and Implementation step must reference its related Requirement ID.
- Populate `Implementation Target Files` and `Reference Files` per `templates/plan.md`:
  one explicit repository-relative file path per row — never a directory, glob
  pattern, component/module name, file group, or a vague phrase such as "related
  files" or "as necessary". Give a test, configuration, schema, migration, deployment,
  or documentation file its own row when it requires modification, rather than folding
  it into the row for the source file it accompanies. Every `Repository Evidence`
  entry must cite what Step 3's inspection actually found — do not infer it.
- Every claim must be backed by evidence gathered above (or, for Path A, by Step 3's
  direct verification).
- Implementation steps must be small enough to be independently revertable.
- A deploy step MUST be included if `scripts/`/`config/` changes; an MCP service map
  update MUST be included if a new server is added.
- Do not include speculative steps — only steps required by the stated goal.
- The Plan must be detailed enough for the next pipeline phase (per Workflow position
  above) to produce file-level implementation procedures from it. Do not implement
  anything.

---

## Step 6: Analyze Unknowns and Risks

- Write any generated `issues/{timestamp}_unknowns.md` / `issues/{timestamp}_risks.md`
  file in English (see `SKILL.md` Core Execution Rules), same as the Plan.
- Include the items carried forward from Step 2's `Needs confirmation` classifications
  as Unknowns, in addition to any Unknowns identified during Steps 3-5.
- Resolve Unknowns only when supported by repository evidence.
- If a blocking ambiguity remains (`BLOCKING: True`), stop and request clarification.
- Record non-blocking Unknowns in the Plan's Unknowns table
  (`ID | Unknown Description | Evidence Missing | Resolution Path | Blocking?`). Only
  create `issues/{timestamp}_unknowns.md` (GitHub Issue Markdown format, one issue per
  section) when at least one Unknown is `BLOCKING: True` or otherwise requires
  standalone tracking beyond the Plan's inline table.
- Analyze every Risk and add a mitigation (Risk + likelihood + mitigation). Only file
  `issues/{timestamp}_risks.md` the same way when at least one Risk lacks a complete
  mitigation and needs separate follow-up.
- Do not create either file with placeholder or empty content — if the Plan's inline
  table fully captures every Unknown/Risk, do not also file a separate issue for it.
- When an Unknown/Risk issue file (or the Step 7 Requirement Traceability table)
  references a Requirement, cite its ID (e.g. `REQ-003`) — do not re-quote the full
  description text.
- Reuse the base timestamp from Step 5 (`date +%Y%m%d-%H%M%S`) for both files — do not
  regenerate.
- If either path already exists, apply the same lowest-available zero-padded sequence
  rule as Step 5 (`issues/{timestamp}_01_unknowns.md`, `issues/{timestamp}_01_risks.md`,
  ...). An existing file MUST NOT be overwritten.
- Each generated Unknown or Risk issue must include a Traceability section (per
  `templates/traceability.md`): Source issue = current Issue path; Source plan = the
  Step 5 Plan file.

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

Verify the Plan preserves: title/priority, target files, background, problem, reason for
change, implementation intent, implementation instructions, acceptance criteria, tests,
documentation impact, constraints/out-of-scope items, dependencies, assumptions,
unknowns, risks/mitigations, and Source Issue traceability.

Verify the Requirement Traceability subsection has at least one row per Requirement ID
(one per target file it affects) with all columns filled, including a Status entry
from Step 2.

Verify every Requirement ID is traceable to its Issue source/evidence, an implementation
step, an acceptance criterion, and a test/validation item.

Apply `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) — Initial validation, to every row of `Implementation Target Files`. Mark the
section `Frozen` only when every row is `Verified` and the section's additional checks
(no directory/glob/component/group/vague-phrase row, no file listed in both
`Implementation Target Files` and `Reference Files`) pass. Do not report `Pass` while
any row remains `Needs confirmation` or the section is not `Frozen`.

Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
is unmapped or untraceable, or `Implementation Target Files` is not `Frozen`, do not
report `Pass` or `Completed`.

Before delivering, cross-check (do not re-derive): goal is one sentence and verifiable;
scope has explicit in/out boundaries; assumptions are falsifiable; no blocking Unknowns
remain unresolved; claims are backed by tool evidence; implementation steps are
independently revertable with a deploy step if production files change; validation plan
has a full table; risks are stated with mitigations.

---

## Step 9: Final Validation

Report: generated Plan path; generated Unknown/Risk files (or `None`); number of
Requirements; number of `Implementation Target Files` rows; Path A/B classification
(one word; rationale is in the Plan's Design section, do not restate);
information-completeness result; traceability result; `Implementation Target Files`
freeze status (`Frozen` / not `Frozen` with reason); unresolved items count; and the
Issue pending move. Do not restate the Requirement Traceability evidence-classification
breakdown — it is already in the Plan's Requirement Traceability table.

No human approval is required for the move to `issues/done/`, per
`rules/workflow-lifecycle.md` Validation Reporting — proceed to Step 10 once Step 8 is
`Pass` and all required validations are `Pass`.

---

## Step 10: Move the Issue

This step MUST NOT be skipped. Apply `rules/workflow-lifecycle.md` Archival Move
(issue-to-plan section) — same before/after verification checklist and `Blocked`-on-
failure rule.

- Move the Issue once Step 9 confirms information completeness is `Pass` and all
  required validations are `Pass`.
- Use only: `git mv issues/{filename}.md issues/done/{filename}.md`. No `mv`,
  `cp` + `rm`, file-copy APIs, or other fallback.
- Report `Completed` only after successful verification.

---

## Out of Scope

See `rules/workflow-lifecycle.md` Global Safety Restrictions for the full list.
(Source code / `docs/*.md` scope: `skills/DESIGN.md` Analysis-only phase constraint,
declared in `SKILL.md` Purpose. File-scope restrictions: declared above in Allowed
file operations. Not repeated here.)

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
