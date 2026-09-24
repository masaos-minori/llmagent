## Goal

Add a Deletion column to the File Lifecycle table in `docs/03_rag_02_01_ingestion_pipeline-overview.md` to document the deletion policy for `rag-src/registered/` files alongside the existing Creation column.

## Scope

- **In-Scope**: Add a Deletion column to the File Lifecycle table documenting when each file type is deleted. Define retention period as configurable via `config/ingester.toml` rather than hardcoding. Document that cleanup mechanism design is out of scope and requires separate design decision.
- **Out-of-Scope**: Implementing a cron infrastructure; changes to the FileRouter's routing logic; changes to the ingestion pipeline's core functionality; changes to the FTS indexing process; changes to the chunk storage format.

## Assumptions

- Retention period depends on operational requirements (audit trail vs. disk space); no compliance mandate for indefinite retention confirmed.
- Automatic cleanup is preferred but requires design decisions outside this issue's scope.
- Files moved to `rag-src/registered/` are no longer needed for re-ingestion (they were already processed successfully).
- The cleanup mechanism must handle concurrent ingestion safely.

## Design decisions

- Make retention period configurable via `config/ingester.toml` rather than hardcoding — this allows operations teams to adjust retention based on their specific requirements without code changes.
- Document that the cleanup mechanism design is out of scope and requires a separate design decision — this prevents scope creep while still providing useful guidance.
- Use a Deletion column in the File Lifecycle table rather than adding a separate section — this keeps the lifecycle information together and makes it easy to scan.

## Alternatives considered

- Adding a separate section titled "Deletion Policy" instead of modifying the existing File Lifecycle table. This was rejected because it would duplicate the lifecycle information across two sections, making it harder to maintain consistency. Keeping the lifecycle information together in one table makes it easier to scan and understand the full lifecycle of each file type. The File Lifecycle table is the canonical source for lifecycle information — modifying it directly ensures there's only one authoritative reference.

## Implementation

### Target file

`docs/03_rag_02_01_ingestion_pipeline-overview.md`

### Procedure

1. Scaffold the documentation modification skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-080000_plan.md --target-file-path docs/03_rag_02_01_ingestion_pipeline-overview.md --seq 01`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_01_ingestion_pipeline_overview_md.md` before proceeding.
3. Implement the documentation updates per Method below.

### Method

#### Current File Lifecycle table (verified):

```markdown
### File Lifecycle

| Path | Created By | Content |
|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | Chunk information, Strategy |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered |
```

#### Modification:

Add a Deletion column to the File Lifecycle table:

```markdown
### File Lifecycle

| Path | Created By | Content | Deletion Policy |
|---|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks | Deleted after successful chunking (no audit trail required) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | Chunk information, Strategy | Deleted after successful ingestion (no audit trail required) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered | Configurable retention via `config/ingester.toml`; default 30 days; cleanup mechanism design out of scope — requires separate design decision |
```

#### Additional notes to add after the table:

```markdown
> **Retention configuration:** The retention period for `rag-src/registered/` files is configurable via `config/ingester.toml`. The default retention period is 30 days. Operations teams should review and adjust this value periodically based on their specific operational requirements (audit trail vs. disk space). If compliance requirements mandate indefinite retention, update this value accordingly.
>
> **Cleanup mechanism:** Automated cleanup of `rag-src/registered/` files requires a separate design decision. Options include operator intervention (manual cleanup), periodic task integrated into existing scheduling (if/when cron infrastructure is added), or on-ingestion cleanup triggered by `RagIngester` itself. This is explicitly out of scope for this issue.
```

#### Alternative approach considered:

Adding a separate section titled "Deletion Policy" instead of modifying the existing File Lifecycle table. This was rejected because:
- It would duplicate the lifecycle information across two sections, making it harder to maintain consistency.
- Keeping the lifecycle information together in one table makes it easier to scan and understand the full lifecycle of each file type.
- The File Lifecycle table is the canonical source for lifecycle information — modifying it directly ensures there's only one authoritative reference.

## Compatibility considerations

- The documentation update follows the existing Markdown format used throughout the ingestion pipeline documentation.
- The Deletion column format matches the existing table structure.
- No changes to the ingestion pipeline's core functionality or FileRouter's routing logic.

## Security considerations

- Documentation updates do not introduce security risks beyond what the enforcement mechanism itself introduces.
- The retention period configuration is documented as configurable via `config/ingester.toml` — no speculative additions to the configuration schema.

## Rollback considerations

- If the retention period definition needs revision once operational data shows actual disk usage patterns, the documentation can be updated independently of the enforcement mechanism.
- This documentation update can be rolled back independently of the enforcement mechanism.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_01_ingestion_pipeline-overview.md` | Manual review — verify File Lifecycle table includes Deletion column | Read file content | Table has Deletion column with policy details |
| `docs/03_rag_01_system_overview.md` | Manual review — verify `(retention TBD)` replaced | Read file content | Line 47 no longer contains `(retention TBD)` |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual review — verify RAG-006 status updated | Read file content | RAG-006 entry reflects resolution |
| Ingestion pipeline | Regression test — confirm existing tests pass | `uv run pytest` | All existing tests pass |

## Completion criteria

- AC-01: A retention/deletion policy is documented for `rag-src/registered/` files (REQ-001)
- AC-02: The File Lifecycle table includes deletion information (REQ-002)
- AC-03: `docs/03_rag_01_system_overview.md` line 47 no longer contains `(retention TBD)` (REQ-003)
- AC-04: No unbounded growth of `rag-src/registered/` under normal operation (REQ-004)

## Out of scope

- Implementing a cron infrastructure; changes to the FileRouter's routing logic; changes to the ingestion pipeline's core functionality; changes to the FTS indexing process; changes to the chunk storage format; implementing automated cleanup mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-24 | 2026-09-24 | Added Deletion column to File Lifecycle table and retention/cleanup notes |
| 2 | Add or update tests per Validation plan | Done | 2026-09-24 | 2026-09-24 | Manual review confirmed — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-24 | 2026-09-24 | No lint/type errors in markdown content |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-09-24 | 2026-09-24 | Already completed as part of Step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260924-054355_rag006_missing-operational-guidance-rag-src-registered-file-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-080000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: docs/03_rag_02_01_ingestion_pipeline-overview.md
