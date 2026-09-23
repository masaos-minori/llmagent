# Move mcp docs into new mcp folder

## Priority
Medium

## Summary
`git mv` all 42 `docs/04_mcp_*.md` files from `docs/` (flat) into a new `docs/22_mcp/`
subfolder. No filename or content change beyond required reference fixups and baseline
updates.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `22_mcp` area — the largest single area by file
count (42 files).

## Problem
All 42 `docs/04_mcp_*.md` files (document guide, system overview, tool ownership
matrix, the endpoints/transport group, the dispatch/registry/lifecycle group, the
tool-family groups, the access-control/auth group, the 17-file configuration-reference
group, and the schema/naming-convention pair) currently sit directly under `docs/`
alongside all other areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this area's docs into its own folder as part of
the broader `docs/` reorganization.

## Implementation Intent
Use `git mv` only — do not rename any file. Move all 42 files listed in Target Files
into `docs/22_mcp/`.

## Target Files or Areas
All 42 files matching `docs/04_mcp_*.md`, listed in full under Traceability's Related
target files below.

## Required Changes
- `git mv` each of the 42 `docs/04_mcp_*.md` files into `docs/22_mcp/`.
- Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`: change
  all 23 keys currently prefixed with a bare `04_mcp_*.md` filename to include the new
  `22_mcp/` folder prefix.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- Coordinate with `docsreorg04`'s reference updates, including `routing.md`'s specific
  mentions of `04_mcp_03_01_dispatch-and-routing.md` and
  `04_mcp_06_02_configuration-file-inventory.md`. No CI workflow path filter targets
  `docs/04_mcp_*.md` specifically (`mcp-docs-consistency.yml` already uses
  `docs/**/*.md`, confirmed unaffected) — no `docsreorg03` coordination needed for this
  area.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any file outside the `04_mcp_*.md` set.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the 23 updated
  `EXPECTED_WITHIN_FILE_PAIRS` keys.
- `uv run python -m tools.check_docs_consistency` (mcp domain) passes against the new
  location.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the mcp area.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.
- Moving any file belonging to a different area.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg04` (canonical reference updates, specifically
  `routing.md`'s two mcp-specific path mentions).

## Unresolved Questions
N/A: none — the full 42-file list and the 23-entry baseline count were directly
confirmed during issue drafting.

## AI Implementation Instruction
Move all 42 `docs/04_mcp_*.md` files, using `git mv`, into `docs/22_mcp/`. Do not rename
any file. Update exactly the 23 `EXPECTED_WITHIN_FILE_PAIRS` keys that reference these
files. If `docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141411
- **Related target files**: docs/04_mcp_00_document-guide.md, docs/04_mcp_01_system_overview.md, docs/04_mcp_01_tool_ownership_matrix.md, docs/04_mcp_02_01_endpoints-and-transport.md, docs/04_mcp_02_02_startup-modes-and-health.md, docs/04_mcp_02_03_audit-logging-and-errors.md, docs/04_mcp_02_service_boundaries.md, docs/04_mcp_03_01_dispatch-and-routing.md, docs/04_mcp_03_02_tool-registry.md, docs/04_mcp_03_03_transport-and-health.md, docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md, docs/04_mcp_03_05_lifecycle-and-new-server.md, docs/04_mcp_03_06_tool-runtime-availability-metadata.md, docs/04_mcp_04_01_web-search-file-read-github.md, docs/04_mcp_04_02_file-write-file-delete-shell.md, docs/04_mcp_04_03_rag-pipeline-and-cicd.md, docs/04_mcp_04_04_mdq.md, docs/04_mcp_04_05_git.md, docs/04_mcp_05_01_access-control-and-allowlists.md, docs/04_mcp_05_02_auth-profiles-and-sandboxing.md, docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md, docs/04_mcp_05_04_mdq-rag-boundary.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md, docs/04_mcp_06_01_purpose.md, docs/04_mcp_06_02_configuration-file-inventory.md, docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/04_mcp_06_04_major-default-values.md, docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md, docs/04_mcp_06_06_verification-methods.md, docs/04_mcp_06_07_reading-audit-logs.md, docs/04_mcp_06_08_end-to-end-tool-call-tracing.md, docs/04_mcp_06_09_mcp-failure-diagnosis.md, docs/04_mcp_06_10_settings-with-high-operational-impact.md, docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md, docs/04_mcp_06_12_watchdog-configuration-monitoring.md, docs/04_mcp_06_13_watchdog-health-reasons-scheduling.md, docs/04_mcp_06_14_new-tool-registration-procedure.md, docs/04_mcp_06_15_new-mcp-server-addition-checklist.md, docs/04_mcp_06_16_pre-production-fail-open-checklist.md, docs/04_mcp_06_17_local-to-production-auth-migration.md, docs/04_mcp_07_tool_schema_export_policy.md, docs/04_mcp_08_tool_capability_naming_convention.md, tests/tools/test_check_docs_quality.py
