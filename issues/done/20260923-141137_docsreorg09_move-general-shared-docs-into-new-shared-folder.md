# Move general shared docs into new shared folder

## Priority
Medium

## Summary
`git mv` the 9 general-shared (non-DB) files from `docs/` (flat) into a new
`docs/40_shared/` subfolder. No filename or content change beyond required reference
fixups. The DB-specific subset of `shared_*` is a separate area (`41_db`, see
`docsreorg10`) and is out of scope here.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `40_shared` area — the general-purpose subset of
the current `shared_*` files (document-guide, overview, types/protocols,
runtime/execution). The DB-architecture and DB-API subsets (`shared_04_*`,
`shared_05_*`) move separately into `41_db` per `docsreorg10`, since they form a
distinct, self-contained topic.

## Problem
`docs/90_shared_00_document-guide.md`, `docs/shared_01_overview.md`,
`docs/90_shared_02_01_types_and_protocols-core-types.md`,
`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`,
`docs/90_shared_02_03_types_and_protocols-reference.md`,
`docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`,
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`,
`docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`,
`docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` currently sit
directly under `docs/` alongside all other areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this subset of shared/cross-domain docs into its
own folder, separate from the DB-specific subset which has its own distinct area.

## Implementation Intent
Use `git mv` only — do not rename any file. Move exactly the 9 files listed below into
`docs/40_shared/`. Do not move any `shared_04_*`/`shared_05_*` file here — those
belong to `docsreorg10`.

## Target Files or Areas
- `docs/90_shared_00_document-guide.md` → `docs/40_shared/90_shared_00_document-guide.md`
- `docs/shared_01_overview.md` → `docs/40_shared/shared_01_overview.md`
- `docs/90_shared_02_01_types_and_protocols-core-types.md` → `docs/40_shared/90_shared_02_01_types_and_protocols-core-types.md`
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` → `docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
- `docs/90_shared_02_03_types_and_protocols-reference.md` → `docs/40_shared/90_shared_02_03_types_and_protocols-reference.md`
- `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` → `docs/40_shared/90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` → `docs/40_shared/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` → `docs/40_shared/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` → `docs/40_shared/90_shared_03_04_runtime_and_execution-caching-and-reference.md`

## Required Changes
- `git mv` each of the 9 files listed above into `docs/40_shared/`.
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to any of these 9 files (confirmed during issue drafting) — no
  baseline update expected.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- `docsreorg02`'s `_docs_consistency_lib.py`/`check_docs_consistency.py` fix must
  already point the "shared" domain's `discover_md_files` call at the correct new
  subfolder before this move, since `check_agent_docs_consistency.py` (per
  `docsreorg02`'s Problem) also reads `shared_04_*` for cross-domain checks — verify
  that dependency does not implicitly also expect the general-shared files to remain in
  the old flat location.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any `shared_04_*`/`shared_05_*` file (tracked by `docsreorg10`).

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the general-shared area.

## Out of Scope
- Moving any `shared_04_*`/`shared_05_*` file (tracked by `docsreorg10`).
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg04` (canonical reference updates), `docsreorg10` (the
  DB-specific subset of the current `shared_*` files, which must not be confused
  with this issue's scope).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Move only the 9 files listed, using `git mv`, into `docs/40_shared/`. Do not include any
`shared_04_*`/`shared_05_*` file. Do not rename any file. If
`docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141137
- **Related target files**: docs/90_shared_00_document-guide.md, docs/shared_01_overview.md, docs/90_shared_02_01_types_and_protocols-core-types.md, docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md, docs/90_shared_02_03_types_and_protocols-reference.md, docs/90_shared_03_01_runtime_and_execution-config-and-logging.md, docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md, docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md, docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md
