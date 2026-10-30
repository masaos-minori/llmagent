# Implementation Procedure: `docs/21_rag/rag_01_system_overview.md` (RAGCORPUS001 Phase 4)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-008, AC-6)

## Goal
Replace the "undetected divergence" statement with the corpus-identity contract: what
is computed, where it is compared, and what happens on mismatch.

## Scope
- MCP responsibility-division section `:172-178` describes the `augment()` fallback
  chain in `scripts/rag/pipeline.py` (192 lines).
- Convention note `:180`: "configured with the same path by convention, not by an
  enforced invariant — a misconfigured ... pointing at a different `rag_db_path` would
  silently diverge, undetected by any current automated check" — the sentence this row
  replaces.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Rewrite the tail of the `:180` note: divergence is no longer undetected. Corpus
   identity is computed from the canonical corpus database plus the corpus-shaping
   config (doc 01); the `augment()` fallback path compares remote-side identity against
   the local identity before accepting a fallback (docs 08-11); a mismatch or
   unverifiable identity is handled per `rag_identity_mismatch_policy` (doc 14), reject
   by default.
2. In the same note, keep the two-config-file path arrangement as fact; only the
   "undetected ... by any current automated check" claim changes, and add that the
   startup consistency check reports fatal corpus corruption (docs 03/07).
3. In the `RagPipeline` bullet (`:176`), extend the fallback-chain phrase with "identity
   comparison before fallback acceptance".
4. Add `corpus identity` to the Keywords list. Docs-only change
   (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01, 08, 14 landed (identity computation, gate, policy key define the
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain rag` passes after the update.

## Completion criteria
- AC-6: the overview no longer claims divergence is undetected; it states the
  identity-comparison contract and the default reject behavior; checker green.

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

## Marker record
- `(new)` markers applied: `rag_identity_mismatch_policy` (Procedure section) — name
  introduced by doc 14.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008; AC-6
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 23
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `docs/21_rag/rag_01_system_overview.md`
