---
name: issue-creator
description: |
  Create clear, actionable GitHub Issues from requests, review findings, investigation notes,
  implementation plans, or documentation tasks. Use this skill when converting work into
  issue-ready Markdown. Do not implement changes unless explicitly requested.
---

# Issue Creator Skill

## Purpose

Create issues only — see `skills/DESIGN.md` Analysis-only phase constraint. Proceed to
implementation only when the user explicitly asks for it.

Exception to `skills/DESIGN.md` Output language: write issue bodies in English (GitHub issues are consumed by AI coding agents and international tooling), unless the user requests another language. If the target design or documentation must be Japanese, state that inside the issue.

Output: one Markdown file per issue under `issues/` (the pipeline entry point — see
`routing.md` Document workflow directories). This skill does not post to GitHub or run
`gh issue create`; filing on GitHub is a separate step the user must request.

See `workflow.md` Step 9b for markdown-safety rules.

## Required reading

`routing.md` loads only this file and `workflow.md` for issue creation. Also read before drafting:

- `templates/issue.md` — the canonical issue structure
- `skills/DESIGN.md` — Analysis-only phase constraint, Output language, Evidence labels,
  Confidence levels, No secrets in output, Avoid implementation-reference duplication,
  Docs content policy — remove
- `rules/ai-execution.md` — Sequential Target Processing (Base), Repository Tool Usage
- `rules/filename-collision.md` — Collision Retry Bound

## When to use

Use this skill for:

- converting a task list into GitHub Issues
- converting review findings into actionable issues
- converting implementation plans into issues
- converting documentation cleanup work into issues
- splitting large work into smaller tasks
- grouping tightly related tasks that should be done together
- writing acceptance criteria, out-of-scope notes, and testing expectations
- preparing AI implementation instructions for coding agents

## When not to use

MUST NOT use this skill for:

- direct code implementation — instead, route it through `python-implementation`
  directly, or through `issue-to-plan` → `plan-to-implementation-procedure` →
  `code-implementation` for larger scope.
- speculative issues without evidence or context — instead, gather at least one
  concrete piece of evidence (a repository file, log, or existing document) first, or
  record the gap as an assumption/open question per Phase 1.
- bulk issue generation that mixes unrelated concerns — instead, apply Phase 2's Task
  Grouping to split them into separate issues.
- writing long implementation manuals inside issues — instead, keep Implementation
  Intent high-level and let `plan-to-implementation-procedure` produce the file-level
  manual.

When requirements are unclear, use this skill, but follow `workflow.md` Phase 1: mark
assumptions and open questions instead of inventing missing requirements. Every such item is
also reported to the user as `不明` in the final report (`workflow.md` Phase 10), which is how
this skill meets `AGENTS.md` Policy's "state 不明 and ask" without blocking: an issue is itself
the vehicle for unresolved questions, and it is not implementation.

---

## Phase overview

1. Classify and Frame: identify the work's source, scope, and whether assumptions are needed
2. Task Grouping: split into multiple issues or group into one
3. Draft Reason and Intent: write Title, Summary, Background, Problem, Reason for Change, and Implementation Intent
4. Scope and Boundaries: define Target Files, Required Changes, Constraints, Out of Scope, and Dependencies
5. Acceptance Criteria and Testing: define verifiable criteria and testing expectations
6. Documentation Impact: assess doc impact and apply documentation cleanup rules
7. Priority Assignment: assign High / Medium / Low
8. AI Implementation Instruction: write concise constraints for an AI coding agent
9. Evidence, Markdown Safety, Final Checklist: verify evidence, copy-paste safety, and completeness of the draft
10. Write and Verify the File: scaffold the file, fill every placeholder (including Traceability),
    run the structure checker, and report to the user

See `workflow.md` for detailed phase content, task grouping rules, documentation cleanup
rules, markdown safety rules, and the final checklist.

---

## Core Principles

- One issue should represent one actionable task.
- Group tasks only when they must be completed together or are safer to review together.
- Prefer small, reviewable issues over broad, vague issues — use `workflow.md` Phase
  2's Task Grouping criteria (group vs. split) to decide the size, not a file count:
  an Issue naming several tightly coupled files can still be one small, reviewable issue.
- Each issue MUST explain both the reason for change and the implementation intent.
- Acceptance criteria MUST be concrete and verifiable.
- Out-of-scope items MUST be explicit.
- Testing expectations MUST be included when code behavior may change.
- An issue that asks implementers to change `docs/*.md` MUST NOT request content that
  `skills/DESIGN.md` "Avoid implementation-reference duplication" or "Docs content policy — remove" forbids.
- Follow `skills/DESIGN.md` No secrets in output.

## Issue Filename Generation

Every issue file MUST follow this naming convention (stable, sortable, human-readable names),
except the Unknown/Risk follow-up files that `skills/issue-to-plan` Step 6 generates, which
use `issues/{timestamp}[_{NN}]_unknowns.md` / `_risks.md` per `templates/unknowns-issue.md`
and `templates/risks-issue.md`.
Duplicate detection in `skills/issue-to-plan` Step 1b is content-based (it matches the Issue's
path in a Plan's Traceability), so it does not parse the filename.

### Naming convention

Format: `{timestamp}_{id}_{slug}.md`

- **`{timestamp}`** — `YYYYMMDD-HHmmss`, generated at issue creation time (e.g., `20260828-155804`).
- **`{id}`** — Short identifier derived from the issue's domain or component, matching
  `[a-z0-9]+` (no underscores or dashes, so the `_` separators stay unambiguous; e.g.,
  `nc019`, `mcp003`, `doc005`, `refactor001`). The full filename, not `{id}` alone, MUST be
  unique — checked in `issues/` and `issues/done/` (see `workflow.md` Phase 10).
- **`{slug}`** — Slug derived from the issue title, lowercase, matching `[a-z0-9_-]+`: at most
  4 words, articles and other filler words dropped, and no symbols other than `_` and `-`.
  If the title has no ASCII words (e.g. a non-English title), write an English slug of the
  same meaning.

Example: `20260828-155804_nc019_git-mcp-command-guards.md`

If no meaningful `{id}` exists, use a generic prefix such as `todo` or `misc` plus a short
sequence number (e.g., `todo001`). Never omit the `{id}` — `tools/generate_workitem.py`
requires it and readers expect the three-part format.

---

## Issue Structure

Use the exact Markdown structure defined in `templates/issue.md`. It is the shared
contract with `skills/issue-to-plan`'s Step 2 extraction — MUST NOT maintain a separate
copy of the field list here.

---

## Priority Guidance

See `workflow.md` Phase 7 for the High / Medium / Low criteria.

---

## Composes with

- `issue-to-plan` — issues produced here may seed a plan directly, or a plan's steps may be converted into issues
- `python-code-review` — review findings are converted into issues via this skill

## Called by

- `python-code-review` — GitHub Issue Conversion step
- `python-documentation` — when documentation cleanup work should be tracked as issues rather than performed immediately

---

## Improvement feedback

After running this skill:
- if a priority definition caused disagreement, refine it in `workflow.md` Phase 7
- if a grouping decision was wrong, refine the grouping rules in `workflow.md` Phase 2
- if the Issue Structure was missing a field the user consistently requested, add it to
  `templates/issue.md` (not here) so `skills/issue-to-plan` picks up the same change

---

## Final Rule

You are creating actionable, reviewable, implementation-ready GitHub Issues, not vague task notes.

When in doubt, prioritize: clarity, actionability, reviewability, minimal scope, testability,
documentation safety.
