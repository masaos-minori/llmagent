# Skill Runtime Rules

Runtime sections that the pipeline skills load at Step 0 (`issue-to-plan`,
`plan-to-implementation-procedure`). They are moved verbatim from `skills/DESIGN.md`, which
keeps each heading as a pointer and holds the rest of the design rationale. The
text of each section is unchanged.

### Output language

Write generated documents (review reports, design docs, documentation) in English. This is
independent of the chat response language (see `AGENTS.md` Role) — a Japanese-language
conversation does not make this "the user requiring Japanese documents." All files under `docs/`
are English, with no exception, regardless of chat language. Always preserve file names,
module/symbol names, commands, configuration keys, type names, and evidence labels in their
original form — MUST NOT translate identifiers.

Write design-document prose so it is easy for an AI coding agent to parse and act on: short,
explicit sentences; one claim per sentence; explicit subjects (avoid implicit pronouns spanning
paragraphs); consistent terminology for the same concept throughout a document; no rhetorical
or figurative language that requires inference. Prefer normative terms (MUST / MUST NOT /
SHOULD / MAY) for required, prohibited, recommended, and optional behavior over descriptive
prose.

Only write a document in another language when the user explicitly asks for that specific
document (not the conversation) to be written in another language.

### Analysis-only phase constraint

Applies to any skill whose core procedure is read-only by design (currently `python-design`,
`python-code-review`, `python-debug-root-cause`, `issue-to-plan`,
`plan-to-implementation-procedure`, `issue-creator`) — i.e. skills whose purpose is to
produce an analysis, review, design, plan, or issue artifact rather than change code.

- MUST NOT modify source code, tests, or other production files while executing the skill's
  analysis/review/design phases.
- State this constraint once, in the skill's Purpose/description section. MUST NOT repeat it in
  every phase, rule list, or workflow step within the same skill.
- Proceed to writing/editing only when the user explicitly requests implementation, or the
  skill's own procedure reaches a phase specifically designated for writing output (e.g. writing
  a design doc or review report, which is the skill's actual deliverable — not source code).

### Change-impact table

Use this common schema whenever a skill needs to document per-file blast radius before making
or planning a change (currently used by `python-refactoring` Step 3 (Preparation) and
`issue-to-plan` Output format "Affected areas" section):

| File | Change | Blast Radius | deploy.sh Impact |
|---|---|---|---|
| `<path>` | create / rename / delete | modules/callers affected | see below |

`deploy.sh Impact` follows `rules/env.md`, section "Architecture". Valid values:
`not applicable (rsynced)`, `add cp line`, `remove cp line`.

A skill MAY append columns to this schema (e.g. `issue-to-plan` adds `Churn (30d)` and `Bus
Factor`) but MUST NOT redefine the meaning of the four base columns above, and MUST NOT
restate this schema inline — reference this section instead.

### Tool availability guard

Applies whenever a phase calls for an optional/advanced tool (e.g. `ast-grep`, `LibCST`,
`mutmut`, `viztracer`, `pydeps`, `semgrep`) that may not be installed in the current environment.

- MUST NOT invent or assume the tool's output or success message.
- Document `Tool [name] not available` in the findings.
- Fall back to the nearest standard equivalent (e.g. `ruff`/`mypy` for static checks, `pdb`/
  `traceback`/manual `rg` search for advanced tracing) and note that the fallback was used.
- Check a Python-package tool with `uv run <tool> --version`. A `command -v` miss does NOT mean
  the tool is missing, because project-environment tools are not on PATH.

### Out-of-scope paths

`__pycache__/`, `.venv/`, vendored/generated code, and build outputs are always out of scope for
reading, editing, or analysis — MUST NOT touch or count them toward any task unless the task
explicitly targets them.
