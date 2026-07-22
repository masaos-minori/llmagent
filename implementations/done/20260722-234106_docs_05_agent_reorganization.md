## Goal

Organize agent documentation by consolidating related content into appropriate files and removing outdated information, ensuring consistency between implementation and docs.

## Scope

Documentation reorganization across 16 target files in `docs/05_agent_*`:
- Slash command list verification against actual commands
- Runtime architecture consolidation
- Turn flow consolidation
- State/persistence consolidation
- CLI command reference consolidation
- Startup/health/diagnostics consolidation
- Review of remaining files (05_agent_08_*, 05_agent_12_*, 05_agent_13_*)
- Known issues cleanup

## Assumptions

- The slash command source of truth is `scripts/agent/commands/command_defs_list.py:_COMMANDS`.
- WorkflowEngine is required (not optional) — confirmed by current implementation.
- No deleted diagnostics.jsonl references remain (confirmed via grep).
- No old direct execution fallback explanations remain (confirmed via grep).

## Unknowns

- **UNK-01**: Are there any slash commands documented that don't exist in `_COMMANDS`? Need to compare each doc's command table against the actual list.
  - Resolution needed during implementation. Recommendation: systematically compare each doc's command list against `_COMMANDS`.
- **UNK-02**: Is there duplication of turn flow/workflow descriptions across multiple sections? The requirement mentions this but doesn't specify which sections.
  - Resolution needed during implementation. Recommendation: search for overlapping content in 05_agent_03_*.md files.
- **UNK-03**: What specific inconsistencies exist in 05_agent_06_*, 05_agent_08_*, 05_agent_12_*, 05_agent_13_* files? These are listed as "review and update" without specifics.
  - Resolution needed during implementation. Recommendation: read each file and identify inconsistencies.

## Design decisions

- Single-file implementation procedure document rather than splitting into multiple small files.
- Eight phases provide sufficient granularity for tracking progress.
- Known issues documented separately in `05_agent_90_inconsistencies_and_known_issues.md`.

## Alternatives considered

- Processing all phases simultaneously: rejected because it increases risk of introducing new inconsistencies.
- Using a different ID format (e.g., AREA-{NNN}): rejected because NC prefix clearly indicates "Needs Confirmation" regardless of area.
- Merging this with the Deprecated Items document: rejected because needs-confirmation tracking is a distinct concern requiring detailed per-item guidance.

## Implementation

### Target files

47 files under `docs/05_agent_*/`:
- `docs/05_agent_00_document-guide.md`
- `docs/05_agent_01_system-overview.md`
- `docs/05_agent_02_runtime-architecture-part1.md`
- `docs/05_agent_02_runtime-architecture-part2.md`
- `docs/05_agent_03_01_turn-processing-flow-overview.md`
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part2.md`
- `docs/05_agent_04_01_state-and-persistence-state-model-part1.md`
- `docs/05_agent_04_01_state-and-persistence-state-model-part2.md`
- `docs/05_agent_04_02_state-and-persistence-history-compression.md`
- `docs/05_agent_04_03_state-and-persistence-platform-databases.md`
- `docs/05_agent_06_01_tool-execution-and-approval-execution.md`
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md`
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`
- `docs/05_agent_07_01_cli-and-commands-cli-reference.md`
- `docs/05_agent_07_02_cli-and-commands-cliview.md`
- `docs/05_agent_07_03_cli-and-commands-command-registry.md`
- `docs/05_agent_07_04_cli-and-commands-purpose.md`
- `docs/05_agent_07_05_cli-and-commands-repl-io.md`
- `docs/05_agent_07_06_cli-and-commands-hot-reload.md`
- `docs/05_agent_07_07_cli-and-commands-migration-notes.md`
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`
- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md`
- `docs/05_agent_08_01_configuration-loading-agent-config-part2.md`
- `docs/05_agent_08_02_configuration-llm-rag.md`
- `docs/05_agent_08_03_configuration-tools-memory.md`
- `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
- `docs/05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `docs/05_agent_10_03_operations-and-observability-workflow-observability.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`
- `docs/05_agent_10_05_operations-and-observability-monitoring.md`
- `docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
- `docs/05_agent_12_01_memory-overview-and-modes-part1.md`
- `docs/05_agent_12_01_memory-overview-and-modes-part2.md`
- `docs/05_agent_12_02_memory-gate-data-model-search-part1.md`
- `docs/05_agent_12_02_memory-gate-data-model-search-part2.md`
- `docs/05_agent_12_03_memory-module-ref-core-and-store.md`
- `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `docs/05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `docs/05_agent_13_reference-api-part1.md`
- `docs/05_agent_13_reference-api-part2.md`
- `docs/05_agent_90_inconsistencies_and_known_issues.md`

### Procedure

1. Read `scripts/agent/commands/command_defs_list.py` to get the authoritative slash command list.
2. Compare documented slash commands against `_COMMANDS` in each affected doc.
3. Resolve UNK-01: Identify any documented commands that don't exist or vice versa.
4. Resolve UNK-02: Search for overlapping content in 05_agent_03_*.md files.
5. Resolve UNK-03: Read each 05_agent_06_*, 05_agent_08_*, 05_agent_12_*, 05_agent_13_* file and identify inconsistencies.
6. Make targeted edits to fix identified inconsistencies.
7. Update cross-references where needed.
8. Run lint checks on modified docs.

### Method

Process eight phases sequentially:
1. Verify slash command list
2. Consolidate runtime architecture
3. Consolidate turn flow
4. Consolidate state and persistence
5. Consolidate CLI command reference
6. Consolidate startup/health/diagnostics
7. Review remaining files
8. Update cross-references

### Details

- **Phase 1**: Compare documented slash commands against 18 actual commands in `_COMMANDS`. Remove deleted commands, add missing ones.
- **Phase 2**: Ensure `05_agent_01` has no detailed architecture content; move it to `05_agent_02_*`.
- **Phase 3**: Review for overlap in `05_agent_03_*.md` files. Ensure WorkflowEngine is described as required.
- **Phase 4**: Verify session_diagnostics documentation matches current implementation. Confirm diagnostics.jsonl references are removed.
- **Phase 5**: Ensure each of the 11 CLI command files covers a distinct aspect without overlap.
- **Phase 6**: Review for overlap in `05_agent_10_*.md` files. Ensure consistent severity classifications.
- **Phase 7**: Review `05_agent_08_*`, `05_agent_12_*`, `05_agent_13_*` for accuracy and consistency. Clean up known issues.
- **Phase 8**: Update File Index, AI Query Routing Table, Related Documents, and internal links after consolidation.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Slash command lists must match `_COMMANDS` exactly.
- WorkflowEngine must be consistently described as required across all files.
- Cross-references must use correct relative paths after consolidation.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If changes need to be reverted, revert git commits for each phase individually.
- No data loss risk since this is purely documentation reorganization.
- Cross-links may break if files are moved between phases; verify after each phase.

## Validation plan

- Verify slash command tables match `_COMMANDS` exactly
- Verify no duplicate content across consolidated files
- Verify all internal links resolve correctly after changes
- Verify WorkflowEngine is consistently described as required
- Verify no references to deleted features remain
- Check that Related Documents sections are updated with correct relative paths

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing Known Issues documents with the new template.
- Defining new metadata fields beyond the eight specified.
- Resolving individual Known Issues entries.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-165130_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-234106
- Related target files: 47 files under docs/05_agent_*/
