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

## Affected areas

- `docs/05_agent_00_document-guide.md` — update guide if needed
- `docs/05_agent_01_system-overview.md` — keep high-level overview only
- `docs/05_agent_02_runtime-architecture-part1.md` — consolidate runtime architecture
- `docs/05_agent_02_runtime-architecture-part2.md` — consolidate runtime architecture
- `docs/05_agent_03_01_turn-processing-flow-overview.md` — consolidate turn flow
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` — consolidate turn flow
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` — consolidate turn flow
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part2.md` — consolidate turn flow
- `docs/05_agent_04_01_state-and-persistence-state-model-part1.md` — consolidate state/persistence
- `docs/05_agent_04_01_state-and-persistence-state-model-part2.md` — consolidate state/persistence
- `docs/05_agent_04_02_state-and-persistence-history-compression.md` — consolidate state/persistence
- `docs/05_agent_04_03_state-and-persistence-platform-databases.md` — consolidate state/persistence
- `docs/05_agent_06_01_tool-execution-and-approval-execution.md` — review and update
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md` — review and update
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` — review and update
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md` — review and update
- `docs/05_agent_07_01_cli-and-commands-cli-reference.md` — consolidate CLI command reference
- `docs/05_agent_07_02_cli-and-commands-cliview.md` — consolidate CLI command reference
- `docs/05_agent_07_03_cli-and-commands-command-registry.md` — consolidate CLI command reference
- `docs/05_agent_07_04_cli-and-commands-purpose.md` — consolidate CLI command reference
- `docs/05_agent_07_05_cli-and-commands-repl-io.md` — consolidate CLI command reference
- `docs/05_agent_07_06_cli-and-commands-hot-reload.md` — consolidate CLI command reference
- `docs/05_agent_07_07_cli-and-commands-migration-notes.md` — consolidate CLI command reference
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` — consolidate CLI command reference
- `docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md` — consolidate CLI command reference
- `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` — consolidate CLI command reference
- `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` — consolidate CLI command reference
- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` — review and update
- `docs/05_agent_08_01_configuration-loading-agent-config-part2.md` — review and update
- `docs/05_agent_08_02_configuration-llm-rag.md` — review and update
- `docs/05_agent_08_03_configuration-tools-memory.md` — review and update
- `docs/05_agent_08_04_configuration-mcp-approval-obs.md` — review and update
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_02_operations-and-observability-audit-and-otel.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_03_operations-and-observability-workflow-observability.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_05_operations-and-observability-monitoring.md` — consolidate startup/health/diagnostics
- `docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` — consolidate startup/health/diagnostics
- `docs/05_agent_12_01_memory-overview-and-modes-part1.md` — review and update
- `docs/05_agent_12_01_memory-overview-and-modes-part2.md` — review and update
- `docs/05_agent_12_02_memory-gate-data-model-search-part1.md` — review and update
- `docs/05_agent_12_02_memory-gate-data-model-search-part2.md` — review and update
- `docs/05_agent_12_03_memory-module-ref-core-and-store.md` — review and update
- `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` — review and update
- `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` — review and update
- `docs/05_agent_12_06_memory-module-ref-ops-and-scoring.md` — review and update
- `docs/05_agent_13_reference-api-part1.md` — review and update
- `docs/05_agent_13_reference-api-part2.md` — review and update
- `docs/05_agent_90_inconsistencies_and_known_issues.md` — keep only unresolved issues

## Design

### Phase 1: Verify slash command list (Step 1)

Compare documented slash commands against `scripts/agent/commands/command_defs_list.py:_COMMANDS`:

Actual commands (18 total):
- Exact-match sync: /help, /config, /stats, /context, /plan, /undo, /reload
- Exact-match async: /compact, /diff
- Prefix sync: /mcp, /session, /clear, /history, /system, /memory, /debug, /audit, /approve, /reject, /skill
- Prefix async: /mdq

Action: Check each doc's command table against this list. Remove deleted commands, add missing ones.

### Phase 2: Consolidate runtime architecture (Step 2)

Move detailed runtime architecture content to `05_agent_02_*`. Keep only high-level overview in `05_agent_01_system-overview.md`.

Current split:
- `05_agent_01_system-overview.md` — should contain only high-level overview
- `05_agent_02_runtime-architecture-part1.md` — detailed architecture (should stay here)
- `05_agent_02_runtime-architecture-part2.md` — detailed architecture (should stay here)

Action: Ensure `05_agent_01` has no detailed architecture content; move it to `05_agent_02_*`.

### Phase 3: Consolidate turn flow (Step 3)

Move all turn flow and workflow engine content to `05_agent_03_*`. Ensure WorkflowEngine is documented as required (not optional). Remove old direct execution fallback explanations.

Current split:
- `05_agent_03_01_turn-processing-flow-overview.md` — overview
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md` — LLM tool loop details
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` — workflow engine part 1
- `05_agent_03_03_turn-processing-flow-workflow-engine-part2.md` — workflow engine part 2

Action: Review for overlap between these files. Ensure WorkflowEngine is described as required.

### Phase 4: Consolidate state and persistence (Step 4)

Move all state and persistence content to `05_agent_04_*`. Update DiagnosticStore/session_diagnostics descriptions to match current implementation. Remove references to deleted diagnostics.jsonl.

Current split:
- `05_agent_04_01_state-and-persistence-state-model-part1.md` — state model part 1
- `05_agent_04_01_state-and-persistence-state-model-part2.md` — state model part 2
- `05_agent_04_02_state-and-persistence-history-compression.md` — history compression
- `05_agent_04_03_state-and-persistence-platform-databases.md` — platform databases

Known issue: `DiagnosticStore.save_loop_guard_hint()` method exists but is never called (dead code documented at 05_agent_04_01_part2 line 87).

Action: Verify session_diagnostics documentation matches current implementation. Confirm diagnostics.jsonl references are removed.

### Phase 5: Consolidate CLI command reference (Step 5)

Move all CLI command reference content to `05_agent_07_*`. Update CLIView/OutputTag/startup validation display descriptions to match implementation.

Current split across 11 files (05_agent_07_01 through 05_agent_07_11).

Action: Ensure each file covers a distinct aspect without overlap. Verify CLIView/OutputTag descriptions match actual implementation.

### Phase 6: Consolidate startup/health/diagnostics (Step 6)

Move all startup, health, and diagnostics content to `05_agent_10_*`.

Current split across 6 files (05_agent_10_01 through 05_agent_10_06).

Action: Review for overlap and ensure consistent severity classifications.

### Phase 7: Review remaining files (Steps 7-8)

Review `05_agent_08_*`, `05_agent_12_*`, `05_agent_13_*` for accuracy and consistency. Clean up known issues in `05_agent_90_inconsistencies_and_known_issues.md`.

### Phase 8: Update cross-references (Step 9)

Update File Index, AI Query Routing Table, Related Documents, and internal links after consolidation.

## Implementation steps

1. Read `scripts/agent/commands/command_defs_list.py` to get the authoritative slash command list (already done).
2. Compare documented slash commands against `_COMMANDS` in each affected doc.
3. Resolve UNK-01: Identify any documented commands that don't exist or vice versa.
4. Resolve UNK-02: Search for overlapping content in 05_agent_03_*.md files.
5. Resolve UNK-03: Read each 05_agent_06_*, 05_agent_08_*, 05_agent_12_*, 05_agent_13_* file and identify inconsistencies.
6. Make targeted edits to fix identified inconsistencies.
7. Update cross-references where needed.
8. Run lint checks on modified docs.

## Validation plan

- Verify slash command tables match `_COMMANDS` exactly
- Verify no duplicate content across consolidated files
- Verify all internal links resolve correctly after changes
- Verify WorkflowEngine is consistently described as required
- Verify no references to deleted features remain
- Check that Related Documents sections are updated with correct relative paths

## Risks

- **Medium risk**: This is a large reorganization affecting many files. Changes may introduce new inconsistencies if not carefully reviewed.
  - Mitigation: Process one phase at a time, verify each before moving to the next. Use grep to check for broken references after changes.
- **Low risk**: Cross-reference updates may miss some links.
  - Mitigation: After all edits, run `grep -r "05_agent_" docs/` to find any remaining absolute paths that should be relative.
- **Low risk**: Some existing inconsistencies may require source code investigation beyond documentation review.
  - Mitigation: Document unresolved items in `05_agent_90_inconsistencies_and_known_issues.md` rather than guessing.

## Traceability

- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/ready/20260722-124547_require.md
- Source plan: plans/20260722-165130_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-165130
- Related target files: 47 files under docs/05_agent_*/
