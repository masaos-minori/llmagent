# Implementation Procedure: Standardize document templates, minimum behavioral contracts, and diagrams in `docs/`

## Goal
Add a governance template document covering the six untemplated document classes (Governance, Guide, Specification, Reference, Operations, Note), add minimum behavioral contract blocks next to the 11 bare "see source code for details" occurrences across 3 RAG doc files, and convert the 10 identified ASCII box-drawing diagrams to Mermaid with a retained plain-text description — all documentation-only, with no source code or EventBus implementation changes.

## Goal
Add a governance template document covering the six untemplated document classes (Governance, Guide, Specification, Reference, Operations, Note), add minimum behavioral contract blocks next to the 11 bare "see source code for details" occurrences across 3 RAG doc files, and convert the 10 identified ASCII box-drawing diagrams to Mermaid with a retained plain-text description — all documentation-only, with no source code or EventBus implementation changes.

## Scope
- Target files:
  - New: `docs/00_governance_11_document-templates.md`
  - Existing: `docs/00_governance_01_documentation-governance.md`
  - 3 RAG files with behavioral contracts (4+5+2 = 11 occurrences):
    - `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (4 occurrences)
    - `docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md` (5 occurrences)
    - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` (2 occurrences)
  - 10 diagram files to convert to Mermaid:
    - `docs/01_overview-arch-01-process.md`
    - `docs/01_overview-files-01-build.md`
    - `docs/01_overview-files-02-rag.md`
    - `docs/01_overview-files-03-scripts.md`
    - `docs/01_overview-files-04-shared.md`
    - `docs/01_overview-files-05-config.md`
    - `docs/01_overview-files-06-misc.md`
    - `docs/04_mcp_03_03_transport-and-health.md`
    - `docs/05_agent_02_runtime-architecture.md`
    - `docs/05_agent_03_01_turn-processing-flow-overview.md`

## Assumptions
- The requirement's suggested path `docs/00_governance_09_document-templates.md` is stale; the next free slot is `11` (`docs/00_governance_11_document-templates.md`)
- The glossary file `docs/00_governance_09_terminology-glossary.md` already exists; no new glossary needed
- 11 occurrences of "詳細はソースコードを参照してください" verified across 3 files
- All 10 diagram target files contain box-drawing characters (`┌└│├┐┘┤┬┴┼─`)
- No EventBus implementation changes (Global Rule 8)
- No source code changes (`scripts/`, `config/`)

## Design decisions
### 1. Template document (`docs/00_governance_11_document-templates.md`)
- Follow Front-Matter + section pattern of `00_governance_04_known-issues-template.md`
- 6 classes: Governance, Guide, Specification, Reference, Operations, Note
- Each class: Required Front Matter fields, Required sections, Optional sections, Evidence label applicability

### 2. Governance cross-links
- Update `docs/00_governance_01_documentation-governance.md`:
  - Add `[Document Templates](00_governance_11_document-templates.md)` to "Related Governance Documents"
  - Narrow/remove the "Document formatting conventions within Specification documents" Non-Goal line

### 3. Behavioral contracts (11 occurrences across 3 files)
- Each occurrence gets a fenced/quoted block with applicable fields:
  - Constants list: Responsibility + Needs Confirmation evidence note
  - Public methods: Responsibility, Input/Output contract, Side effects, Failure behavior, Idempotency (where relevant)
  - Do not restate full signatures; keep pointing to source

### 4. Diagram conversion (10 files)
- Convert ASCII box-drawing to ```mermaid flowchart TD``` (or `graph LR` for left-to-right)
- Keep a short plain-text description before/after
- Do not remove surrounding explanatory prose

## Implementation steps

### Phase 1 — Template and governance cross-link (independently committable)
1. Create `docs/00_governance_11_document-templates.md` with 6 class templates
2. Update `docs/00_governance_01_documentation-governance.md`:
   - Add `[Document Templates](00_governance_11_document-templates.md)` to "Related Governance Documents"
   - Narrow/remove the "Document formatting conventions within Specification documents" Non-Goal line

### Phase 2 — Behavioral contracts (independently committable per file)
1. `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`: add contract blocks at all 4 occurrences
2. `docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md`: add contract blocks at 5 occurrences
3. `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`: add contract blocks at both occurrences
3. Re-run `grep -c "詳細はソースコードを参照してください"` on the 3 files; confirm each remaining bare occurrence has an adjacent contract block

### Phase 3 — Diagram conversion (independently committable per file)
1. Convert each of the 10 files' ASCII diagram(s) to Mermaid, one file at a time
2. Keep a plain-text description before/after each diagram
3. After each file, re-run `grep -c '[┌└│├┐┘┤┬┴┼─]' <file>` to confirm no diagram-purpose box-drawing characters remain in fenced blocks

### Phase 4 — Verification and closeout
1. Manually preview every new ```mermaid block (GitHub PR preview or equivalent)
2. Confirm all links added between the new template document and `00_governance_01_documentation-governance.md` resolve
3. Spot-check one class's template against one real document
4. No deploy step required (documentation-only)

## Validation plan
- Cross-reference check: Manual link resolution (`ls` each referenced path)
- Behavioral contracts: `grep -c "詳細はソースコードを参照してください" <file>` — each remaining bare occurrence has adjacent contract block
- Diagram conversion: `grep -c '[┌└│├┐┘┤┬┴┼─]' <file>` — no box-drawing diagram remains in fenced block
- Mermaid render: Manual GitHub PR preview / Mermaid-compatible renderer — all render without syntax errors
- Repo-wide: `git diff --stat` — only `docs/*.md` files changed, no `scripts/`, `config/`, `tests/`

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-223022_require.md
- Source plan: plans/20260819-181551_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-151132
- Related target files: (see Affected areas list in plan)