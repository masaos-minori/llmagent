# Implementation: docs/06_shared_99_source_mapping.md

## Goal

Create an audit table mapping every significant section from all 4 source files to its
new location in the restructured documentation set.

## Scope

- Covers all 4 source files: 06_shared.md (96L), 06_spec_shared.md (383L),
  07_spec_db.md (367L), 07_ref-sqlite.md (601L)
- Output: `docs/06_shared_99_source_mapping.md`

## Assumptions

- Mapping columns: Source File | Source Section | New File | New Section | Status
- Status values: Preserved / Summarized+Link / Merged / Flag(see 90)
- "Preserved" = moved without loss; "Summarized" = reduced with link to canonical

## Implementation

### Target file

`docs/06_shared_99_source_mapping.md`

### Procedure

Build the mapping table for each source file:

1. `06_shared.md` (96 lines):
   - §モジュールインデックス → 06_shared_01 §Module Table | Preserved
   - §共通プロトコル仕様 (MCP v1/call_tool, plugin return tuple) → 06_shared_03 §ToolExecutor | Preserved
   - §RagHit TypedDict → 06_shared_02 §RagHit | Preserved
   - §LLMMessage TypedDict (5-field version) → 06_shared_02 §LLMMessage | Flag(see 90-SPEC_CONFLICT-9)
   - §RagConfig Protocol → 06_shared_02 §RagConfig | Preserved

2. `06_spec_shared.md` (383 lines):
   - §1-5 (purpose/scope/background/prereqs/constraints) → 06_shared_01 §1-5 | Preserved
   - §6.1 ConfigLoader → 06_shared_03 §ConfigLoader | Preserved
   - §6.2 Logger → 06_shared_03 §Logger | Preserved
   - §6.3 types.py → 06_shared_02 §LLMMessage / §RagConfig | Preserved
   - §6.4 tool_constants → 06_shared_02 §tool_constants | Preserved
   - §6.5 plugin_registry → 06_shared_03 §plugin_registry | Preserved
   - §6.6 OTel tracer → 06_shared_03 §OTel | Preserved
   - §6.7 token_counter → 06_shared_03 §token_counter | Preserved
   - §6.8 formatters → 06_shared_03 §formatters | Preserved
   - §6.9 llm_types → 06_shared_02 §LLMUsage/LLMResponse | Preserved
   - §6.10 action_result → 06_shared_02 §ActionResult | Preserved
   - §6.11 events → 06_shared_02 §ArtifactEvent | Preserved
   - §6.12 ShellPolicy → 06_shared_02 §ShellPolicy | Preserved
   - §7 I/O (ConfigLoader/Logger/ToolExecutor usage) → 06_shared_03 §7 | Preserved
   - §8 processing flows → 06_shared_03 §ToolExecutor flow | Preserved
   - §9.1-9.7 data specs → 06_shared_02 all types | Preserved
   - §10 public interfaces → 06_shared_03 §10 | Preserved
   - §11 error handling → 06_shared_03 §Error Handling | Preserved
   - §12 validation plan → (retained as internal reference)
   - §13 known issues → 06_shared_90 issues 1-10 | Preserved

3. `07_spec_db.md` (367 lines):
   - §1-5 (purpose/scope/background/prereqs/constraints) → 06_shared_04 §1-5 | Preserved
   - §6 functional requirements → 06_shared_04 §Architecture | Preserved
   - §7 I/O (SQLiteHelper, DbConfig) → 06_shared_04 §DbConfig | Preserved
   - §8 processing flows → 06_shared_04 §Flows | Preserved
   - §9.1 rag.sqlite schema → 06_shared_04 §rag.sqlite | Preserved
   - §9.2 session.sqlite schema → 06_shared_04 §session.sqlite | Preserved
   - §10 public interfaces → 06_shared_05 §1-4 | Preserved
   - §11 error handling → 06_shared_05 §Error Handling | Preserved
   - §12 validation plan → (retained as internal reference)
   - §13 known issues → 06_shared_90 issues 11-12 | Preserved

4. `07_ref-sqlite.md` (601 lines):
   - §db/helper.py constructor (incl. workflow target) → 06_shared_04 §Target Table + 06_shared_05 §open() | Preserved; workflow gap → Flag(see 90-DOC-13)
   - §SQLiteHelper.open detailed spec → 06_shared_05 §open() | Preserved
   - §SQLiteHelper.execute/executemany/fetchall/commit/close → 06_shared_05 §methods | Preserved
   - §begin_immediate/begin_exclusive → 06_shared_05 §transactions | Preserved
   - §health_check/checkpoint/vacuum → 06_shared_05 §operations | Preserved
   - §db/store.py embedding helpers → 06_shared_05 §embedding helpers | Preserved
   - §VectorStore/DocumentStore/SessionStore Protocols → 06_shared_05 §Protocols | Preserved
   - §SQLite backend implementations → 06_shared_05 §Implementations | Preserved
   - §MemoryDeleteStore → 06_shared_05 §MemoryDeleteStore | Preserved
   - §db/maintenance.py full API → 06_shared_05 §maintenance | Preserved
   - §db/tool_results.py ToolResultStore → 06_shared_05 §ToolResultStore | Preserved
   - §memories/memories_fts/memories_vec/memory_links tables → 06_shared_04 §session.sqlite + 06_shared_05 §MemoryStore | Preserved
   - §MemoryStore API → 06_shared_05 §MemoryStore | Preserved; layer note → Flag(see 90-DOC-17)
   - §db/workflow_schema.py → 06_shared_04 §workflow.sqlite | Preserved; spec gap → Flag(see 90-DOC-13)

### Method

- Table format: Source File | Source Section | New File | New Section | Status
- Coverage Summary section at end confirming all 4 source files fully mapped
- Flag entries cross-reference 06_shared_90 issue numbers

## Validation plan

- File exists at `docs/06_shared_99_source_mapping.md`
- All 4 source files appear in the mapping table
- Coverage Summary present
- Flag entries reference 06_shared_90
- No source section left unmapped
