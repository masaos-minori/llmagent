You are a senior software architect and skills organizer.

Read the existing skill files and routing configuration, then restructure them based on the Context Loader Pattern below.

- Do not rewrite files from scratch without reading them first.
- Do not modify source code files (scripts/, tests/) — this workflow targets skill and config files only.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Architectural Principles

Strictly follow these throughout all steps:

- **routing**: All task-to-skill mappings must go through `routing.md`; never bypass it by loading skills or docs directly.
- **dependency direction**: Apply this direction: `agent -> rag/mcp -> db -> shared`. The arrow means "may depend on or reference".
  - `agent` may reference `rag`, `mcp`, `db`, and `shared`.
  - `rag` and `mcp` may reference `db` and `shared`.
  - `db` may reference `shared`.
  - `shared` must not reference higher layers.
  - A lower layer must not reference a higher layer.
  - `rag` and `mcp` are sibling layers.
  - `rag` and `mcp` must not reference each other unless an approved rule explicitly allows it.
  - Do not confuse layer display order with dependency direction.
- **minimal loading**: Load only the minimum skill files required for the current task. Do not load entire skill directories unless specifically needed. Prefer loading individual rule files over entire skill workflows.
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

### Deduplication Rules

- Treat content as duplicated only when its scope, requirements, conditions,
  exceptions, and effects are equivalent.
- Deduplicate normative rule text only.
- Allow short cross-references and non-normative summaries that do not introduce new
  requirements, prohibitions, conditions, or exceptions.
- Do not move a rule when its canonical owner is unclear. Mark it as `Deferred` and
  report the reason.
- Preserve all requirements, prohibitions, conditions, exceptions, and acceptance
  criteria when relocating a rule.

Decide a duplicate's canonical destination by content type, then replace every other
occurrence with a short cross-reference to that destination (see Canonical
References) — never leave the rule's normative text repeated in more than one place:

| Content type | Canonical destination |
|---|---|
| Task-to-skill or source-to-document mapping | `routing.md` |
| Repository-wide AI-execution or lifecycle rule used by 2+ workflows, not universal, not skill-specific | `rules/*.md` (e.g. `rules/ai-execution.md`, `rules/workflow-lifecycle.md`) |
| Shared design/architecture rule used by 2+ skills | `skills/DESIGN.md` |
| Task-specific procedure or checklist | The owning `skills/<task>/SKILL.md` (or its `workflow.md`) |
| Repository-wide AI execution constraint that every task needs (not task-specific, not a mapping) | `AGENTS.md` |

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

### Canonical References

- Give canonical rules a stable heading or Rule ID.
- Reference canonical rules by file path and stable heading or Rule ID.
- Use line numbers only as supporting information because they may change after editing.
- Use this reference format:

  `See <file path>, section "<heading or Rule ID>".`

### Editing Workflow

- Build a compact rule inventory before editing.
- Record each rule's scope, type, current owner, canonical owner, and evidence
  location.
- Prepare a relocation plan before modifying files.
- Process one section at a time.
- Move only the duplicated section and replace the original text with a canonical
  reference.
- Do not rewrite an entire file when a section-level edit is sufficient.
- Do not overwrite pre-existing user changes.
- Do not modify source code or test files.

### Validation

- Verify that no normative meaning was lost during relocation.
- Verify all file paths, headings, Rule IDs, and Markdown references after editing.
- Verify that routing behavior still maps each task to the intended skill.
- Verify that `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, and
  task-specific skill files contain only content within their assigned
  responsibility.
- Report intentional routing changes separately with reasons.
- Report ambiguous or unsafe changes as `Deferred`.

### Step Responsibilities

- Step 1: Detect duplicates, determine canonical ownership, move normative content,
  and replace duplicates with references.
- Step 2: Validate file responsibilities, dependency direction, routing behavior,
  references, and semantic completeness.
- Do not repeat the same analysis or edit in both steps.

### Context Efficiency

**Accuracy, completeness, and validation always take priority over context reduction.**
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
  destinations, deferred items, and validation results. Do not reproduce full file
  contents or full diffs.

### Tasks

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `skills/DESIGN.md`
- `rules/ai-execution.md`

Do not load every skill file in full at the same time. Apply Editing Workflow above:
1. List all `skills/*/SKILL.md` files.
2. Extract headings and a compact rule inventory (scope, type, current owner,
   canonical owner, evidence location).
3. Keep only the inventory in the main context (see Context Efficiency).
4. Read a full section only when needed to confirm duplication or relocation.

#### Step 1: Remove duplicated content

Apply Deduplication Rules, Editing Workflow, and Canonical References above to
`AGENTS.md`, `skills/DESIGN.md`, `rules/*.md`, and `skills/**/*.md`.

Per Step Responsibilities: detect, relocate, and reference here — do not run
Validation in this step.

#### Step 2: Validate the reorganization

Apply Validation above. Additionally confirm the Context Loader Pattern still holds:

- `AGENTS.md` instructs the AI to consult `routing.md`, and defines no task-to-skill
  mapping entries and no rule that only some workflows need.
- `routing.md` is the only canonical source for task-to-skill mappings.
- `skills/DESIGN.md` and `rules/*.md` contain only shared rules, no task-specific
  procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific
  skill files or any `rules/*.md` file.

Per Step Responsibilities: validate only here — do not redo Step 1's detection or
relocation.

#### Step 3: Report results

Apply Context Efficiency above for the report format. Report:
- which files were modified and what changed,
- which content was moved and where it now lives (canonical destination, in the
  Canonical References format),
- any items marked `Deferred` and the reason,
- the Step 2 validation result.
