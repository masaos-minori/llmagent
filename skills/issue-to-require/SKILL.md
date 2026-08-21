---
name: issue-to-require
description: |
  Use this skill PROACTIVELY when converting a raw, unformatted issue
  (`issues/*.md`) into a formal requirement document (`requires/*.md`).
  Covers: verifying the issue's claims against current source, deciding
  whether the issue is already resolved or too vague to act on, and writing
  the requirement document in the project's standard section structure.
  Use when the task is document-only — no source code, tests, or docs/*.md
  are changed by this skill.
---

# Issue To Require Skill

## Purpose

Turn a raw issue into a formal, evidence-checked requirement document that `require-to-plan` can consume; verify the issue still applies before writing anything.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Identify the target issue file(s) | Confirm every specified `issues/{filename}.md` path exists before starting any processing. |
| 2 | Assess the issue | Read the issue in full and verify its factual claims against current source. If already resolved or no longer applicable, stop and move it to `issues/done/` without writing a requirement document. If too vague to act on, stop and ask the user. |
| 3 | Write the requirement document | Produce `requires/{timestamp}_require.md` using the fixed section structure below. |
| 4 | Move the completed issue file | Move the source issue to `issues/done/` and verify the move succeeded. Mandatory — do not skip. |

See `workflow.md` for the detailed per-step procedure, review-mode gating, and
multi-file processing rules.

---

## Core Execution Rules (Strictly Enforced)

- **Document-only phase**: this skill creates the requirement document in `requires/` and moves the processed issue file to `issues/done/`. It must not modify source code files or `docs/*.md`.
- **One file at a time**: see `workflow.md` Multi-file processing.
- **No Guesswork**: verify factual claims (affected files, whether the described problem still reproduces) against current source before writing the requirement document.
- **Mandatory move**: see `workflow.md` Step 4.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.
- Exception to `skills/DESIGN.md` Output language: write the requirement document in clear and concise English (it feeds directly into `require-to-plan` for AI consumption).

---

## Output format

Generate `requires/{timestamp}_require.md` using this exact Markdown structure. Do not omit any sections.

```markdown
# <Title>

## Priority
High / Medium / Low

## Target files
[Files or areas the requirement is expected to touch]

## Background
[Why this requirement exists]

## Problem
[The concrete problem being solved]

## Reason for change
[Why this change is needed now]

## Implementation intent
[High-level approach, without prescribing exact code]

## Implementation instructions
[Concrete, actionable instructions for the next phase]

## Acceptance criteria
[Verifiable completion criteria]

## Tests
[Testing expectations]

## Traceability
- Workflow phase: issue-to-requirement
- Source issue: {path to the source issue file}
- Source requirement: N/A
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: {timestamp from Step 3}
- Related target files: {target files from the issue}
```

## See Also
See `workflow.md` for detailed phase content, review-mode gating, and the multi-file processing procedure.
See `prompts/00_issue-to-require.md` for how this skill is invoked as part of the document-workflow pipeline.

## Composes with
- `require-to-plan` — consumes the requirement document this skill produces

## Improvement feedback

After running this skill, if the requirement section structure was missing a field the
user consistently requested, or a Step needed clarification, update `workflow.md`
accordingly.
