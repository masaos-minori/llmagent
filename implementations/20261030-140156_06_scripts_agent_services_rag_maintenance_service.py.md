# Implementation Procedure: `scripts/agent/services/rag_maintenance_service.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005, REQ-006, REQ-007)

## Goal
Expose severity and repair actions in `RagConsistencyResult`, and add the corpus-meta
ensure/read the startup and the fallback gate use.

## Scope
- `class RagMaintenanceService` `:21`; `consistency()` `:46-54` (returns
  `RagConsistencyResult` wrapping `check_rag_consistency` + `is_consistent`).
- Repair verbs named in messages by doc 03: `rebuild_fts` `:31`, `rebuild_vec` `:66`,
  `recover` `:56`, `reconcile_url` `:80`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `consistency()` keeps its signature; `RagConsistencyResult` carries the new
  `findings`, `fatal_count`, `degraded_count` fields straight from the report (the
  result type is a pass-through — if it is a thin re-export today, extend it in place;
  if it copies fields, add the new ones to the copy).
- `corpus_identity()` (new): method wrapping `rag.corpus_identity.ensure_corpus_meta`
  (doc 01) — returns `CorpusIdentity` (possibly `verified=False`); used by
  `scripts/agent/startup_validation.py` (doc 07) and `scripts/rag/pipeline.py` (doc 08)
  so neither opens the DB directly.
- Import policy: the module already lives at the `agent.services` layer; the import of
  `rag.corpus_identity` must respect the `skills/DESIGN.md` Shared Vocabulary layer
  contract — if a layer violation appears, route through the existing shared-db helper
  convention rather than restructure (record at implementation).

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Extend the result construction in `consistency()` `:46-54` with the severity fields.
2. Append `corpus_identity()` after `consistency()`; lazy-open via the existing helper
  pattern used by the other methods.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 05 (findings types), docs 03/04 (severity-bearing report), doc 01
**Blocks**: docs 07, 20

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/agent/test_startup.py` (doc 20) and `tests/db/test_rag_consistency.py`
  consumers.

## Completion criteria
- Startup and gate read severity/meta only through this service; no direct SQL appears
  in docs 07/08.

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
| `20261030-140156_01_scripts_rag_corpus_identity.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_03_scripts_db_rag_consistency.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_05_scripts_db_models.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `corpus_identity` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 06
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`
