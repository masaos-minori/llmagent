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

No standalone requirement document (`requires/*.md`) is produced. Evidence
verification and planning happen in one continuous cycle, Steps 1-10 below.

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `grimp` | architecture analysis | Import graph with layering and cycle detection |
| `pyan3` | architecture analysis | Call graph and module dependency visualization |
| `import-linter` | architecture analysis | Enforce declared module boundary contracts |
| `networkx` | architecture analysis | Graph analysis (centrality, paths, cycles) |
| `pydeps` | dependency graphing | Visual module dependency graph |
| `universal-ctags` | dependency graphing | Symbol index across the entire codebase |
| `radon` | validation quality analysis | Cyclomatic complexity and maintainability index |
| `vulture` | validation quality analysis | Dead code detection |
| `semgrep` | validation quality analysis | Semantic pattern matching |
| `bandit` | validation quality analysis | Static security analysis |
| `pip-audit` | operational dependency inspection | Vulnerability scan of installed packages |
| `diff-cover` | validation quality analysis | Coverage gate scoped to changed lines |
| `pytest-testmon` | validation quality analysis | Impact-based test selection |
| `git-fame` | historical analysis | Per-author contribution breakdown |
| `git churn` | historical analysis | Change frequency by file |
| `git bisect` | historical analysis | Binary search for regression commit |
| `lsof` | operational dependency inspection | Open files and socket connections |
| `rg` | — | Symbol definitions, call sites, log strings |
| `fd` | — | File listing by pattern |
| `ast-grep` | — | Structural code patterns |

---

## Multi-file processing

If multiple target Issue files are specified, treat Steps 1-10 as one complete cycle per
file: finish every step for the current file (through moving it to `issues/done/` in
Step 10) before starting Step 1 for the next file. Do not batch-read multiple target
files up front, and do not interleave steps across files.

- Perform Step 2 (verifying claims in the Issue against current source) sequentially.
  Retain only a concise confirmation or correction, not full file contents.
- When multiple target Issue files are specified, process each Steps 1-10 cycle
  sequentially for context hygiene only, so investigation from one file's cycle does not
  accumulate into the next. This is for context isolation, not parallel execution: run
  each cycle one at a time, never in parallel.
- Keep start/end progress reports to one or two lines; do not restate full document
  content in progress reports.
- `review_mode`: in `review_mode = manual` (the default), stop after Step 9 and wait for
  explicit user approval before Step 10. In `review_mode = autonomous`, proceed directly
  from Step 9 to Step 10, reporting the Plan path and a validation summary. The default
  is `manual` unless the invoking context states otherwise.

Report progress at the start and end of each step.

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`,
`templates/traceability.md`, `templates/requirement-traceability.md`, `SKILL.md` (this
skill), and this file.

Before reusing previously loaded shared files from an earlier cycle in this session,
check their modified time or checksum. If any shared file changed, reload only the
changed shared file.

---

## Step 1: Identify Target Issues

- The target Issue file(s) are provided by the user (e.g. `issues/{filename}.md`), one
  path per file. The user may specify one file or a list of multiple files.
- If no target file is specified, stop immediately and ask the user to specify one or
  more.
- If any specified file does not exist, stop immediately and report which file(s) are
  missing. Do not start processing any file until all specified paths are confirmed to
  exist.
- If multiple target files are specified, process them in filename (lexicographic)
  order.
- Do not read files under `issues/done/`.
- Do not preload later Issues.

---

## Step 2: Assess the Current Issue

- Read the current Issue file in full.
- Verify any factual claims against current source (affected files, whether the
  described problem still reproduces).
- Extract: title, priority, target files, background, problem, reason for change,
  implementation intent, implementation instructions, acceptance criteria, tests,
  constraints, dependencies, and unresolved questions.
- Classify each extracted item as one of: `Explicit in issue`, `Confirmed by repository
  evidence`, `Derived from confirmed evidence`, `Needs confirmation`. Do not invent
  missing requirements.
- Any item classified `Needs confirmation` carries forward to Step 6 as an Unknown by
  name — do not re-derive it there. This classification is also the source for the
  Requirement Traceability table's Status column in Step 7.
- If the Issue is already resolved, cannot be reproduced, or no longer applies: stop,
  report the supporting evidence, do not create a Plan, and proceed to Step 9/10 to move
  it to `issues/done/` (same `git mv`-only procedure, no separate path).
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

---

## Step 4: Map Issue Information to Plan Information

Create an explicit mapping before writing the Plan:

| Issue item | Plan destination |
|---|---|
| Title | Goal |
| Priority | Priority |
| Target files | Affected areas, Related target files |
| Background | Background |
| Problem | Problem |
| Reason for change | Reason for change |
| Implementation intent | Implementation intent, Design |
| Implementation instructions | Requirements, Implementation steps |
| Acceptance criteria | Acceptance criteria, Validation plan |
| Tests | Tests, Validation plan |
| Constraints | Scope, Assumptions, Risks |
| Unresolved questions | Unknowns |
| Repository evidence (Step 2/3) | Design, Risks, Validation plan |
| Source Issue path | Traceability |

No requirement information may remain unmapped. If information has no suitable
destination, add an appropriate Plan section instead of discarding it. This mapping step
runs identically for Path A and Path B — task-size classification does not reduce
mapping completeness, only analysis depth (Steps 3 and 5).

---

## Step 5: Create the Plan

Using the Path A/B classification from Step 3:

- **Path A**: skip architecture analysis, dependency graphing, historical analysis, and
  operational dependency inspection (below). Still establish the validation quality
  baseline (radon/vulture/semgrep/bandit/diff-cover, lightweight or full as installed) —
  this baseline is not part of what Path A skips, matching this skill's Path A
  definition in `SKILL.md`.
- **Path B**: perform all of the following before creating the Plan.

**Lightweight alternatives are always available; heavy tools only if installed — see
`skills/DESIGN.md` Tool availability guard.**

#### Architecture analysis

```bash
rg "^from|^import" scripts/<module>.py | sort -u
lint-imports
cat .importlinter
```

`grimp` / `pyan3` / `networkx` for deeper import-graph, call-graph, and centrality
analysis if installed — see the Toolchain table above for tool roles; invocation
syntax is unchanged from prior usage of these tools.

#### Dependency graphing

```bash
rg "from <module> import" scripts/
rg "def <function>" scripts/
ast-grep --pattern '<Class>($$$)' --lang python scripts/
```

Build a concrete list: "these N files will require changes." `pydeps` /
`universal-ctags` if installed.

#### Historical analysis

```bash
git log --oneline --diff-filter=M -- scripts/ | awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

High-churn files are riskier to touch. `git bisect` for regression localization if the
Issue describes a known regression. `git-fame` for bus-factor if installed (>70% single
author = flag as high bus factor).

#### Operational dependency inspection

```bash
lsof -p <PID> | grep -E 'REG|IPv4|IPv6'
lsof -i :<PORT>
```

Before planning a change to MCP servers or the DB: confirm no process holds locks.
`pip-audit` before planning any dependency upgrade.

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

- Determine the timestamp by running: `date +%Y%m%d-%H%M%S`.
- Save as `plans/{timestamp}_plan.md`. If that path already exists, use the lowest
  available zero-padded sequence (`plans/{timestamp}_01_plan.md`,
  `plans/{timestamp}_02_plan.md`, ...). Never overwrite an existing file.
- Use the section order and structure from `SKILL.md` Output format.
- Assign every requirement a stable ID (`REQ-001`, `REQ-002`, ...). Each Acceptance
  criterion, Test, and Implementation step must reference its related Requirement ID.
- Every claim must be backed by evidence gathered above (or, for Path A, by Step 3's
  direct verification).
- Implementation steps must be small enough to be independently revertable.
- Always include a deploy step if `scripts/`/`config/` changes; always include an MCP
  service map update if a new server is added.
- Do not include speculative steps — only steps required by the stated goal.
- The Plan must be detailed enough for `prompts/02_plan-to-implementation-procedure.md`
  to produce file-level implementation procedures. Do not implement anything.

---

## Step 6: Analyze Unknowns and Risks

- Include the items carried forward from Step 2's `Needs confirmation` classifications
  as Unknowns, in addition to any Unknowns identified during Steps 3-5.
- Resolve Unknowns only when supported by repository evidence.
- If a blocking ambiguity remains (`BLOCKING: True`), stop and request clarification.
- Record non-blocking Unknowns in the Plan's Unknowns table
  (`ID | Unknown Description | Evidence Missing | Resolution Path | Blocking?`); when
  necessary, also file `issues/{timestamp}_unknowns.md` (GitHub Issue Markdown format,
  one issue per section). Never overwrite an existing file.
- Analyze every Risk and add a mitigation (Risk + likelihood + mitigation). When
  necessary, file `issues/{timestamp}_risks.md` the same way.

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
constraints/out-of-scope items, dependencies, assumptions, unknowns, risks/mitigations,
and Source Issue traceability.

Verify the Requirement Traceability subsection has one row per Requirement ID with all
columns filled, including a Status entry from Step 2.

Verify every Requirement ID is traceable to its Issue source/evidence, an implementation
step, an acceptance criterion, and a test/validation item.

Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
is unmapped or untraceable, do not report `Pass` or `Completed`.

Before delivering, cross-check (do not re-derive): goal is one sentence and verifiable;
scope has explicit in/out boundaries; assumptions are falsifiable; no blocking Unknowns
remain unresolved; claims are backed by tool evidence; implementation steps are
independently revertable with a deploy step if production files change; validation plan
has a full table; risks are stated with mitigations.

---

## Step 9: Validate and Await Approval

Report: generated Plan path; generated Unknown/Risk files; number of Requirements; the
Path A/B classification and its rationale; information-completeness result;
traceability result; Requirement Traceability completeness result (with a breakdown of
how many Requirements fall under each Step 2 evidence classification); unresolved
items; and the Issue pending move.

Set state to `Awaiting approval` and stop (per `review_mode`, see Multi-file processing
above). Do not move the Issue in the same response. An unclear user response must not be
treated as approval.

---

## Step 10: Move the Issue After Approval

**This step is mandatory. Do not skip it.**

- Move the Issue only after explicit user approval (or immediately in
  `review_mode = autonomous`).
- Use only: `git mv issues/{filename}.md issues/done/{filename}.md`. Do not use `mv`,
  `cp` + `rm`, file-copy APIs, or any fallback move method.
- Before running `git mv`, verify: state is `Awaiting approval`; approval applies to the
  current Issue; information completeness is `Pass`; all required validations are
  `Pass`; source exists; destination does not exist; `issues/done/` exists.
- After running `git mv`, verify: destination exists; source no longer exists; Git
  records the change as a rename or staged move.
- If `git mv` fails, do not use a fallback. Report `Blocked`.
- Report `Completed` only after successful verification.

---

## Out of Scope

Do not perform any of the following as part of this workflow. (Source code and
`docs/*.md` are already out of scope per `skills/DESIGN.md` Analysis-only phase
constraint, declared once in `SKILL.md` Purpose — not repeated here.)
- unrelated refactoring
- broad formatting-only rewrites
- moving existing documentation files
- changing workflow directory structure
- changing implementation behavior during document-only phases
- processing files under `__pycache__/`
- interleaving multiple target files
- parallel processing of target-file cycles
- modifying files outside `plans/`, `issues/`, and the Issue file being moved
  (`issues/` -> `issues/done/`)

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
