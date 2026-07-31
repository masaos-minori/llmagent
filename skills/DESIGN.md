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

## Shared Vocabulary

Canonical definitions referenced by multiple skills. Do not redefine these inline in a
`SKILL.md`/`workflow.md` — reference this section instead.

### Evidence labels

Use when describing current (not proposed) behavior in a review, design doc, or documentation
update. Do not introduce a parallel label system (e.g. `Confirmed`, `Inferred`, `Unknown`).

| Label | Meaning |
|---|---|
| `Explicit in code` | Directly visible in the current source |
| `Strongly implied by code` | Not explicit, but strongly suggested by surrounding code/structure |
| `Documentation only` | Backed only by docs, not verified against code |
| `Needs confirmation` | Unclear; state what must be checked |
| `Deprecated` | Exists but marked/intended for removal |
| `Verified by test` | Confirmed by an existing or newly written test |
| `Operationally observed` | Confirmed by runtime/log/production observation, not by reading source |

If behavior is unclear, mark it `Needs confirmation` and state what must be checked instead of
guessing. Do not treat dead code, unused code, stale migrations, or obsolete documentation as
active behavior.

### Confidence levels

- **High** — directly verified
- **Medium** — strongly implied
- **Low** — plausible but requires confirmation

### Tool availability guard

Applies whenever a phase calls for an optional/advanced tool (e.g. `ast-grep`, `LibCST`,
`mutmut`, `viztracer`, `pydeps`, `semgrep`) that may not be installed in the current environment.

- Do not invent or assume the tool's output or success message.
- Document `Tool [name] not available` in the findings.
- Fall back to the nearest standard equivalent (e.g. `ruff`/`mypy` for static checks, `pdb`/
  `traceback`/manual `rg` search for advanced tracing) and note that the fallback was used.

### Import layer contract (enforced by `.importlinter`)

Layers may only import from themselves and layers below:

```
shared → external only
db     → shared
rag    → db, shared
mcp_servers → db, shared
agent  → all layers
```

Violations fail `lint-imports`. Never import a lower layer from a higher one (e.g. `shared`
must not import from `agent`, `rag`, `db`, or `mcp_servers`).

### Pythonic safety constraints

Applies to any skill that writes or transforms production Python code
(`python-implementation`, `python-refactoring`, and any other skill producing code changes).

- Never use mutable objects (`list`, `dict`, etc.) as default arguments — use `None` and
  initialize inside the function.
- Never use `except Exception` (or bare `except:`) without re-raising, unless logging and
  safely terminating the process. Catch specific exception types. Use explicit exceptions
  instead of `assert` in business logic.
- Avoid raw `dict[str, Any]` for core domain data — use `dataclasses`, `Pydantic` models, or
  `TypedDict`. Do not perform unconditional `str()` conversion; validate types first. Treat
  `None`, empty string, and unset as distinct — do not collapse them.
- Always use context managers (`with`/`async with`) for resource management (files, network
  connections, locks).
- Forbid unsafe dynamic execution: no `eval()`, `exec()`, or `pickle` on untrusted input; when
  using `subprocess`, always set `shell=False` and pass arguments as a list.
- In `async def` functions, never introduce blocking I/O (`time.sleep()`, sync file/network
  calls) — use `await asyncio.sleep()` or run blocking paths in executors.
- Use fail-fast for unknown tool names, tiers, or metadata — never fail-open.
- No placeholders (`pass`, `...`, `# TODO`) in the final implementation — every logical path
  must be fully implemented.
- No debug artifacts before closing the task: remove `print()` statements, commented-out code,
  and temporary debug variables — use the `logging` framework instead.

## Skill catalog

| Skill | Directory | Purpose |
|---|---|---|
| `python-implementation` | `skills/python-implementation/` | Feature development, bug fixes, new Python modules |
| `python-debug-root-cause` | `skills/python-debug-root-cause/` | Systematic root cause analysis for Python failures |
| `python-lint-typecheck` | `skills/python-lint-typecheck/` | Ruff / mypy / pyright lint and type error resolution |
| `python-test-and-fix` | `skills/python-test-and-fix/` | pytest test writing, flaky test detection, fix validation |
| `python-refactoring` | `skills/python-refactoring/` | Structural refactoring without behavior change |
| `python-code-review` | `skills/python-code-review/` | Evidence-based review of existing Python code, PRs, and diffs |
| `issue-to-require` | `skills/issue-to-require/` | Convert raw issues into formal requirement documents |
| `require-to-plan` | `skills/require-to-plan/` | Convert requirement documents into implementation plans |
| `python-design` | `skills/python-design/` | Architecture and module interface design |
| `python-documentation` | `skills/python-documentation/` | Writing and updating Python documentation |
| `issue-creator` | `skills/issue-creator/` | Convert requests, findings, or plans into actionable GitHub Issues |
| `mcp-server-add` | `skills/mcp-server-add/` | Add a new MCP server to the project |
| `deploy` | `skills/deploy/` | Deploy changes to the production environment |
| `git-commit-and-sync` | `skills/git-commit-and-sync/` | Safe Git commit, pull, conflict resolution, and push |
