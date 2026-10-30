# Implementation Procedure: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (RAGCORPUS001 Phase 4)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005, REQ-006, REQ-008)

## Goal
Document the severity classes, the new fatal checks, and the changed startup
consequences and repair actions.

## Scope
- Startup Warnings section `:22-28`: "If an inconsistency is detected, a warning is
  printed" with the `fts_gap` example — the description this row replaces (83 lines).
- The session rag-rebuild-fts command section `:31+` — keep, and pair it with the other
  repair verbs.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Rewrite Startup Warnings (`:22-28`) as severity-routed behavior:
   - degraded findings (FTS gap, FTS orphan, vector count mismatch, orphan vector rows,
     chunks without vector rows, URL-level inconsistency, documents without chunks) →
     console warning per finding with its repair action; startup proceeds.
   - fatal findings (duplicate `chunk_index`, FK inconsistency, embedding-dimension
     mismatch, unknown schema, unverifiable corpus generation) → `rag_consistency`
     fatal and startup aborts with the repair action in the message.
   - failed or timed-out check → an identity-unverified warning, no longer a skipped
     record; fail-closed is enforced later at the augment gate.
2. Add a Severity Classes subsection: classification is fixed in code, not
   configuration; list the two classes with their finding sets (names exactly as docs
   03/04 define them).
3. Repair actions: map each degraded finding to `rebuild_fts`, `rebuild_vec`,
   `reconcile_url`, or the maintenance `recover` verb (doc 06); fatal findings take
   restore-from-backup or re-ingest guidance, not the rebuild commands.
4. Keep the `fts_gap` warning example; add one fatal-abort example line. Docs-only
   change (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 03, 04, 06, 07 landed (finding severities, fatal checks, repair verbs,
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain rag` passes after the update.

## Completion criteria
- AC-4/AC-5/AC-6 documentation side: operators can read which findings abort startup,
  which warn, and which repair action applies; checker green.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_03_scripts_db_rag_consistency.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: the five fatal finding names (duplicate `chunk_index`, FK
  inconsistency, embedding-dimension mismatch, unknown schema, unverifiable corpus
  generation) and `reconcile_url`, identity-unverified wording (Procedure section) —
  names introduced by docs 03/04/06/07.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006, REQ-008
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 24
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
