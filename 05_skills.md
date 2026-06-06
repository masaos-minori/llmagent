[prerequisites]

Strictly follow the principles below.
- routing
- dependency direction
- minimal loading
- shared normalization

[tasks]

- Show progress as you work.
- Remove duplicated content across `AGENTS.md`, `skills/DESIGN.md`, and `skills/**/*.md`.
- Reorganize `AGENTS.md`, `skills/DESIGN.md`, and `skills/**/*.md` based on the Context Loader Pattern.
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
- Apply the following structure:
  - Put task routing rules in `AGENTS.md`.
  - Put shared design and architectural rules in `skills/DESIGN.md`.
  - Put only task-specific procedures and checklists in `skills/**/*.md`.
  - Ensure that shared rules are defined only once and referenced from the appropriate files.
  - Minimize default loading cost.
  - Preserve clear dependency direction between files and rules.
