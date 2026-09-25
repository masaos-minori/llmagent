# Update CI docs path filters for folder reorganization

## Priority
High

## Summary
Update the `paths:` filters in 5 GitHub Actions workflows that use a prefix-based glob
scoped to today's flat `docs/` layout, so each workflow keeps triggering correctly once
the corresponding files move into their planned area subfolder. No filename changes.

## Background
A separate investigation (2026-09-23) evaluated reorganizing `docs/` into area-based
subfolders while keeping every existing filename unchanged.

## Problem
5 of the 8 `docs/`-related workflows under `.github/workflows/` use a `paths:` filter
that only matches files directly under `docs/` (not a recursive `docs/**/*.md`
pattern), scoped by filename prefix:

- `agent-docs-consistency.yml`: `"docs/05_agent_*.md"`, `"docs/90_shared_04_*.md"`
- `overview-docs-consistency.yml`: `"docs/01_overview*.md"`
- `deployment-docs-consistency.yml`: `"docs/02_deployment*.md"`
- `rag-docs-consistency.yml`: `"docs/03_rag_*.md"`
- `rag-docs-quality.yml`: `"docs/03_rag_*.md"`

Once the corresponding files move into `docs/23_agent/`, `docs/41_db/` (for the
`shared_04_*` DB-architecture files), `docs/01_overview/`, `docs/90_deployment/`,
and `docs/21_rag/` respectively, none of these path patterns match anymore, and GitHub
Actions will not raise an error — the workflow will simply stop triggering on future
edits to those files. This is a silent-failure mode: no error, just a check that quietly
stops running.

The other 3 docs-related workflows (`governance-docs-consistency.yml`,
`mcp-docs-consistency.yml`, `backward-compat-check.yml`) already use `"docs/**/*.md"`
and are unaffected by the move — confirmed via direct inspection, no change needed for
these three.

## Reason for Change
These 5 workflows are the CI enforcement for docs-consistency checks in their
respective domains. A workflow that silently stops triggering removes a safety net
without any visible signal, which is worse than an outright failure.

## Implementation Intent
For each of the 5 workflows, change the `paths:` filter to match the new subfolder
location while keeping the same prefix specificity where it still makes sense (or
relaxing to a recursive-within-subfolder pattern, since the subfolder itself now scopes
the domain). Apply the same change to both the `push` and `pull_request` trigger
sections in each file (both currently duplicate the same `paths:` list).

## Target Files or Areas
- `.github/workflows/agent-docs-consistency.yml`
- `.github/workflows/overview-docs-consistency.yml`
- `.github/workflows/deployment-docs-consistency.yml`
- `.github/workflows/rag-docs-consistency.yml`
- `.github/workflows/rag-docs-quality.yml`

## Required Changes
- `agent-docs-consistency.yml`: change `"docs/05_agent_*.md"` →
  `"docs/23_agent/05_agent_*.md"` and `"docs/90_shared_04_*.md"` →
  `"docs/41_db/90_shared_04_*.md"`, in both the `push` and `pull_request` sections.
- `overview-docs-consistency.yml`: change `"docs/01_overview*.md"` →
  `"docs/01_overview/01_overview*.md"`, in both sections.
- `deployment-docs-consistency.yml`: change `"docs/02_deployment*.md"` →
  `"docs/90_deployment/02_deployment*.md"`, in both sections.
- `rag-docs-consistency.yml`: change `"docs/03_rag_*.md"` →
  `"docs/21_rag/03_rag_*.md"`, in both sections.
- `rag-docs-quality.yml`: change `"docs/03_rag_*.md"` →
  `"docs/21_rag/03_rag_*.md"`, in both sections.

## Constraints
- Do not change any other `paths:` entry in these workflows (e.g. `tools/check_*.py`,
  `config/*.toml`, `deploy/*.sh` entries stay as-is).
- Do not touch `governance-docs-consistency.yml`, `mcp-docs-consistency.yml`, or
  `backward-compat-check.yml` — already recursive, no change needed.
- This change is only correct once the corresponding physical file move has actually
  happened; do not merge this ahead of the corresponding area-move issue without
  coordinating so the workflow isn't briefly pointed at a location that doesn't exist
  yet (a non-matching path filter is silent, not an error, so a temporary mismatch
  window is low-risk but should still be minimized).

## Acceptance Criteria
- Each of the 5 workflow files' `paths:` filters (both `push` and `pull_request`
  sections) point at the new subfolder location.
- After the corresponding area-move issue lands, a test commit touching one of the
  moved files triggers the corresponding workflow (verified by observing the Actions
  run list, or by inspecting the resolved path filter with
  `gh workflow view <name> --yaml` or equivalent).
- No unrelated `paths:` entries in these 5 files are changed.

## Testing Expectations
- Manual verification only: after the corresponding files move, confirm each workflow
  triggers on a subsequent commit touching one of them (CI-level check, not a unit
  test — no `tests/` files are affected by this issue).

## Documentation Impact
N/A: covered by Summary — this is a CI configuration change with no `docs/` content or
rule documentation affected.

## Out of Scope
- Any other `paths:` entry, job step, or trigger condition in these 5 workflow files.
- `governance-docs-consistency.yml`, `mcp-docs-consistency.yml`,
  `backward-compat-check.yml`.
- Physically moving any file under `docs/`.
- Removing or shortening any filename prefix.

## Dependencies
- Should land in close coordination with (immediately before or in the same PR as) the
  corresponding area-move issues: `docsreorg` agent-area move (blocks
  `agent-docs-consistency.yml`'s change being meaningful), db-area move (for the
  `shared_04_*` half of the same workflow), overview-area move, deployment-area
  move, rag-area move.

## Unresolved Questions
N/A: none — all 5 workflow files and their current `paths:` values were directly
confirmed during issue drafting.

## AI Implementation Instruction
Change only the `paths:` list entries named in Required Changes, in the 5 named
workflow files, in both their `push` and `pull_request` sections. Do not modify any
other workflow, any job step, or any other `paths:` entry within these files. Do not
perform any physical file move as part of this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-140711
- **Related target files**: .github/workflows/agent-docs-consistency.yml, .github/workflows/overview-docs-consistency.yml, .github/workflows/deployment-docs-consistency.yml, .github/workflows/rag-docs-consistency.yml, .github/workflows/rag-docs-quality.yml
