## Goal

Fix stale references to non-existent config files (`rag_pipeline.toml`, `common.toml`) in RAG documentation.

## Scope

- Update `docs/03_rag_01_system_overview-part2.md` — remove rag_pipeline.toml references (lines 50, 86)
- Update `docs/03_rag_02_07_ingestion_pipeline-utils.md` — remove rag_pipeline.toml reference (line 69)
- Update `docs/03_rag_05_2-execution-guide.md` — remove rag_pipeline.toml references (lines 23, 29)
- Update `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md` — remove common.toml reference (line 49)

## Assumptions

1. The existing documentation structure and content are correct; only the stale references need correction
2. Each MCP server loads its own `<key>_mcp_server.toml` instead of a shared `rag_pipeline.toml`
3. Agent config is consolidated into `agent.toml` instead of using `common.toml`

## Design decisions

- Remove the stale references entirely since they refer to non-existent files
- If the context around the reference is still relevant, add a note explaining the actual config mechanism

## Alternatives considered

- Adding inline notes within existing sections instead of removing references
- Creating a separate appendix for config file mapping

## Implementation

### Target files

- `docs/03_rag_01_system_overview-part2.md`
- `docs/03_rag_02_07_ingestion_pipeline-utils.md`
- `docs/03_rag_05_2-execution-guide.md`
- `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`

### Procedure

#### Step 1: Fix rag_pipeline.toml references

For each file containing rag_pipeline.toml references:

1. Open the file
2. Find the line(s) referencing `rag_pipeline.toml`
3. Replace with accurate description of how MCP servers load their own config

Change from:

```markdown
... references config/rag_pipeline.toml ...
```

To:

```markdown
... each MCP server loads its own <key>_mcp_server.toml configuration file ...
```

Files affected:
- `docs/03_rag_01_system_overview-part2.md` (lines 50, 86)
- `docs/03_rag_02_07_ingestion_pipeline-utils.md` (line 69)
- `docs/03_rag_05_2-execution-guide.md` (lines 23, 29)

#### Step 2: Fix common.toml reference

1. Open `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`
2. Find line 49 referencing `common.toml::embedding_dims`
3. Replace with accurate description of where embedding_dims is configured

Change from:

```markdown
... references common.toml::embedding_dims ...
```

To:

```markdown
... embedding_dims is configured in agent.toml ...
```

#### Step 3: Verify cross-references

If there are any cross-references to these sections elsewhere in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The corrected references help prevent misunderstanding about config file locations

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the fixes if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_01_system_overview-part2.md` | Stale reference removal | grep for rag_pipeline.toml | No rag_pipeline.toml references remain |
| `docs/03_rag_02_07_ingestion_pipeline-utils.md` | Stale reference removal | grep for rag_pipeline.toml | No rag_pipeline.toml references remain |
| `docs/03_rag_05_2-execution-guide.md` | Stale reference removal | grep for rag_pipeline.toml | No rag_pipeline.toml references remain |
| `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md` | Stale reference removal | grep for common.toml | No common.toml references remain |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124909_require.md
- Source plan: plans/20260722-170440_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181341
- Related target files: docs/03_rag_01_system_overview-part2.md, docs/03_rag_02_07_ingestion_pipeline-utils.md, docs/03_rag_05_2-execution-guide.md, docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md
