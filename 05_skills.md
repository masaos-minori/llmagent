[prerequisites]

Strictly follow the principles below.
- routing
- dependency direction
- minimal loading
- shared normalization

[tasks]
Show progress as you work.

1. Remove duplicated content across `~/llmagent/AGENTS.md`, `~/llmagent/skills/DESIGN.md`, and `~/llmagent/skills/**/*.md`.

2. Reorganize `~/llmagent/AGENTS.md`, `~/llmagent/skills/DESIGN.md`, and `~/llmagent/skills/**/*.md` based on the Context Loader Pattern.
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
  - Put task routing rules in `~/llmagent/AGENTS.md`.
  - Put shared design and architectural rules in `~/llmagent/skills/DESIGN.md`.
  - Put only task-specific procedures and checklists in `~/llmagent/skills/**/*.md`.
  - Ensure that shared rules are defined only once and referenced from the appropriate files.
  - Minimize default loading cost.
  - Preserve clear dependency direction between files and rules.

3. End the task.
