You are a senior software architect and skills organizer.

Read the existing skill files and routing configuration, then restructure them based on the Context Loader Pattern below.

- Do not rewrite files from scratch without reading them first.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Scope

**In scope for reading and editing** (this workflow's Allowed file operations):
- `AGENTS.md`
- `routing.md`
- `skills/DESIGN.md`
- `rules/*.md`
- `skills/**/*.md` — every `SKILL.md`, `workflow.md`, and any split file under a skill
  directory (e.g. `path-a.md`, `discovery.md`, `report-template.md`)
- `prompts/*.md` — entry-point prompts; audit them for restated content the same as
  any skill file

**Out of scope** (MUST NOT be read for content, MUST NOT be edited by this workflow):
- `scripts/`, `tests/` — source code
- `docs/*.md` — product documentation (owned by the `python-documentation` skill, a
  different workflow)
- `templates/*.md` — structural format definitions only; not a source of normative
  rule text to deduplicate
- `issues/`, `plans/`, `implementations/`, and their `done/` subdirectories —
  pipeline documents, frozen once archived; an already-`done/` file MUST NOT be edited
- `.claude/commands/*.md` — check and update only when a Relocation Plan item (Step
  2) explicitly names one as citing content that moved (e.g. a renamed section
  heading); MUST NOT be treated as a primary duplication-scan target

If a task instruction elsewhere in the session conflicts with this Scope, apply
`rules/ai-execution.md` Instruction Precedence before proceeding.

### Architectural Principles

These MUST be followed throughout all steps:

- **routing**: All task-to-skill mappings MUST go through `routing.md`; it MUST NOT be bypassed by loading skills or docs directly.
- **dependency direction**: Apply this direction: `agent -> rag/mcp -> db -> shared`. The arrow means "may depend on or reference".
  - `agent` may reference `rag`, `mcp`, `db`, and `shared`.
  - `rag` and `mcp` may reference `db` and `shared`.
  - `db` may reference `shared`.
  - `shared` must not reference higher layers.
  - A lower layer must not reference a higher layer.
  - `rag` and `mcp` are sibling layers.
  - `rag` and `mcp` must not reference each other unless an approved rule explicitly allows it.
  - Do not confuse layer display order with dependency direction.
- **minimal loading**: Load only the minimum skill files required for the current task. Do not load entire skill directories unless specifically needed. Prefer loading individual rule files over entire skill workflows. See Context Loader Pattern Validation below for how this is measured, not just asserted.
- **shared normalization**: Rules and conventions shared across multiple skills must be defined once — in `skills/DESIGN.md` for design/architecture rules, or in `rules/*.md` for shared AI-execution/lifecycle rules (see Canonical Ownership Model) — and referenced, not duplicated.

Context Loader Pattern (the target structure):

```
Task
  ↓
Routing
  ↓
Minimal Skills
  ↓
Shared Rules
  ↓
Execution
```

### Canonical Ownership Model

- `AGENTS.md`: repository-wide AI execution constraints that every task needs, and an
  instruction to consult `routing.md`. Must be loaded first by any AI agent. Contains
  global safety restrictions and execution rules.
- `routing.md`: the only canonical source for task-to-skill mappings and
  source-to-document mappings.
- `skills/DESIGN.md`: shared design and architecture rules used by 2+ skills.
- `rules/*.md`: shared AI-execution or workflow-lifecycle rules used by 2+ workflows
  but not universal enough for every task to need them (e.g. `rules/ai-execution.md`,
  `rules/workflow-lifecycle.md`) — loaded selectively by the `SKILL.md`/`workflow.md`
  files that reference them, per "minimal loading". This is what distinguishes a
  `rules/*.md` rule from an `AGENTS.md` rule: `AGENTS.md` content is always loaded;
  `rules/*.md` content is loaded only by the workflows that need it.
- `skills/<task>/SKILL.md`: task-specific procedures and checklists.

Do not place task-to-skill mappings in `AGENTS.md`. Do not duplicate routing definitions in other files.

#### The `AGENTS.md` vs. `rules/*.md` boundary test

This boundary has been ambiguous in practice. Apply this test, in order, whenever a
candidate rule could plausibly belong to either:

1. **Universality check**: would this rule apply to every task this repository
   executes, regardless of which skill (or no skill) handles it? If yes → `AGENTS.md`.
   If the rule only makes sense in the context of a structured, multi-step workflow
   (it presupposes "the active workflow", "a target file", "a phase gate", or similar
   workflow machinery) → `rules/*.md`.
2. **Adoption check** (use when the universality check is unclear): count how many of
   `skills/DESIGN.md` Skill catalog's skills currently restate this rule independently,
   or would need it if written today. All, or all but a documented exception → treat as
   universal → `AGENTS.md`. A defined subset with at least one clear, legitimate
   counterexample skill that does not need it → `rules/*.md`.
3. **Size check** (tie-breaker): `AGENTS.md` is loaded on every single task (see
   Context Loading Flow) — a rule belongs there only if its benefit on every task
   outweighs its fixed per-task context cost. When still in doubt, default to
   `rules/*.md` and let skills reference it explicitly; promote to `AGENTS.md` only
   once evidenced by independent restatement across 3 or more skills — that is a
   concrete signal the rule is already being treated as universal in practice even
   though it was written as scoped.

Record which check resolved each Relocation Plan item (Step 2) — do not leave the
`AGENTS.md`/`rules/*.md` choice unexplained.

### Normative vs. Descriptive Content

Deduplicate normative content only. Apply this test per sentence or bullet, not per
section — a single section commonly mixes both:

- **Normative**: the sentence states or implies a constraint — it uses, or could be
  rephrased into, MUST / MUST NOT / SHOULD / MAY / "do not" / "always" / "never" /
  "required" / "prohibited" — and removing the sentence would change what an executor
  is permitted to do. Example: "do not use `git add -A` or `git add .`".
- **Descriptive**: the sentence explains *why* a rule exists, gives an example, or
  restates a normative rule's effect without adding a new constraint of its own.
  Removing it leaves the actual constraint unchanged elsewhere. Example: "`git add -A`
  stages everything in the repo, which can accidentally include unrelated files" — this
  explains the reason; the constraint itself lives in the adjacent normative sentence.

A short, one-sentence descriptive gloss attached to a canonical reference (e.g. "see
`rules/coding.md` Prohibited behavior — this is why we stage files individually here")
is allowed and does not need deduplicating. A descriptive paragraph that quietly
reintroduces the full original constraint in different words does need deduplicating.
Use this normative/descriptive split as the first filter (skip non-normative text
entirely), then test the remaining normative text with the Deduplication Rules'
scope/requirements/conditions/exceptions/effects equivalence test below.

### Deduplication Rules

- Treat content as duplicated only when its scope, requirements, conditions,
  exceptions, and effects are equivalent (apply this only to text that passed the
  Normative vs. Descriptive test above).
- Deduplicate normative rule text only.
- Allow short cross-references and non-normative summaries that do not introduce new
  requirements, prohibitions, conditions, or exceptions.
- Do not move a rule when its canonical owner is unclear. Mark it as `Deferred` and
  report the reason.
- Preserve all requirements, prohibitions, conditions, exceptions, and acceptance
  criteria when relocating a rule.

Decide a duplicate's canonical destination by content type, then replace every other
occurrence with a short cross-reference to that destination (see Canonical
References) — the rule's normative text MUST NOT be left repeated in more than one
place:

| Content type | Canonical destination |
|---|---|
| Task-to-skill or source-to-document mapping | `routing.md` |
| Repository-wide AI-execution or lifecycle rule used by 2+ workflows, not universal, not skill-specific | `rules/*.md` (e.g. `rules/ai-execution.md`, `rules/workflow-lifecycle.md`) |
| Shared design/architecture rule used by 2+ skills | `skills/DESIGN.md` |
| Task-specific procedure or checklist | The owning `skills/<task>/SKILL.md` (or its `workflow.md`) |
| Repository-wide AI execution constraint that every task needs (not task-specific, not a mapping) | `AGENTS.md` |

Use the `AGENTS.md` vs. `rules/*.md` boundary test above to choose between the last two
rows when a candidate could plausibly fit either.

Acceptance criteria:
- No normative rule appears in more than one file.
- Each piece of normative content has exactly one canonical location.
- All references to relocated content use the Canonical References format.
- `AGENTS.md` contains only execution constraints every task needs, plus the
  instruction to consult `routing.md` — no task-specific procedures, no task-to-skill
  mapping entries, and no rule that is only needed by some workflows (that belongs in
  `rules/*.md` instead).
- `skills/DESIGN.md` and `rules/*.md` contain only shared rules; no task-specific
  procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific
  skill files or any `rules/*.md` file.

### New File Creation Policy

This workflow reorganizes content across *existing* files by default. Creating a new
file is in scope only when the Relocation Plan (Step 2) explicitly proposes it, for one
of these two reasons:

1. **Split-on-relocation**: moving content into an existing canonical file would push
   it past `skills/DESIGN.md` File Split Rule's trigger (a single file exceeds 400
   lines AND contains multiple independent responsibilities). Apply that Rule's Four
   Principles (routing, dependency direction, minimal loading, shared normalization)
   and Procedure when this applies.
2. **No existing canonical home**: the Relocation Plan finds a genuinely new,
   cross-cutting concern that does not fit any existing Canonical Ownership Model row
   and is needed by 2 or more skills — propose a new `rules/<topic>.md` file (matching
   the existing `rules/*.md` naming convention) rather than forcing the content into an
   unrelated existing file.

Any new file must be named in the Relocation Plan with its proposed path, its initial
section headings, and which existing files will be edited to reference it afterward.
Do not create a file during Step 3 (Edit) that was not named in the Step 2 plan the
user approved.

### Canonical References

- Give canonical rules a stable heading or Rule ID.
- Reference canonical rules by file path and stable heading or Rule ID.
- Use line numbers only as supporting information because they may change after editing.
- Use this reference format:

  `See <file path>, section "<heading or Rule ID>".`

### Relocation Plan format (Step 2 output)

Report the Relocation Plan as a table, one row per duplicate candidate carried over
from Step 1's inventory:

| # | Content (summary) | Current location(s) | Canonical destination | Boundary test used (if `AGENTS.md`/`rules/*.md` was ambiguous) | Reference text to insert at each non-canonical location | New file? (Y/N + reason, per New File Creation Policy) |
|---|---|---|---|---|---|---|

An item with an unclear canonical owner is not included as a row here — report it
separately as `Deferred` with the reason, per Deduplication Rules.

### Editing Constraints (Step 3)

- Process one Relocation Plan row at a time.
- Move only the duplicated content and replace the original text with the planned
  canonical reference — do not also edit unrelated text in the same file.
- Do not rewrite an entire file when a section-level edit is sufficient.
- Do not overwrite pre-existing user changes.
- Stay within Scope above; do not modify source code or test files.

### Validation (Step 4)

- Verify that no normative meaning was lost during relocation.
- Verify all file paths, headings, Rule IDs, and Markdown references after editing.
- Verify that routing behavior still maps each task to the intended skill.
- Verify that `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, and
  task-specific skill files contain only content within their assigned
  responsibility.
- Report intentional routing changes separately with reasons.
- Report ambiguous or unsafe changes as `Deferred`.

### Context Loader Pattern Validation (Step 4)

In addition to Validation above, verify the Context Loader Pattern with these two
concrete, repeatable checks — do not report Step 4 `Pass` without running both.

**Minimal loading, measured**:
- For each skill touched by this cycle's Relocation Plan, compute its *default load
  size*: the combined line count (`wc -l`) of every file its `SKILL.md`/`workflow.md`
  Step 0 loads unconditionally. Do not count files loaded conditionally at a later step
  (e.g. a Path-specific file, or a file loaded only on a failure branch).
- Record this number from before and after the Step 3 edits, per skill.
- The Relocation Plan must not increase any skill's default load size unless the
  increase is justified in the plan (e.g. removing a multi-line restatement in exchange
  for one new reference line is an acceptable trade; adding a reference without
  removing the restatement it targets is not).
- Also compute the combined size of the universal default load (`AGENTS.md` +
  `routing.md`, loaded before any skill is chosen, via `wc -l`). Report this number in
  Step 5's final report every time this workflow runs, so growth is visible across
  runs.

**Circular reference check**:
- Build the reference graph: for every file in Scope, list every other in-scope file it
  references for canonical content (a `See <file>, section "<heading>"` citation, or an
  "Apply `<file>` `<section>`" instruction).
- The graph must respect the precedence order defined in `rules/ai-execution.md`,
  section "Instruction Precedence" — treat `skills/DESIGN.md` as ranked alongside
  `rules/*.md` in that order (both are shared-rules layers). Flag as an `Ownership
  violation` (not a duplicate) any reference that points from a lower-precedence file
  to a higher-precedence one for content the lower-precedence file is itself supposed
  to canonically own.
- The graph must contain no cycle (file A references file B for content whose
  definition itself references back to file A). Flag any cycle found as a `Circular
  reference` and report it — do not attempt to silently break it during Step 4; fixing
  it requires a new Step 1-2 pass.

### Step Responsibilities

- **Step 1 (Inventory)**: build the compact rule inventory and flag duplicate
  *candidates* only — record each candidate's scope, type, current owner(s), and
  evidence location. Apply the Normative vs. Descriptive test to decide what qualifies
  as a candidate. Do not decide canonical ownership and do not edit any file in this
  step.
- **Step 2 (Relocation Plan)**: for each candidate from Step 1, decide canonical
  ownership (Canonical Ownership Model + the `AGENTS.md`/`rules/*.md` boundary test),
  the exact destination file and heading, every source location to be replaced with a
  reference, and whether it requires a new file (New File Creation Policy). Produce the
  Relocation Plan table, then stop and report it — do not proceed to Step 3 in the same
  response. Resume at Step 3 only after explicit user approval of the plan; an approval
  given for a different task does not count. Do not edit any file in this step.
- **Step 3 (Edit)**: apply only the rows the user approved in Step 2, exactly as
  planned, per Editing Constraints. If executing a row reveals the plan does not match
  current file content (e.g. the target heading does not exist, or the source text
  differs from what Step 1 recorded), stop that row, mark it `Blocked: plan mismatch`,
  and do not improvise a different edit — report it for a new Step 1-2 pass rather than
  fixing it ad hoc.
- **Step 4 (Validate)**: apply Validation and Context Loader Pattern Validation above.
  Do not redo Step 1's detection or Step 2's planning here.
- **Step 5 (Report)**: report per Context Efficiency's format below.

Do not merge or skip any of these five steps, and do not perform a later step's work
while still inside an earlier one (e.g. do not edit a file while still building the
Step 1 inventory, and do not decide canonical ownership while still building the
inventory).

### Context Efficiency

Accuracy, completeness, and validation MUST take priority over context reduction.
Do not reduce context when doing so may cause missing evidence, incorrect
conclusions, incomplete plans, or insufficient validation.

Apply `rules/ai-execution.md` Context Reading, Tool Usage, Reasoning and Planning,
and Output for the general AI-execution baseline this workflow runs under. In
addition, specific to this workflow:

- Keep the full rule inventory internal. Retain only duplication candidates,
  ownership violations, and unresolved items in active context.
- Reuse unchanged shared files and verified inventory entries.
- Do not reread complete files when validating only an edited section.
- Read a complete file only when excerpts are insufficient to determine ownership,
  dependencies, conditions, exceptions, or lifecycle behavior.
- Keep progress reports to one line.
- Provide detailed progress only for `Blocked`, `Deferred`, or failed validation
  states.
- In the final report, list only modified files, relocated content, canonical
  destinations, deferred items, the two Context Loader Pattern Validation
  measurements (default load sizes, circular-reference result), and validation
  results. Do not reproduce full file contents or full diffs.

### Repository Tool Usage

Apply `rules/ai-execution.md`, section "Repository Tool Usage". For this workflow,
inspect repository tools relevant to: normative-rule inventory; duplicate detection;
canonical-reference validation; reference-graph and cycle detection; default
context-load measurement.

### Tasks

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `skills/DESIGN.md`
- `rules/ai-execution.md`

Do not load every skill file in full at the same time. List all files in Scope above
(`skills/*/SKILL.md`, `skills/*/workflow.md` and any split files, `rules/*.md`,
`prompts/*.md`) before starting Step 1.

#### Step 1: Inventory

Apply Step Responsibilities' Step 1 definition above. For each file in Scope:
1. Extract headings and a compact rule inventory: scope, type (normative/descriptive,
   per the Normative vs. Descriptive test), current owner, evidence location.
2. Read a full section only when needed to confirm whether a candidate is truly
   normative and truly equivalent in scope to another candidate.
3. Keep only the inventory in the main context (see Context Efficiency).

Report the Step 1 inventory as a compact table (content summary, locations found,
normative Y/N) before proceeding to Step 2.

#### Step 2: Relocation Plan

Apply Step Responsibilities' Step 2 definition above and the Relocation Plan format.
For every inventory candidate marked normative in Step 1, decide its canonical
destination using the Canonical Ownership Model and the `AGENTS.md`/`rules/*.md`
boundary test; apply the New File Creation Policy when no existing file fits.

**Report the Relocation Plan and stop. Do not proceed to Step 3 in the same
response.** Wait for explicit user approval of the plan before continuing.

#### Step 3: Edit

**Execute only the rows of the Relocation Plan the user approved.** Apply Editing
Constraints above. Report each row's outcome (`Applied` / `Blocked: plan mismatch`) as
it completes.

#### Step 4: Validate the reorganization

Apply Validation and Context Loader Pattern Validation above. Additionally confirm the
Context Loader Pattern still holds:

- `AGENTS.md` instructs the AI to consult `routing.md`, and defines no task-to-skill
  mapping entries and no rule that only some workflows need.
- `routing.md` is the only canonical source for task-to-skill mappings.
- `skills/DESIGN.md` and `rules/*.md` contain only shared rules, no task-specific
  procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific
  skill files or any `rules/*.md` file.

Per Step Responsibilities: validate only here — do not redo Step 1's inventory or
Step 2's planning or Step 3's edits.

#### Step 5: Report results

Apply Context Efficiency above for the report format. Report:
- which files were modified and what changed,
- which content was moved and where it now lives (canonical destination, in the
  Canonical References format),
- any items marked `Deferred` and the reason,
- any new file created, per the New File Creation Policy,
- the two Context Loader Pattern Validation measurements (per-skill default load size
  before/after, and the circular-reference check result),
- the Step 4 validation result.
