# Move ADR docs into new adr folder

## Priority
Medium

## Summary
`git mv` the 14 ADR files from `docs/adr/` plus `docs/adr-index.md` into a new
`docs/10_adr/` subfolder. No filename or content change beyond required reference
fixups.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `10_adr` area — the only area move that changes an
*existing* subfolder's name (`docs/adr/` → `docs/10_adr/`), not a flat-to-subfolder
move.

## Problem
`docs/adr/ADR-001-workflow-engine-mandatory.md` through `ADR-015-...md` (14 files,
IDs 001-010, 012-015 — ADR-011 does not exist, it was merged into ADR-008 per an
earlier, unrelated decision) live in `docs/adr/`, and `docs/adr-index.md` lives
directly under `docs/`. `docsreorg02`'s Target Files already lists the tools
(`check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`,
`check_known_deviation_sync.py`'s `ADR_DIR` constant) whose hardcoded `docs/adr`
references depend on this exact move.

## Reason for Change
Same rationale as `docsreorg05`: fold this existing subfolder into the new
area-numbered scheme so `docs/` has one consistent top-level structure.

## Implementation Intent
Use `git mv` only — do not rename any file (the `ADR-NNN-slug.md` names are unaffected,
and `adr-index.md` keeps its current bare name). Move the entire contents of
`docs/adr/` plus `docs/adr-index.md` into `docs/10_adr/`.

## Target Files or Areas
- `docs/adr/ADR-001-workflow-engine-mandatory.md` through
  `docs/adr/ADR-015-reference-document-class-disposition.md` (all 14 existing files
  under `docs/adr/`) → same filename under `docs/10_adr/`
- `docs/adr-index.md` → `docs/10_adr/adr-index.md`

## Required Changes
- `git mv docs/adr docs/10_adr` (moves all 14 ADR files at once, preserving the
  directory's contents) — or move each file individually if the tooling in use
  requires per-file `git mv` calls; either way, every existing file under `docs/adr/`
  ends up under `docs/10_adr/` with its filename unchanged.
- `git mv docs/adr-index.md docs/10_adr/adr-index.md`.
- Confirm this move happens no earlier than `docsreorg02`'s corresponding tool fixes
  (`check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`,
  `check_known_deviation_sync.py`'s `ADR_DIR`) have landed — these tools hardcode
  `docs/adr`/`docs/adr-index.md` and will fail to find their target files otherwise.
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to any ADR file or `adr-index.md` (confirmed during issue drafting)
  — no baseline update expected.

## Constraints
- `git mv` only — no filename change (ADR IDs and slugs stay exactly as they are), no
  content rewriting beyond what `docsreorg04` already covers.
- Do not attempt to fill the ADR-011 numbering gap or otherwise touch ADR numbering as
  part of this issue.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python -m tools.check_adr_structure` (or the equivalent invocation) finds all
  14 ADRs and `adr-index.md` at their new location with zero new findings.
- `uv run python -m tools.check_adr_reference` and
  `uv run python -m tools.check_adr_invariant_matrix` pass against the new location.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run pre-commit run adr-invariant-matrix adr-reference-scoped --all-files` passes.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q` (covers the ADR-specific tool tests updated by
  `docsreorg02`)

## Documentation Impact
This issue is itself the documentation-location change for the ADR area.

## Out of Scope
- Any filename change, including not renaming `adr-index.md` to add a numeric prefix.
- Filling the ADR-011 numbering gap.
- Any content edit beyond what `docsreorg04` already covers.
- The known pre-existing broken body links from `ADR-008-sqlite-4db-separation.md` and
  `ADR-010-rag-fallback.md` to non-existent target files (tracked separately, e.g.
  issue DOC-001) — not touched by this move.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02` (specifically its
  `check_adr_structure.py`/`check_adr_reference.py`/`check_adr_invariant_matrix.py`/
  `check_known_deviation_sync.py` path updates — hard blocker, since these tools are
  wired into pre-commit hooks).
- Coordinate with: `docsreorg04` (canonical reference updates).

## Unresolved Questions
N/A: none — the ADR-011 gap and its "merged into ADR-008" resolution were already
confirmed as an independent, pre-existing decision unrelated to this move.

## AI Implementation Instruction
Move the entire `docs/adr/` directory's contents plus `docs/adr-index.md` into
`docs/10_adr/`, using `git mv`, with no filename changes. Confirm `docsreorg02`'s
ADR-tool path updates have landed before merging — if not, stop and report `Blocked`
rather than proceeding while pre-commit ADR hooks would silently stop finding their
target files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141237
- **Related target files**: docs/adr/ADR-001-workflow-engine-mandatory.md, docs/adr/ADR-002-config-isolation.md, docs/adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/adr/ADR-004-environment-failure-handling-policy.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md, docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/adr/ADR-008-sqlite-4db-separation.md, docs/adr/ADR-009-rag-ft5-text-separation.md, docs/adr/ADR-010-rag-fallback.md, docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md, docs/adr/ADR-013-eventbus-authentication-authorization.md, docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md, docs/adr/ADR-015-reference-document-class-disposition.md, docs/adr-index.md
