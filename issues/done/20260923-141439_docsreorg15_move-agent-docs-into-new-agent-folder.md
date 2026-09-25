# Move agent docs into new agent folder

## Priority
Medium

## Summary
`git mv` all 47 `docs/05_agent_*.md` files from `docs/` (flat) into a new
`docs/23_agent/` subfolder. No filename or content change beyond required reference
fixups and baseline updates. This is the largest area by file count — execute last
among the area-move issues, after the process has been validated on smaller areas.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `23_agent` area.

## Problem
All 47 `docs/05_agent_*.md` files (document guide, system/runtime overview, the
turn-processing group, the state/persistence group, the tool-execution-and-approval
group, the 11-file CLI-and-commands group, the configuration group, the data-layer
group, the operations-and-observability group, the memory group, and the reference-API
pair) currently sit directly under `docs/` alongside all other areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this area's docs into its own folder as part of
the broader `docs/` reorganization.

## Implementation Intent
Use `git mv` only — do not rename any file. Move all 47 files listed in Target Files
into `docs/23_agent/`.

## Target Files or Areas
All 47 files matching `docs/05_agent_*.md`, listed in full under Traceability's
Related target files below.

## Required Changes
- `git mv` each of the 47 `docs/05_agent_*.md` files into `docs/23_agent/`.
- Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`: change
  all 29 keys currently prefixed with a bare `agent_*.md` filename to include the new
  `23_agent/` folder prefix.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- Coordinate with `docsreorg03`'s `agent-docs-consistency.yml` path-filter update
  (its `docs/05_agent_*.md` half) and `docsreorg04`'s reference updates, including
  `routing.md`'s mention of
  `agent_10_01_operations-and-observability-startup-and-health.md`.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any file outside the `agent_*.md` set.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the 29 updated
  `EXPECTED_WITHIN_FILE_PAIRS` keys.
- `uv run python -m tools.check_docs_consistency` (agent domain) passes against the new
  location.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the agent area.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.
- Moving any file belonging to a different area (including the `shared_04_*` DB
  files that `check_agent_docs_consistency.py` also reads for a cross-domain check —
  those move separately per `docsreorg10`).

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg03` (`agent-docs-consistency.yml` path filter),
  `docsreorg04` (canonical reference updates), `docsreorg10` (the `shared_04_*`
  cross-domain dependency this area's consistency checker also reads).

## Unresolved Questions
N/A: none — the full 47-file list and the 29-entry baseline count were directly
confirmed during issue drafting.

## AI Implementation Instruction
Move all 47 `docs/05_agent_*.md` files, using `git mv`, into `docs/23_agent/`. Do not
rename any file. Update exactly the 29 `EXPECTED_WITHIN_FILE_PAIRS` keys that reference
these files. If `docsreorg01`/`docsreorg02` have not landed yet, stop and report
`Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141439
- **Related target files**: docs/agent_00_document-guide.md, docs/agent_01_system-overview.md, docs/agent_02_runtime-architecture.md, docs/agent_03_01_turn-processing-flow-overview.md, docs/agent_03_02_turn-processing-flow-llm-tool-loop.md, docs/agent_03_03_turn-processing-flow-workflow-engine.md, docs/agent_04_01_state-and-persistence-state-model.md, docs/agent_04_02_state-and-persistence-history-compression.md, docs/agent_04_03_state-and-persistence-platform-databases.md, docs/agent_05_llm-and-streaming.md, docs/agent_06_01_tool-execution-and-approval-execution.md, docs/agent_06_02_tool-execution-and-approval-approval.md, docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md, docs/agent_06_04_tool-execution-and-approval-canonical.md, docs/agent_07_01_cli-and-commands-cli-reference.md, docs/agent_07_02_cli-and-commands-cliview.md, docs/agent_07_03_cli-and-commands-command-registry.md, docs/agent_07_04_cli-and-commands-purpose.md, docs/agent_07_05_cli-and-commands-repl-io.md, docs/agent_07_06_cli-and-commands-hot-reload.md, docs/agent_07_07_cli-and-commands-migration-notes.md, docs/agent_07_08_cli-and-commands-slash-commands-session-mcp.md, docs/agent_07_09_cli-and-commands-slash-commands-context-db.md, docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md, docs/agent_07_11_cli-and-commands-slash-commands-memory-other.md, docs/agent_08_01_configuration-loading-agent-config.md, docs/agent_08_02_configuration-llm-rag.md, docs/agent_08_03_configuration-tools-memory.md, docs/agent_08_04_configuration-mcp-approval-obs.md, docs/agent_09_01_data-layer-session-db.md, docs/agent_09_02_data-layer-access-patterns.md, docs/agent_09_03_data-layer-indexing-boundaries.md, docs/agent_10_01_operations-and-observability-startup-and-health.md, docs/agent_10_02_operations-and-observability-audit-and-otel.md, docs/agent_10_03_operations-and-observability-workflow-observability.md, docs/agent_10_04_operations-and-observability-validation-and-troubleshooting.md, docs/agent_10_05_operations-and-observability-monitoring.md, docs/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md, docs/agent_12_01_memory-overview-and-modes.md, docs/agent_12_02_memory-gate-data-model-search.md, docs/agent_12_03_memory-module-ref-core-and-store.md, docs/agent_12_04_memory-module-ref-retrieval-and-injection.md, docs/agent_12_05_memory-module-ref-extraction-and-facade.md, docs/agent_12_06_memory-module-ref-ops-and-scoring.md, docs/agent_12_07_memory-module-reference-generated.md, docs/agent_13_reference-api.md, docs/agent_14_reference-api-generated.md, tests/tools/test_check_docs_quality.py
