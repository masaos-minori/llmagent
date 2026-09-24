# Missing operational guidance for rag-src/registered/ file lifecycle

## Priority
Low

## Summary
Define the retention period, deletion trigger, and deletion ownership for chunk files moved to `rag-src/registered/` after successful ingestion.

## Background
After successful ingestion, chunk files are **moved** (via `shutil.move()`) to `rag-src/registered/` by `FileRouter.route()` in `scripts/rag/ingestion/file_routing.py`. The File Lifecycle table in the ingestion pipeline overview documents creation but not deletion of these files. This creates uncertainty about how long files persist and who is responsible for cleanup. Note: `docs/03_rag_01_system_overview.md` line 47 already marks this area as `(retention TBD)`.

## Problem
No deletion logic exists in `scripts/rag/ingestion/ingester.py` or `file_routing.py`. The `rag-src/registered/` directory may grow unbounded over time, and files may be deleted ad hoc without traceability if this gap is not tracked. Additionally, there is no cron job or scheduled task for cleanup — the project has no automated maintenance mechanism for this directory.

## Reason for Change
Without defined lifecycle management, the `rag-src/registered/` directory becomes a source of disk space growth and operational confusion. A clear policy prevents both issues.

## Implementation Intent
1. Review the current `FileRouter.route()` behavior to understand what happens after a file is written to `rag-src/registered/`:
   - `self._registered_dir.mkdir(parents=True, exist_ok=True)` — lazy directory creation
   - `dest = self._registered_dir / path.name` — destination path construction
   - `shutil.move(str(path), str(dest))` — atomic file move (not copy)
   - `retry_dir` and `failed_dir` are also created by the same method
2. Determine whether files should be retained indefinitely, deleted after a fixed period, or cleaned up by a separate process.
3. Define the deletion trigger (e.g., periodic cron job, on-ingestion cleanup of older files) and ownership (which component/process is responsible).
4. Document the policy in the ingestion pipeline documentation and update the Known Issue entry.

## Target Files or Areas
- `scripts/rag/ingestion/file_routing.py` — `FileRouter.route()` method
- `scripts/rag/ingestion/ingester.py` — ingestion orchestrator
- `docs/03_rag_02_01_ingestion_pipeline-overview.md` — File Lifecycle section
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md` — ingester documentation
- `docs/03_rag_01_system_overview.md` — Component Responsibilities section (line 47: `(retention TBD)`)

## Required Changes
- Define the retention/deletion policy for `rag-src/registered/` files
- Designate a cleanup mechanism (cron job, periodic task, or operator intervention) — note: no existing cron infrastructure
- Update the File Lifecycle table in the ingestion pipeline overview to include deletion information
- Update `docs/03_rag_01_system_overview.md` line 47 to replace `(retention TBD)` with the defined policy
- Update the Known Issue entry RAG-006 status to reflect the resolution

## Constraints
- Deletion must not remove files that are still needed for re-ingestion or audit purposes
- The cleanup mechanism must handle concurrent ingestion safely
- No data loss for files that have not yet been fully processed
- Any cleanup implementation must work within the constraint that no cron infrastructure exists

## Acceptance Criteria
- A retention/deletion policy is documented for `rag-src/registered/` files
- The File Lifecycle table includes deletion information
- `docs/03_rag_01_system_overview.md` line 47 no longer contains `(retention TBD)`
- No unbounded growth of `rag-src/registered/` under normal operation

## Testing Expectations
- Manual verification: confirm the cleanup mechanism runs correctly under normal operation
- Regression test: confirm existing ingestion tests still pass after any cleanup implementation

## Documentation Impact
- The File Lifecycle table in `docs/03_rag_02_01_ingestion_pipeline-overview.md` must include deletion information
- The ingestion pipeline documentation must describe the cleanup mechanism
- `docs/03_rag_01_system_overview.md` line 47 must be updated to replace `(retention TBD)` with the defined policy
- The Known Issue entry RAG-006 must be updated to reflect the resolution status

## Out of Scope
- Changes to the FileRouter's routing logic itself
- Changes to the ingestion pipeline's core functionality
- Changes to the FTS indexing process
- Changes to the chunk storage format
- Implementing a cron infrastructure (out of scope; requires separate design decision)

## Dependencies
- NC-026 — unresolved; no corresponding `#### NC-026` heading exists in Part 2 and no removal-placeholder paragraph naming NC-026 was found during this Plan's systematic scan
- DESIGN-1 (resolved; shared-corpus note added to docs/03_rag_01_system_overview.md)

## Unresolved Questions
- What is the expected retention period for registered files? Depends on operational requirements (audit trail vs. disk space).
- Should the cleanup be automatic (periodic task) or manual (operator intervention)? Automatic is preferred but requires design decisions.
- Are there any compliance requirements that mandate retaining registered files indefinitely?
- Does the fact that files are MOVED (not copied) affect the retention policy? (If a file is moved, it no longer exists at the source — does this change the risk profile?)

## AI Implementation Instruction
- Do not implement any cleanup mechanism until the retention policy is defined
- Do not modify the FileRouter's routing logic unless the cleanup mechanism requires it
- Preserve the existing ingestion behavior until the policy is defined
- Report open questions about retention period before implementing cleanup
- If adding a cron job, ensure it is designed separately from this issue

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260924-054355
- **Related target files**: scripts/rag/ingestion/file_routing.py, scripts/rag/ingestion/ingester.py, docs/03_rag_02_01_ingestion_pipeline-overview.md, docs/03_rag_02_04_ingestion_pipeline-ingester.md, docs/03_rag_01_system_overview.md
