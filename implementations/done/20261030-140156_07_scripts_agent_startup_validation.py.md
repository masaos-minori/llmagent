# Implementation Procedure: `scripts/agent/startup_validation.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-006, REQ-007)

## Goal
Route RAG findings by severity: fatal → `pipeline.add_fatal` (startup aborts per
ADR-004), degraded → `add_warning` with the repair action named, check failure/timeout →
identity-unverified warning (not fatal — fail-closed is enforced later at the gate).

## Scope
- RAG block `:160-188`: comment `# 6. RAG consistency` at `:160`, wait_for timeout 30s
  `:163-169`, blanket `add_warning` loop `:174-176`, `except TimeoutError` →
  `add_skipped` `:177-181`, `except Exception` → `add_skipped` with `# noqa: BLE001`
  `:182-188`.
- `_classify_rag_failure` `:31` — keep for failure categorization.
- `add_fatal` primitive already used in this file: routing_drift `:59`, readiness
  `:85`/`:99`, mcp_tool_discovery `:127` — no new pipeline primitive needed.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- Consistent case unchanged: `add_ok("rag_consistency")`.
- Inconsistent case: iterate `rag_check.findings`; any `FindingSeverity.FATAL` →
  `pipeline.add_fatal("rag_consistency", message_with_repair_action)`; otherwise
  `pipeline.add_warning("rag_consistency", ...)` per degraded finding with its
  `repair_action` in the message. If both classes appear, the fatal call dominates
  (pipeline aborts).
- Timeout/unexpected exception: replace `add_skipped` with
  `pipeline.add_warning("rag_consistency", "... identity-unverified ...")` — a warning
  that startup continues but the corpus is marked unverified; the gate (doc 08) refuses
  fallback while unverified (REQ-007). The `# noqa: BLE001` rationale comment is kept
  and updated to say the unverified state is enforced at the gate.
- No config path may downgrade a fatal finding (AC-4): severity comes only from code.
- `add_skipped("rag_consistency")` is no longer produced by this block.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Rewrite only the RAG block `:160-188` per the contract; touch nothing else in the
   file.
2. Remove the per-issue text-prefix filtering — findings carry severity structurally.

## Compatibility considerations
**Dependencies**:
- Upstream: docs 05/03/04 (severity-bearing findings), doc 06 (`consistency()` severity,
**Blocks**: docs 20, 21

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py`
  (docs 20/21).

## Completion criteria
- A fabricated duplicate `chunk_index` fixture aborts startup; a fabricated FTS gap only
  warns with `rebuild_fts` named; a 30s timeout yields an unverified warning and startup
  continues.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261031-073655 | 20261031-073655 | Phase 1: RAG findings routed by structural severity (FATAL aborts, DEGRADED warns with repair_action). SKIPPED removed per contract. Gates: ruff/mypy(482)/lint-imports(6/6)/ast-grep/bandit clean; tests/agent 3819, tests/db 372, MDQ-RAG boundary 5, diff-cover 100%. |
| 2 | Apply the Implementation procedure | Completed | 20261031-073655 | 20261031-073655 | Phase 1: RAG findings routed by structural severity (FATAL aborts, DEGRADED warns with repair_action). SKIPPED removed per contract. Gates: ruff/mypy(482)/lint-imports(6/6)/ast-grep/bandit clean; tests/agent 3819, tests/db 372, MDQ-RAG boundary 5, diff-cover 100%. |
| 3 | Run the Validation plan gates | Completed | 20261031-073655 | 20261031-073655 | Phase 1: RAG findings routed by structural severity (FATAL aborts, DEGRADED warns with repair_action). SKIPPED removed per contract. Gates: ruff/mypy(482)/lint-imports(6/6)/ast-grep/bandit clean; tests/agent 3819, tests/db 372, MDQ-RAG boundary 5, diff-cover 100%. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_05_scripts_db_models.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_06_scripts_agent_services_rag_maintenance_service.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No new named constructs (in-place block rewrite).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 07
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/agent/startup_validation.py`