# Skill Design Principles

**Essential definition:** A SKILL is a formalized, re-executable encoding of a work procedure.

**Design principles** — every SKILL must satisfy all of these:

| Principle | What it means |
|---|---|
| Write the minimum necessary | Include only what cannot be inferred from the code or context; omit obvious steps |
| Spell out the procedure | List concrete, ordered steps — no ambiguous verbs like "handle" or "deal with" |
| Reduce judgment | Pre-decide branching logic so the executor never has to improvise |
| Define the deliverable | State exactly what artifact or state change marks the SKILL complete |
| Include verification | Provide a concrete check command or assertion that confirms success |
| Compose with other SKILLs | Design so the SKILL can be chained; avoid re-encoding what another SKILL already covers |
| Optimize for token efficiency | Front-load critical rules; cut prose that does not constrain behavior |
| Design to prevent failure | Anticipate common error modes and encode the guard or recovery inline |

**Execution model** — universal rules for running any skill:
- Execute phases in order; do not skip mandatory phases
- Skip optional phases only when the defined skip condition applies
- If a phase reveals missing information or blocking issues, stop, resolve, then continue

**File organization** — when splitting a skill file or creating a new one, apply the File Split Rule below.

**Evaluation criteria** — a SKILL is good when it:

- Runs autonomously end-to-end without human intervention
- Produces the same result on every execution (idempotent)
- Requires no judgment calls from the executor beyond reading the input
- Can be improved incrementally without breaking existing callers
- Contains an `## Improvement feedback` section — after running, update that section when a phase gate was wrong or a recovery path was missing

## File Split Rule

When a document or skill file grows too large, split it according to these rules.

**Trigger:** a single file exceeds 400 lines AND contains multiple independent responsibilities.

**Four principles:**

| Principle | Rule |
|---|---|
| **routing** | After splitting, add task-type → file entries to the "Docs → task mapping" table in `routing.md` |
| **dependency direction** | Keep dependencies between new files strictly one-directional; no circular imports or references |
| **minimal loading** | Draw responsibility boundaries so that any single task requires reading as few files as possible |
| **shared normalization** | Consolidate shared specs or protocol definitions into one file; all others reference it, never duplicate |

**Procedure:**

1. Group sections/functions by responsibility and write the split proposal in a temporary plan file (e.g. `04_split_plan.md`); review the plan before touching any file
2. After splitting, convert the original file to an index (link list) or remove its content
3. Apply ripple-effect changes in the same pass: `routing.md`, `rules/env.md`, skill references, `docs/00_llm-implementation-guide.md`, `docs/06_common.md`
4. For code files, confirm `ruff` / `mypy` / `pytest` pass before closing the task

## Skill catalog

| Skill | Directory | Purpose |
|---|---|---|
| `python-implementation` | `skills/python-implementation/` | Feature development, bug fixes, new Python modules |
| `python-debug-root-cause` | `skills/python-debug-root-cause/` | Systematic root cause analysis for Python failures |
| `python-lint-typecheck` | `skills/python-lint-typecheck/` | Ruff / mypy / pyright lint and type error resolution |
| `python-test-and-fix` | `skills/python-test-and-fix/` | pytest test writing, flaky test detection, fix validation |
| `python-refactoring` | `skills/python-refactoring/` | Structural refactoring without behavior change |
| `python-issue-to-plan` | `skills/python-issue-to-plan/` | Convert tickets or requests into implementation plans |
| `python-design` | `skills/python-design/` | Architecture and module interface design |
| `python-documentation` | `skills/python-documentation/` | Writing and updating Python documentation |
| `mcp-server-add` | `skills/mcp-server-add/` | Add a new MCP server to the project |
| `deploy` | `skills/deploy/` | Deploy changes to the production environment |
| `git-commit-and-sync` | `skills/git-commit-and-sync/` | Safe Git commit, pull, conflict resolution, and push |
