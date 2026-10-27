# Issue Creator — Detailed Workflow

## Multi-file processing

When Phase 2 decides to split the work into multiple issues, apply `rules/ai-execution.md`
Sequential Target Processing (Base): draft, verify (Phase 9), and generate the filename
(Phase 10) for one issue completely before starting Phase 3 for the next — MUST NOT batch-draft
several issues' Phase 3-8 content before running Phase 9/10 on any of them. This also
prevents filename collisions, since Phase 10's uniqueness check sees each prior issue's file
already written.

## Batch mode

Entry condition: Phase 2 assigned the source's tasks to two or more issue groups. A single
issue skips this section.

- **Shared pre-investigation pass**: once, after Phase 2 and before Phase 3 of the first
  issue, verify the batch's claims against current source once per file or claim group.
  Phases 3-10 stay per-issue and sequential (Multi-file processing is unchanged).
- **Session notes**: record each result as a session note — the claim or file, the source
  evidence (path and symbol, or command), and the result (confirmed, refuted, or
  `Needs confirmation`). The notes are not a repository artifact; do not write them to a file.
- **Reuse**: each later draft cites the notes instead of re-reading a source. Re-read only
  for a claim the notes do not cover, or for a file that changed since it was read. If
  context compaction drops the notes, re-read the affected claim group once and re-note it.
- **Evidence rules unchanged**: Step 9a still runs per issue, and each draft's Background
  cites the notes' evidence.

## Merge into an existing issue

Use this only when the user asks to integrate findings into an existing open issue. The rule
in Phase 4 for a sibling that fully covers the problem (stop and report) is unchanged.

- Read the existing issue once in full.
- Apply all edits to it in one batch, keeping every `templates/issue.md` section intact.
- Run `uv run python tools/check_workitem_structure.py --file {issue}` once after the batch,
  and re-check the evidence labels of the sections that changed.

## Input from review findings

When called by `python-code-review` (Step 10b), map each finding as follows:

- Priority: assign by Phase 7's criteria, not by copying the finding's severity label.
- Finding location -> `Target Files or Areas`; cite the evidence under `Background`.
- Evidence label / confidence below confirmed -> `Unresolved Questions` (per Step 9a).
- Suggested fix -> `Implementation Intent` at the responsibility level, not as a code patch.

### From test-audit Tasks

One issue per Task (`Workflow phase`: `test-audit`). Priority by Phase 7, not the Task's `P1`.

- Goal -> `Title` and `Summary`.
- The Findings the Task `Addresses` (why the tests are insufficient, the uncovered risk) ->
  `Problem` and `Background`; cite the Task ID and Finding IDs there.
- Actions -> `Required Changes`; Acceptance Criteria -> `Acceptance Criteria`.
- Affected Files -> `Target Files or Areas`; Depends On -> `Dependencies` (as paths).
- The Task's Test Cases -> `Testing Expectations`.

### From python-refactoring Proposals

One issue per Proposal (`Workflow phase`: `python-refactoring`). A Proposal is a change that
was not made because it may alter behavior, so state in `Constraints` that the behavior
change is intended here.

- Title -> `Title`; Reason -> `Reason for Change`.
- Behavior risk -> `Constraints` and `Unresolved Questions`.
- Affected files -> `Target Files or Areas`.
- Suggested follow-up issue -> `Summary` and `Implementation Intent`.
- Recommended validation -> `Testing Expectations` and `Acceptance Criteria`.

## Phase 1: Classify and Frame

Identify the source of the work:
- review findings, investigation notes, an implementation plan, or a raw user request

Identify:
- scope of the work described
- whether requirements are complete or need assumptions
- whether the source already provides evidence (code review, investigation) or is request-only

If requirements are incomplete, mark assumptions and open questions instead of inventing
missing requirements — record them in the issue's `Unresolved Questions` section
(per `templates/issue.md`), not only in this phase's internal reasoning.

**Completed when**: source, scope, and completeness (complete vs. needs assumptions) are all
recorded, and any incomplete requirement has a corresponding assumption or open question.
**Stop and ask the user before Phase 2 when**: the scope of the work cannot be determined
even provisionally — there is nothing to group or draft against. Any other incompleteness is
recorded as an assumption/open question and framing continues.

---

## Phase 2: Task Grouping

Decide whether to split work into multiple issues or group it into one.

### Group tasks into one issue only when

- they modify the same file or tightly coupled files
- they are part of the same reviewable change
- separating them would cause duplicate work
- they share the same acceptance criteria
- they must be tested together

### Split into separate issues when

- they affect unrelated areas
- they have different owners
- one can be completed safely without the other
- they require different validation strategies
- grouping would make review harder

**Completed when**: every task from Phase 1's scope has been assigned to exactly one issue
group, using the criteria above (grouping and splitting are mutually exclusive per pair of
tasks — a pair matching a "Group" criterion is not also split, and vice versa).

---

## Phase 3: Draft Title, Summary, Background, Problem, Reason for Change, and Implementation Intent

**Title** — the `# <Issue Title>` line: a short statement of the task's outcome. The filename
slug (Phase 10) is derived from it.

**Summary** — a brief description of the task and the intended outcome, per `templates/issue.md`.

**Background** — why this requirement exists: prior context, history, related decisions.
Use `N/A: covered by Summary` when `Summary` already says everything relevant.

**Problem** — the concrete problem being solved, stated separately from the general
`Summary`. Use `N/A: {short reason}` for proposals that are not problem-driven.

**Reason for Change** — explain why the change is needed now. Include relevant context: current
problem, maintenance risk, operational risk, correctness risk, documentation/code mismatch,
user or developer impact. If nothing makes the change time-sensitive, say so; timing belongs
here, severity belongs in Priority (Phase 7).

**Implementation Intent** — explain the high-level approach. Focus on responsibility
boundaries, minimal change, expected design direction, what should be preserved, and what
should not be changed. Name a specific file, function, or line number only when the boundary
itself is the design decision (see `skills/DESIGN.md` Avoid implementation-reference
duplication) — otherwise describe the responsibility, not the location.

**Completed when**: Title and Summary are written, and Background, Problem, Reason for
Change, and Implementation Intent are each filled or explicitly marked `N/A` with a stated reason.

---

## Phase 4: Scope and Boundaries

**Target Files or Areas** — list only likely relevant files or areas. MUST NOT list the entire
repository. Use `Unknown` if the exact file is not confirmed.

**Required Changes** — list concrete changes as small, actionable bullets.

**Constraints** — technical or domain constraints that bound the solution space
(compatibility, performance, security, operational). Use `N/A: {short reason}` if none apply.

**Out of Scope** — list what must not be changed in this issue.

**Sibling-issue check** — run this before filling Dependencies, in two tiers.

Tier 1 lists candidates without reading bodies: the open issues under `issues/`, the
in-flight plans under `plans/`, and the recently archived issues under `issues/done/` that
touch the same files, tests, or failure group, identified by filename, title, summary line,
Target Files, and keywords. For example:

```bash
rg -l -F "<target path>" issues plans            # open issues and in-flight plans
ls issues/done | rg "^<yyyymmdd>"                # archived issues by date prefix
rg -l -F "<target path>" issues/done/<matching files>
```

Tier 2 reads the full body only of candidates that share a target file or failure group. In
batch mode, run tier 1 once for the union of the batch's target files and reuse its result
for each issue.

`issues/done/` is large (over a thousand files), so narrow it by the filename's timestamp
prefix first; this skill treats the last 30 days as recent (a proposed window; widen it when
the failure group is older). Record each overlapping open issue or plan as a Dependency with
the fix order. Write each Dependency as the other item's repository-relative path, the
direction (`depends on` or `blocks`), and the required order, because `issue-to-plan` looks
dependencies up by path or slug (an `{id}` alone is not unique). When a sibling's fix may remove this issue's
cause, state in `Background` that this issue must be re-verified against current source after
the sibling is resolved. MUST NOT file an issue whose problem a sibling already fully covers:
in that case stop, do not write the file, and report the sibling's path to the user.

**Dependencies** — other issues, plans, or external work this issue depends on, or
that depend on it, including the siblings found above. Use `N/A: none` if there are none.

**Completed when**: the sibling-issue check has run and its result is recorded in
Dependencies (or `N/A: none` because nothing overlaps), and Target Files or Areas, Required
Changes, Constraints, Out of Scope, and Dependencies are each filled or explicitly marked
`N/A`/`Unknown` per the template's convention.

---

## Phase 5: Acceptance Criteria and Testing

**Acceptance Criteria** — list verifiable completion criteria. Each item should be testable
by review, test execution, or documentation inspection.

**Testing Expectations** — include when relevant: unit tests, integration tests, regression
tests, type checks, lint checks, documentation consistency checks, manual verification. Use
`Not required` only when the task is documentation-only or clearly does not affect behavior.

**Completed when**: every Acceptance Criteria item is independently testable, and Testing
Expectations is filled or marked `Not required` only for a documentation-only/no-behavior-change task.

---

## Phase 6: Documentation Impact

State whether documentation must be updated. If affected, specify what kind of information
should be documented: intent, boundaries, constraints, failure behavior, operational notes,
Known Issues, Needs Confirmation items.

### Documentation cleanup rules

For documentation-related issues, focus on: design intent, responsibility boundaries,
constraints, design decisions, operational notes, failure behavior, Known Issues, Needs
Confirmation items.

Apply `skills/DESIGN.md` "Avoid implementation-reference duplication" and "Docs content
policy — remove" to the documentation changes this issue asks implementers to make: the issue
MUST NOT request adding any content those sections forbid.

If implementation-derived details are currently present, prefer in this order: remove,
compress, replace with source reference, move to Known Issues, move to Needs Confirmation.

**Completed when**: Documentation Impact states whether documentation must be updated and, if so, the kind of information affected.

---

## Phase 7: Priority Assignment

### High

Tasks that affect: correctness, data integrity, security-sensitive behavior, startup or
deployment failure, workflow execution, public API behavior, production reliability,
critical documentation/code mismatch.

### Medium

Tasks that affect: maintainability, testability, type safety, unclear ownership, ambiguous
configuration behavior, non-critical documentation/code mismatch, documentation structure
that affects AI or developer usability.

### Low

Tasks such as: wording cleanup, small metadata cleanup, minor formatting improvements,
opportunistic link descriptions, non-blocking consistency improvements.

### Tie-breaking

- When a task matches more than one tier, assign the highest tier whose criterion is
  supported by evidence cited in the issue — not by speculation.
- "Critical" documentation/code mismatch means the mismatch can make an operator or
  implementer take a wrong action (e.g. a wrong command, a wrong safety rule, a wrong
  startup step). A mismatch that only misleads understanding is Medium.

**Completed when**: exactly one of High/Medium/Low is assigned, matching the criteria
stated above for that tier.

---

## Phase 8: AI Implementation Instruction

Give concise instructions for an AI coding agent. Include constraints such as: do not
rewrite unrelated files, keep changes minimal, preserve public behavior unless explicitly
required, stop and report open questions if requirements are unclear, do not implement
out-of-scope items.

**Completed when**: the AI Implementation Instruction states concrete constraints an
implementer must follow (not a generic restatement of Phase 4's Out of Scope).

---

## Phase 9: Evidence, Markdown Safety, and Final Checklist

This phase has three sub-steps, applied in order: verify evidence (9a), verify markdown
safety (9b), then run the final checklist (9c). It checks the drafted issue before the file
exists; Phase 10 Step 10.4 re-verifies the written file.

### Step 9a: Evidence and assumptions

When the issue is based on code review or investigation, apply `skills/DESIGN.md` Evidence
labels and Confidence levels — MUST NOT invent a parallel confirmed/assumption/unknown scheme.

When the issue is based on a user request only:
- state assumptions clearly
- include open questions if requirements are incomplete
- MUST NOT invent missing requirements

**Completed when**: every claim in the issue is either backed by cited evidence (code
review/investigation) or explicitly marked as an assumption/open question.

### Step 9b: Markdown safety rules

- When the user asks for issue text in chat instead of (or in addition to) a file, emit each
  issue as a separate Markdown block.
- Avoid nested triple-backtick blocks inside issue bodies.
- If code examples are unavoidable, prefer indented examples or short inline snippets.
- MUST NOT put large code blocks inside Markdown tables.
- Use bullet lists instead of complex tables when copy-paste safety matters.
- Keep headings consistent.
- Ensure every opened list, quote, or block is closed.

**Completed when**: every rule above has been checked against the drafted issue body.

### Step 9c: Final checklist

Before finalizing issues, verify:
- [ ] each issue is actionable
- [ ] Background, Problem, Reason for Change, and Implementation Intent meet Phase 3
  (or are explicitly `N/A` with a reason)
- [ ] Acceptance Criteria and Testing Expectations meet Phase 5
- [ ] Constraints, Out of Scope, and Dependencies are explicit (or `N/A`), per Phase 4
- [ ] Unresolved Questions reflects every open assumption from Phase 1 (or is `N/A: none`)
- [ ] grouping follows Phase 2 criteria
- [ ] Markdown safety follows Step 9b
- [ ] no secrets or sensitive data are included (See `skills/DESIGN.md`, section "No secrets in output")
- [ ] the issue follows `templates/issue.md`'s field order and names exactly

**Completed when**: every checked item above is true.
**On an unchecked item**: return to the phase that owns it (Phase 1–8, or Step 9a/9b above)
and fix only the gap the item identifies — MUST NOT redo the whole phase's output. Then
re-check only that item, not the full checklist, before proceeding to Phase 10.
Per `AGENTS.md` Loop Prevention > Attempt Limit, this loop tolerates at most 3 attempts per
distinct unchecked item; if it still fails, stop and report
`Blocked: {item} still unresolved after 3 attempts` rather than continuing to patch.

---

## Phase 10: Write and Verify the Issue File

Phase 9 verified the draft; this phase writes it to `issues/` and verifies the written file.
Steps 1-5 apply per issue (see Multi-file processing).

### Step 10.1: Derive `{id}` and `{slug}`

Per `SKILL.md` Issue Filename Generation:

- `{id}`: `[a-z0-9]+` (e.g., `NC-019` -> `nc019`); generic prefix + `SKILL.md` Numbering when none exists.
- `{slug}`: derived from the issue title under the `SKILL.md` slug rules.

### Step 10.2: Scaffold the file

Default: `uv run python tools/generate_workitem.py --kind issue --id {id} --title {slug}`.

Direct writing from the `templates/issue.md` skeleton is allowed only when all of these hold:

- (a) the skeleton (the fenced block of `templates/issue.md`) was read in this session and
  the template has not changed since;
- (b) the exact target path was verified absent from `issues/` and `issues/done/`
  immediately before the write;
- (c) the filename passed the name checks below (pattern and at most 4 slug words) before
  the write;
- (d) Step 10.4 verification runs on the written file and passes.

Otherwise, and whenever the tool is unavailable, use the tool path (or the manual procedure
below). A direct write MUST reproduce what the tool guarantees: the exact-path absence check
in both directories (never a `{timestamp}_*` glob), the skeleton verbatim (every heading of
the fenced block, in template order, none dropped), and the name verification. The name
verification and Step 10.2a apply to both paths.

Tool path notes:

- The tool's `--title` only builds the filename (lowercases, spaces to dashes). Pass the
  already-normalized `{slug}` from Step 10.1, not the raw title.
- The tool writes `templates/issue.md`'s skeleton verbatim (placeholders only). It does not
  set the `# <Issue Title>` line, `Generated at`, or any other field.
- It refuses (non-zero exit, no write) when the path already exists in `issues/` or
  `issues/done/`. Treat that refusal as the trigger for the retry in Step 10.2a, not as a
  workflow failure.
- After a `0` exit, independently verify the reported output path exists and contains the
  expected `## ` section headings before filling it in — per `rules/ai-execution.md`
  Repository Tool Usage item 8, a `0` exit alone MUST NOT be treated as proof the file was
  written correctly.
- The tool validates neither `--id` nor the slug, so verify the name yourself:

  ```bash
  basename <path> | rg -c -x '[0-9]{8}-[0-9]{6}_[a-z0-9]+_[a-z0-9_-]+\.md'   # prints 1 on a match
  echo "<slug>" | tr '_-' '\n\n' | rg -c .                                   # word count, at most 4
  ```

  A name that fails either check is wrong: remove the scaffold file you just created
  (single path) and regenerate with a corrected `{id}` or `{slug}`.

Manual procedure (when the tool is unavailable, or for a direct write under the conditions above):

1. Generate `{timestamp}` as `YYYYMMDD-HHmmss` with `date +%Y%m%d-%H%M%S`.
2. Assemble `issues/{timestamp}_{id}_{slug}.md`.
3. Confirm `issues/` exists, then verify that exact path does not exist in `issues/` or
   `issues/done/` before writing (a glob on `{timestamp}_*` is not a substitute: it does not
   cover `issues/done/`). Create the file from the `templates/issue.md` skeleton.

### Step 10.2a: On a collision

Regenerate with the next available disambiguator — append digits to `{id}` or a word to
`{slug}`, keeping both within their character classes — and re-check, applying
`rules/filename-collision.md` Collision Retry Bound.

### Step 10.3: Fill every placeholder

Write the Phase 1-8 content into the file created by either path, replacing every placeholder — including the
`# <Issue Title>` line and the Traceability fields:

- `Workflow phase`: the workflow that produced this issue (`issue-creator`, or the caller such
  as `python-code-review`), or `N/A: manually filed`.
- `Generated at`: the `{timestamp}` of the filename (the same value, not a second `date` call).
- `Source plan` / `Source implementation procedure`: per `templates/issue.md` Field notes.
- `Related target files`: restates `Target Files or Areas`; do not keep a divergent list.

### Step 10.4: Verify the written file

- Run `uv run python tools/check_workitem_structure.py --file issues/{filename}.md`. It checks
  that every required `## ` section is present; it does not judge content, so the Phase 9c
  checklist still applies to the filled text.
- Confirm no template placeholder (`{...}`, `<Issue Title>`) remains. The checker cannot see
  the template's instruction sentences under each heading (for example `High / Medium /
  Low` or `Briefly describe the task and the intended outcome.`), so replace each of them
  with real content and then check that none survives verbatim:

  ```bash
  tmp=$(mktemp)
  sed -n '/^```markdown/,/^```$/p' templates/issue.md | sed '1d;$d' | rg -v '^(#|- |$)' > "$tmp"
  rg -n -F -x -f "$tmp" issues/{filename}.md    # any output is a leftover template line
  rm "$tmp"
  ```

  (On a filled issue this prints nothing; on the unfilled scaffold it prints every
  instruction line.) For `{...}`, run `rg -n '\{[^}]*\}|<Issue Title>' issues/{filename}.md`
  and judge each hit: braces that belong to the issue's own content are fine.

### Step 10.5: Report to the user

Return, in Japanese:

- the written path(s), or the `Blocked` reason
- each issue's Priority and one-line Summary
- every Unresolved Question and assumption, labeled `不明` where applicable, so the user can
  confirm or correct them
- next steps: the new issue files are uncommitted, so `git-commit-and-sync` commits them;
  `issue-to-plan` then takes each issue. This skill does neither itself.

**This task is complete when, and only when**: the issue file has been written to `issues/`
at its verified-unique filename, passed Step 10.4, and been reported in Step 10.5, or the
cycle ended in a `Blocked` state per Phase 9c, the sibling-issue check in Phase 4, or this
Phase's own stop condition — in either case, for a Multi-file batch (see Multi-file
processing above), proceed to Phase 3 for the next issue only after this one's outcome
(written or `Blocked`) is settled.
