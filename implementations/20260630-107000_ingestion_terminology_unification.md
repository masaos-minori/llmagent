## Goal
- Clarify `stage_name` field description in RAG ingestion docs to prevent confusion with query pipeline Stage classes, and verify terminology consistency across all ingestion-related documents.

## Scope
- **In-Scope**:
  - Verify `docs/03_rag_01_system_overview.md:L70-80` has "3 scripts / 4 processing phases" definition
  - Clarify `docs/03_rag_02_ingestion_pipeline.md:L652` `stage_name` description ("Stage name string" → accurate description)
  - Verify no ambiguous `stage` usage in ingestion docs
  - Verify cross-references to system overview exist
- **Out-of-Scope**:
  - Query pipeline Stage class renaming (MqeStage, FusionStage, etc.)
  - `stage_name` DB field name changes (breaks backward compatibility)
  - Runtime behavior changes

## Findings

### 1. "3 scripts / 4 processing phases" definition — Already present
`03_rag_01_system_overview.md:L70-L80`:
```
**3 scripts / 4 processing phases**
> **Terminology:** "3 scripts" refers to the three executable files (crawler.py, chunk_splitter.py, ingester.py).
> "4 processing phases" refers to the four logical steps (Crawl, Chunk, Embed, Store) — two of which run inside ingester.py.
```

### 2. `stage_name` description — Ambiguous, needs clarification
`03_rag_02_ingestion_pipeline.md:L652`:
- Current: `| stage_name | Stage name string | ingester |`
- Issue: "Stage name string" sounds like it refers to an ingestion processing phase (e.g., "chunk", "embed"), but code shows it's always `"ingester"` — the script name, not a phase label.
- Fix: `| stage_name | Script name (always "ingester") | ingester |`

### 3. No ambiguous `stage` usage in ingestion docs
- `03_rag_02_ingestion_pipeline.md`: no `stage` references ✓
- `03_rag_05_configuration_and_operations.md`: no `stage` references ✓

### 4. Cross-references to system overview — Already present
- `03_rag_02_ingestion_pipeline.md:L3`: "System overview → [03_rag_01_system_overview.md]" ✓
- `03_rag_05_configuration_and_operations.md:L3`: "System overview → [03_rag_01_system_overview.md]" ✓

## Conclusion
Only change needed: clarify `stage_name` description at L652 to prevent confusion with query pipeline Stage classes.
