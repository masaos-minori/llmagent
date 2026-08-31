---
title: "ADR Index"
area: governance
tags:
  - governance
  - adr
related:
  - 00_governance_01_documentation-policy.md
  - 00_governance_04_documentation-checks.md
---

# ADR Index

## Purpose

Canonical list of all Architecture Decision Records (ADRs): current status,
dependency relationships, and invariant verification status. ADR status
definitions, ID format rules, and section header conventions are defined once in
`00_governance_01_documentation-policy.md` — not repeated here.

## ADR List

| ID | Title | Status | File |
|----|-------|--------|------|
| ADR-001 | Workflow Engine必須化 | Accepted | `adr/ADR-001-workflow-engine-mandatory.md` |
| ADR-002 | プロセス単位の設定所有権とConfig Isolation | Accepted | `adr/ADR-002-config-isolation.md` |
| ADR-003 | RuntimeToolRegistryを唯一のルーティング権威とする | Accepted | `adr/ADR-003-runtime-tool-registry-routing-authority.md` |
| ADR-004 | Production Failure-Handling Policy | Accepted | `adr/ADR-004-production-failure-handling-policy.md` |
| ADR-005 | RAGの正本と派生インデックスの関係 | Accepted | `adr/ADR-005-rag-source-derived-index-relationships.md` |
| ADR-006 | EventBusのSQLite永続化とSSE配信方式 | Accepted | `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` |
| ADR-007 | HTTP MCP採用とstdio非サポート | Accepted | `adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` |
| ADR-008 | SQLiteを4DBへ分離する | Accepted | `adr/ADR-008-sqlite-4db-separation.md` |
| ADR-009 | RAGのFTS5検索用テキストとLLM提示用テキスト分離 | Accepted | `adr/ADR-009-rag-ft5-text-separation.md` |
| ADR-010 | RAGの外部実行失敗時のインプロセスフォールバック | Accepted | `adr/ADR-010-rag-fallback.md` |
| ADR-012 | Git MCP Server-Side Write Enforcement | Accepted | `adr/ADR-012-git-mcp-server-side-write-enforcement.md` |

ADR-011（Database Corruption Recovery Safety Boundary）はADR-008へ統合され、削除された。
ADR-013（MCP Tool Availability Model）はADR-003へ統合され、削除された。

## ADR Dependency Graph

```text
ADR-001 → ADR-004 → ADR-008
ADR-002 → ADR-001, ADR-003, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010
ADR-003 → ADR-004, ADR-007
ADR-005 → ADR-008, ADR-009, ADR-010
ADR-006 → ADR-008
ADR-007 → ADR-004
ADR-009 → ADR-005
ADR-010 → ADR-004
```

### Circular Dependencies Detected

CDR-1: ADR-005 ↔ ADR-009 (bidirectional)
CDR-2: ADR-003 ↔ ADR-007 (bidirectional)

These violate the governance framework's prohibition on circular dependencies.
Resolve by restructuring related ADRs or documenting as known exceptions.

## ADR Invariant Verification Matrix

Documents how each ADR invariant is verified, where it runs, and what happens if it
fails. Critical invariants (INV-001–015) require automated verification; non-critical
invariants (INV-016–020) may rely on Manual Review or Operational Procedure.

| INV | ADR | Invariant | Type | Timing | Gate | Verification Status |
|-----|-----|-----------|------|--------|------|---------------------|
| INV-001 | ADR-001 | Workflow definition mandatory; missing workflow raises RuntimeError | Unit Test | CI | Blocking | Confirmed in code; no test yet |
| INV-002 | ADR-001 | Workflow schema consistent across versions | Integration Test | CI | Blocking | Not implemented |
| INV-003 | ADR-002 | Config isolation enforced between environments | Unit Test | CI | Blocking | Confirmed in code (`config_loader.py` `restrict_to()`); no test yet |
| INV-005 | ADR-003 | RuntimeToolRegistry is the sole routing authority | Unit Test | CI | Blocking | Confirmed in code (`resolve()` never falls back to ToolRegistry); no test yet |
| INV-006 | ADR-007 | No stdio transport usage | Unit Test | CI | Blocking | Confirmed (no stdio transport code exists); no test yet |
| INV-007 | ADR-005 | `chunks_vec` deleted before `documents` | Unit Test | CI | Blocking | Confirmed in code; no test yet |
| INV-008 | ADR-009 | `normalized_content` must not appear in LLM output | Unit Test | CI | Blocking | Confirmed (`_format_chunks()` uses `c.content`); no test yet |
| INV-009 | ADR-009 | FTS5 rebuild rules followed | Integration Test | CI | Blocking | Not verified |
| INV-010 | ADR-004 | Startup fails fast when a configured component's health check fails (Production is the sole supported mode) | Startup Validation | Startup | Deployment Blocking | Confirmed (`StartupOrchestrator._check_services()`, `scripts/agent/startup.py`); no test yet |
| INV-011 | ADR-004 | Safety-related startup checks (auth, allowlist, safety-tier, secrets, Config Isolation, approval-control establishment) fail fast; no fail-open path exists for these checks | Startup Validation | Startup | Deployment Blocking | Confirmed in code (`scripts/agent/startup.py`, ADR-004 Decision Details #2); no test yet |
| INV-012 | ADR-006 | EventBus offsets strictly monotonic | Unit Test | CI | Blocking | Confirmed (`offsets.py` `write_offset()`, `seq > current`); no test yet |
| INV-013 | ADR-006 | No success response before event persistence | Integration Test | CI | Blocking | Not verified |
| INV-014 | ADR-010 | No local fallback on normal empty RAG result | Integration Test | CI | Blocking | Confirmed (`remote_empty` → `HttpResultKind.EMPTY`); no test yet |
| INV-015 | ADR-010 | No local fallback on RAG 401/403 | Integration Test | CI | Blocking | **Potentially violated** — `http_augment.py` falls back on 4xx/parse errors (see Known Issue CI-003); no test yet |
| INV-016 | ADR-008 | SQLite 4DB separation maintained | Operational Procedure | Pre-deploy | Deployment Blocking | Confirmed (`DbTarget` enum); needs operational procedure |
| INV-018 | ADR-012 | Git MCP write operations enforced server-side | Unit/Integration Test | CI | Blocking | Confirmed (`tests/mcp_servers/git/`, 164 tests passing covering INV-01 through INV-04); one narrow gap remains (empty `branch` bypasses protected-branch check, see ADR-012 Known Deviations) |
| INV-019 | ADR-004 | Missing or invalid required configuration fails fast at startup | Startup Validation | Startup | Deployment Blocking | **Violated** — `load_config()` omits `strict=True` on `load_all()` (see Known Issue CI-005); no test yet |
| INV-020 | ADR-004 | Safety-related checks (e.g., permission checks) fail closed, independent of general availability-failure handling | Startup Validation | Startup | Deployment Blocking | **Unclear** — CI-006 was written against a now-removed local-mode distinction and needs re-investigation against the current Production-only model; no test yet |

**Note**: Most invariants have been verified via code inspection, but lack automated
test coverage. "Type" reflects the intended verification method, not whether a test
currently exists.

### Pipeline Mapping Summary

| Pipeline Stage | Invariants Covered |
|----------------|-------------------|
| CI (pull request) | INV-001 through INV-015, INV-018 |
| Startup validation | INV-010, INV-011, INV-019, INV-020 |
| Pre-deployment validation | INV-016 |
| Operations (runtime monitoring) | INV-018 |

## Related Documents

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

adr
architecture decision record
invariant
verification matrix
dependency graph
