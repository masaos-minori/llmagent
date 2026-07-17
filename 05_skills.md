You are a senior software architect and skills organizer.

Read the existing skill files and routing configuration, then restructure them based on the Context Loader Pattern below.

- Do not rewrite files from scratch without reading them first.
- Do not modify source code files (scripts/, tests/) — this workflow targets skill and config files only.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Architectural Principles

Strictly follow these throughout all steps:

- **routing**: All task-to-skill mappings must go through `routing.md`; never bypass it by loading skills or docs directly.
- **dependency direction**: Files may only reference layers below them (`shared` → `db` → `rag`/`mcp` → `agent`); no upward references allowed.
- **minimal loading**: Load only the files required for the current task; never load all docs or all skills by default.
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

### Token efficiency

- Before reading full file contents, build a compact rule inventory in two stages:
  delegate to sub-agent(s) to extract, per file (or per batch of files), a list of
  rules/procedures as topic + one-line summary + file:line reference. Keep only this
  inventory in the main context, not the raw text of every skill file.
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

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `skills/DESIGN.md`
- All files matching `skills/*/SKILL.md`

#### Step 1: Remove duplicated content

Remove duplicated content across `AGENTS.md`, `skills/DESIGN.md`, and `skills/**/*.md`.

Acceptance criteria:
- No rule, guideline, or procedure appears in more than one file.
- Each piece of content has exactly one canonical location.
- All references to moved content point to the correct canonical location.

#### Step 2: Reorganize files based on the Context Loader Pattern

Perform after Step 1 is complete.

Apply the following structure:
- Put task routing rules in `AGENTS.md`.
- Put shared design and architectural rules in `skills/DESIGN.md`.
- Put only task-specific procedures and checklists in `skills/**/*.md`.
- Ensure that shared rules are defined only once and referenced from the appropriate files.
- Minimize default loading cost.
- Preserve clear dependency direction between files and rules.

Acceptance criteria:
- `AGENTS.md` contains routing rules only; no task-specific procedures.
- `skills/DESIGN.md` contains shared design/architectural rules only; no task-specific procedures.
- Each `skills/<task>/SKILL.md` contains only procedures specific to that task.
- Default context load (`AGENTS.md` + `routing.md`) does not pull in task-specific skill files.

#### Step 3: Report results

After completing Step 1 and Step 2, report:
- which files were modified and what changed,
- which content was moved and where it now lives,
- any proposals deferred because the change was ambiguous or risky.
