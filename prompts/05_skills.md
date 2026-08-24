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
- **minimal loading**: See the minimal skill loading process below.
- **shared normalization**: Rules and conventions shared across multiple skills must be defined once in `skills/DESIGN.md` and referenced, not duplicated.

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

- `AGENTS.md`: repository-wide AI execution constraints and an instruction to consult `routing.md`.
- `routing.md`: the only canonical source for task-to-skill mappings and source-to-document mappings.
- `skills/DESIGN.md`: shared design and architecture rules.
- `skills/<task>/SKILL.md`: task-specific procedures and checklists.

Do not place task-to-skill mappings in `AGENTS.md`. Do not duplicate routing definitions in other files.

### Context efficiency

**Accuracy, completeness, and validation always take priority over context reduction.**
Do not reduce context when doing so may cause missing evidence, incorrect conclusions,
incomplete plans, or insufficient validation.

#### Context reading

- Read the current target file in full when its complete meaning or structure is required.
- Read only relevant sections of related files by default.
- Read a related file in full when excerpts are not enough to understand: behavior,
  dependencies, lifecycle, ownership, side effects, error handling, configuration, tests,
  or document consistency.
- Do not omit necessary evidence only to save context.
- Reuse a verified fact only while its source file remains unchanged.
- Store the source path and evidence location with each cached fact.
- Recheck cached facts after the related source file changes.

#### Tool usage

- Before invoking a tool, check whether already-available information is sufficient to
  decide or answer.
- Batch independent tool calls into a single request instead of issuing them one at a
  time.
- Use verbose, debug, or trace output only when diagnosing a problem.
- Do not repeat the same command when neither its input nor the environment has changed.

#### Reasoning and planning

- For simple tasks, act directly instead of producing a long plan.
- Do not repeat interim summaries of investigation results.
- Do not over-explain intermediate results.
- Do not list alternatives the user did not ask for.
- Investigate further only when genuinely uncertain.
- Judge at the granularity needed to finish the task; avoid excessive optimization or
  verification.

#### Output

- State the conclusion first.
- Keep the answer scoped to what was requested.
- Explain only the changes made, not the surrounding unchanged code.
- Omit long background explanation unless the user asks for detail.
- Do not repeat the same content as a "summary", "detail", and "conclusion".
- Report only the necessary part of execution results; do not restate them verbatim.

#### Inventory-first approach

- Before reading full file contents, build a compact rule inventory in two stages:
  extract, per file (or per batch of files), a list of rules/procedures as topic + one-line
  summary + file:line reference. Keep only this inventory in the main context, not the
  raw text of every skill file.
- In Step 1, detect duplication by comparing inventory entries first; only read the full
  text of the specific matching sections (not entire files) to confirm a suspected
  duplicate.
- In Step 2, process one file at a time: read it, apply the move/edit, then move to the
  next file; do not keep the full content of already-processed files in context.
- Prefer surgical `Edit` moves (cut a section from the source file, paste it into the
  destination) over rewriting entire files.
- Read `routing.md`, `AGENTS.md`, and `skills/DESIGN.md` only once per session.
- In Step 3, report which files changed and where content moved to; do not restate full
  diffs or full before/after file content.

#### Progress reporting

- Keep start/end progress reports to one or two lines; do not restate full document
  content in progress reports.
- Include all failures, blocking issues, and important validation results even in concise reports.

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `skills/DESIGN.md`

Do not load every skill file in full at the same time. Use this process:
1. List all `skills/*/SKILL.md` files.
2. Extract headings and a compact rule inventory.
3. Keep only the topic, summary, file path, and line reference in the main context.
4. Read a full section only when needed to confirm duplication or relocation.
5. Do not keep all skill file contents in the main context.

#### Step 1: Remove duplicated content

Remove duplicated content across `AGENTS.md`, `skills/DESIGN.md`, and `skills/**/*.md`.

When a duplicate is found, decide its destination by content type using the table
below, then replace every other occurrence with a short cross-reference to that
destination — never leave the rule's text repeated in more than one place:

| Content type | Canonical destination | Reference form left behind elsewhere |
|---|---|---|
| Task-to-skill or source-to-document mapping | `routing.md` | An instruction to consult `routing.md`; no mapping entries anywhere else |
| Shared design/architecture rule used by 2+ skills | `skills/DESIGN.md` | `see skills/DESIGN.md {section name}` |
| Task-specific procedure or checklist | The owning `skills/<task>/SKILL.md` (or its `workflow.md`) | `see skills/<task>/SKILL.md {section name}` |
| Repository-wide AI execution constraint (not task-specific, not a mapping) | `AGENTS.md` | Referenced by name from skills that need it |

Acceptance criteria:
- No rule, guideline, or procedure appears in more than one file.
- Each piece of content has exactly one canonical location.
- All references to moved content point to the correct canonical location, using the
  reference form in the table above.
- `AGENTS.md` contains repository-wide execution constraints and the instruction to
  consult `routing.md` only — no task-specific procedures and no task-to-skill mapping
  entries.
- `skills/DESIGN.md` contains shared design/architectural rules only; no task-specific procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific skill files.

#### Step 2: Reorganize files based on the Context Loader Pattern

Perform after Step 1 is complete.

Define the roles of each file type:

##### AGENTS.md

- Contains repository-wide AI execution constraints.
- Instructs the AI to consult `routing.md`.
- Does not contain task-to-skill mapping entries.

##### routing.md

- Is the only canonical source for task-to-skill mappings.
- Contains required source-to-document mappings.
- Does not duplicate routing definitions in other files.

##### skills/DESIGN.md

- Contains architectural rules shared by multiple skills.
- Does not contain task-specific procedures.

##### skills/<task>/SKILL.md

- Contains only task-specific procedures, decisions, and checklists.
- Does not define task-to-skill mappings.

A normative rule must have one canonical definition. A short link or non-normative summary is allowed if it does not redefine the rule.

Apply the following structure:
- Put only an instruction to consult `routing.md` in `AGENTS.md` — the task-to-skill
  mapping table itself lives only in `routing.md` (per Canonical Ownership Model
  above). Do not add mapping entries, or a second copy of the mapping table, to
  `AGENTS.md`.
- Put shared design and architectural rules in `skills/DESIGN.md`.
- Put only task-specific procedures and checklists in `skills/**/*.md`.
- Ensure that shared rules are defined only once and referenced from the appropriate files.
- Minimize default loading cost.
- Preserve clear dependency direction between files and rules.

Acceptance criteria:
- `AGENTS.md` contains repository-wide execution constraints and the instruction to
  consult `routing.md` only — no task-specific procedures and no task-to-skill mapping
  entries.
- `skills/DESIGN.md` contains shared design/architectural rules only; no task-specific procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific skill files.

#### Step 3: Report results

After completing Step 1 and Step 2, report:
- which files were modified and what changed,
- which content was moved and where it now lives,
- any proposals deferred because the change was ambiguous or risky.
