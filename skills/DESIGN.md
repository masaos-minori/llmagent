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

### Analysis-only phase constraint

Applies to any skill whose core procedure is read-only by design (currently `python-design`,
`python-code-review`, `python-debug-root-cause`, `issue-to-plan`, `issue-creator`) — i.e.
skills whose purpose is to produce an analysis, review, design, plan, or issue artifact
rather than change code.

- Do not modify source code, tests, or other production files while executing the skill's
  analysis/review/design phases.
- State this constraint once, in the skill's Purpose/description section. Do not repeat it in
  every phase, rule list, or workflow step within the same skill.
- Proceed to writing/editing only when the user explicitly requests implementation, or the
  skill's own procedure reaches a phase specifically designated for writing output (e.g. writing
  a design doc or review report, which is the skill's actual deliverable — not source code).

### Import layer contract (enforced by `.importlinter`)

Layers may only import from themselves and layers below. The canonical layer diagram lives in
`rules/env.md` Architecture (includes the current `eventbus` isolation rule and `agent`'s actual
scope) — do not restate or re-derive the diagram here. Violations fail `lint-imports`. Never
import a lower layer from a higher one.

### Output language

Write generated documents (review reports, design docs, documentation) in English. This is
independent of the chat response language (see `AGENTS.md` Role) — a Japanese-language
conversation does not make this "the user requiring Japanese documents." All files under `docs/`
are English, with no exception, regardless of chat language. Always preserve file names,
module/symbol names, commands, configuration keys, type names, and evidence labels in their
original form — do not translate identifiers.

Write design-document prose so it is easy for an AI coding agent to parse and act on: short,
explicit sentences; one claim per sentence; explicit subjects (avoid implicit pronouns spanning
paragraphs); consistent terminology for the same concept throughout a document (do not vary
wording for the same thing across sections); no rhetorical or figurative language that requires
inference. Prefer normative terms (MUST / MUST NOT / SHOULD / MAY) for required, prohibited,
recommended, and optional behavior over descriptive prose.

Only write a document in another language when the user explicitly asks for that specific
document (not the conversation) to be written in another language.

### Change-impact table

Use this common schema whenever a skill needs to document per-file blast radius before making
or planning a change (currently used by `python-refactoring` Phase 1 and `issue-to-plan`
Output format "Affected areas" section):

| File | Change | Blast Radius | deploy.sh Impact |
|---|---|---|---|
| `<path>` | create / rename / delete | modules/callers affected | see below |

`deploy.sh Impact` follows `rules/env.md` Architecture: `scripts/` is rsynced wholesale, so a
module create/rename/delete needs no `deploy.sh` change; only a `config/*.toml` add/remove
needs a `cp` line added or removed there. Valid values: `not applicable (rsynced)`, `add cp
line`, `remove cp line`.

A skill MAY append columns to this schema (e.g. `issue-to-plan` adds `Churn (30d)` and `Bus
Factor`) but MUST NOT redefine the meaning of the four base columns above, and MUST NOT
restate this schema inline — reference this section instead.

### Avoid implementation-reference duplication

When writing a design document, review report, or documentation update, do not copy exhaustive
file lists, method catalogs, DTO/config-key field tables, or long command/JSON examples into the
document — recommend or write a concise, evidence-grounded summary instead, and point to the
source for exhaustive detail.

### No source-code line numbers

Do not cite source-code line numbers in design documents (e.g. `recovery.py:120-150`) — they go
stale on the next edit and carry no meaning outside the current diff. Reference implementation by
class name, function name, method name, or protocol name instead (e.g. `recover_corruption()`,
`RuntimeToolRegistry.resolve()`). A file path may be included only when needed to disambiguate a
symbol name that exists in more than one place.

### No concrete configuration values

Do not copy concrete values from `config/*.toml` (or other configuration files) into design
documents — paths, hosts, ports, timeouts, retry limits, thresholds, allowlist entries, branch
names, remote names, cache sizes, or any other current deployed/default value. Describe the
policy and its consequences instead (what the setting controls, what happens when it is
empty/unset, what depends on it), and point to the owning configuration file for the current
operational value. A concrete value is acceptable only inside a worked example that is explicitly
labeled as illustrative, never as a claim about the current deployed configuration.

### No implementation counts

Do not state how many modules, tools, servers, states, fields, tests, or documents something
comprises (e.g. "all three production DBs", "6 of 10 servers", "the following 17 fields"). Counts
drift the moment an item is added or removed, and the design intent rarely depends on the exact
number. Name the items instead (list them, or reference the enum/collection that defines them) so
the statement stays correct regardless of how many there are. This does not apply to counts that
are themselves part of the technical contract (e.g. a retry limit, a schema version number) — those
are configuration values, not commentary, and are governed by the "No concrete configuration
values" rule above.

### Out-of-scope paths

`__pycache__/`, `.venv/`, vendored/generated code, and build outputs are always out of scope for
reading, editing, or analysis — do not touch or count them toward any task unless the task
explicitly targets them.

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
| `issue-to-plan` | `skills/issue-to-plan/` | Convert raw issues directly into implementation plans |
| `plan-to-implementation-procedure` | `skills/plan-to-implementation-procedure/` | Convert an approved plan into file-level implementation procedure documents |
| `code-implementation` | `skills/code-implementation/` | Execute an approved implementation procedure into code, tests, and documentation |
| `python-design` | `skills/python-design/` | Architecture and module interface design |
| `python-documentation` | `skills/python-documentation/` | Writing and updating Python documentation |
| `issue-creator` | `skills/issue-creator/` | Convert requests, findings, or plans into actionable GitHub Issues |
| `mcp-server-add` | `skills/mcp-server-add/` | Add a new MCP server to the project |
| `deploy` | `skills/deploy/` | Deploy changes to the production environment |
| `git-commit-and-sync` | `skills/git-commit-and-sync/` | Safe Git commit, pull, conflict resolution, and push |
