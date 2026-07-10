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
