# Implementation Procedure: `docs/21_rag/rag_05_01-configuration-reference.md` (RAGCORPUS001 Phase 4)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-003, REQ-008)

## Goal
Document the new `rag_identity_mismatch_policy` key in the configuration reference.

## Scope
- `## config/agent.toml` section `:86-93` (`:90` describes what `AgentConfig.rag`
  carries; `:93` states `rag_query_service_url` is not an agent.toml key) (102 lines).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. In the `config/agent.toml` section, after `:93`, add a bullet documenting
   `rag_identity_mismatch_policy` (new): lives in the RAG config section of
   `config/agent.toml` (doc 14); accepted values `reject` (default) and `degraded`;
   `degraded` only by explicit operator approval (UNK-01 open — document the default,
   mark the approval requirement, do not present degraded as recommended).
2. State the semantics in one sentence: the key selects how the augment fallback
   identity gate labels a mismatch or unverifiable identity; it never changes the
   fallback trigger conditions (ADR-010 INV-12, doc 22).
3. Keep `:90` and `:93` statements intact — the new key does not change what
   `AgentConfig.rag` carries for search-stage parameters, and
   `rag_query_service_url` remains a non-agent.toml key. Docs-only change
   (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations
**Dependencies**:
- Upstream: doc 14 landed (`config/agent.toml` key name and accepted values are fixed
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain rag` passes after the update.

## Completion criteria
- AC-6 configuration side: the key, its accepted values, its default, and its
  label-only semantics are documented; checker green.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261031-173000 | 20261031-180000 |  |
| 2 | Apply the Implementation procedure | Completed | 20261031-173000 | 20261031-180000 |  |
| 3 | Run the Validation plan gates | Completed | 20261031-173000 | 20261031-180000 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_14_config_agent.toml.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `rag_identity_mismatch_policy` (config/agent.toml bullet) —
  same key name as doc 14; accepted values `reject`/`degraded`, default `reject`,
  fail-closed for any other value.

## Deviations from the approved procedure
None. The approved procedure's placement (the `config/agent.toml` section), accepted
values (`reject` default, `degraded`), and label-only semantics were all confirmed
against source: the key is a top-level `config/agent.toml` entry (consumed by the RAG
pipeline via `resolve_rag_config()` / `ConfigLoader().load_all()`, alongside `rag_db_path`),
and `_identity_gate()` treats any value other than `"degraded"` as fail-closed reject.
One pre-existing observation, not changed here (out of scope for this docs-only row):
the production comment on the `agent.toml` key reads `accept|degraded`, but the code
treats only `"degraded"` specially and rejects everything else — the word `accept` is
stale/misleading. Flagged for a follow-up config-comment fix, not edited in this batch.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-008
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 25
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `docs/21_rag/rag_05_01-configuration-reference.md`