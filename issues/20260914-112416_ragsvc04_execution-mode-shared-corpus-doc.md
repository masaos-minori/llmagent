# Document that external/local RAG execution modes share one corpus

## Priority
Medium

## Summary
`docs/00_governance_03_issue-and-uncertainty-management.md` `DESIGN-1` originally claimed external RAG (HTTP delegation) and local/in-process RAG use different corpora — this is not accurate under current configuration: both `config/rag_pipeline_mcp_server.toml` and `config/agent.toml` set `rag_db_path` to the same `/opt/llm/db/rag.sqlite`. This issue documents the corrected understanding: "external" vs. "local" RAG is an execution-mode distinction (HTTP delegation vs. in-process pipeline, per `ADR-010`), not a corpus difference, and adds an explicit note that both modes are expected to point at the same database.

## Background
`DESIGN-1`'s entry was corrected 2026-09-14 after verification found the two configs' `rag_db_path` values identical. `docs/adr/ADR-010-rag-fallback.md`'s Decision states `rag_service_url`'s presence/absence selects between HTTP delegation and in-process execution (INV-01) — this is an execution-mode switch, not a data-source switch. The ADR's own "Data Ownership and Persistence" section lists "`rag.sqlite`（ローカルRAG用）、外部RAGサービス（リモートRAG用）" as if they were two systems of record, which reads as supporting the original (incorrect) "different corpora" framing — this issue's documentation update should reconcile that ADR wording too, not just the system overview.

## Problem
`docs/03_rag_01_system_overview.md` has no note explaining that external and local RAG execution modes read the same corpus by configuration convention — a reader could reasonably infer from `ADR-010`'s current "Data Ownership and Persistence" wording that they are separate data sources, which does not match the actual configuration.

## Reason for Change
Per `DESIGN-1`'s corrected Impact: operators may not understand that "external"/"local" RAG is an execution-mode distinction over one shared corpus, risking incorrect assumptions about result consistency between modes (the opposite direction from the original concern, but still a real documentation gap).

## Implementation Intent
Add a short note to `docs/03_rag_01_system_overview.md` (or the most appropriate existing RAG architecture section) stating that external (HTTP) and local (in-process) RAG execution modes are both configured to read the same `rag_db_path` by convention, and that this is an operational convention rather than an architectural guarantee (i.e., a misconfigured `rag_pipeline_mcp_server.toml` pointing at a different `rag_db_path` would silently create a real corpus divergence, which the system does not currently detect). Also correct `ADR-010`'s "Data Ownership and Persistence" wording so it does not read as declaring two separate systems of record.

## Target Files or Areas
- `docs/03_rag_01_system_overview.md`
- `docs/adr/ADR-010-rag-fallback.md`
- `config/rag_pipeline_mcp_server.toml`
- `config/agent.toml`

## Required Changes
- Add a note to `docs/03_rag_01_system_overview.md` stating external/local RAG execution modes share one corpus by configuration convention (cite the `rag_db_path` keys in both config files as the current, verified evidence).
- State explicitly that this is a configuration convention, not an enforced invariant — a misconfigured `rag_db_path` divergence between the two config files is not currently detected by any automated check.
- Correct `ADR-010`'s "Data Ownership and Persistence" section so its "System of Record" line does not read as declaring `rag.sqlite` and "外部RAGサービス" as two separate corpora — restate it to reflect that both configs currently point at the same file.

## Constraints
Do not claim the shared-corpus configuration is architecturally enforced — it is currently only a configuration convention (both TOML files happen to agree). Overstating it as guaranteed would itself be a new inaccuracy.

## Acceptance Criteria
- `docs/03_rag_01_system_overview.md` states that external/local RAG execution modes currently share one corpus, citing the `rag_db_path` configuration keys as evidence, and notes this is a convention rather than an enforced invariant.
- `docs/adr/ADR-010-rag-fallback.md`'s "Data Ownership and Persistence" section no longer reads as declaring two separate systems of record for the same data.
- `DESIGN-1` is removed from the active Known Issues inventory once these doc updates are made.

## Testing Expectations
Not required — documentation-only change. Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and `tools/check_docs_consistency.py --domain rag` on the touched files to confirm no new findings.

## Documentation Impact
This issue's entire scope is the documentation update described above; update `DESIGN-1`'s governance entry to reflect resolution only after the doc updates are made.

## Out of Scope
- Adding an automated check that detects `rag_db_path` divergence between the two config files — that would be a separate, larger issue if pursued (this issue only documents the current convention and its lack of enforcement).
- Any change to `ADR-010`'s actual fallback Decision/Invariants — only the "Data Ownership and Persistence" wording is in scope.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the corpus-identity fact was directly verified from both config files during this issue's drafting.

## AI Implementation Instruction
Keep changes scoped to the documentation described above; do not add new enforcement code (e.g. a config-divergence check) as part of this issue — that is explicitly out of scope. Cite the two config files' `rag_db_path` values as the evidence for the shared-corpus claim, and state clearly that this is a convention, not a guarantee, per the Constraints above.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-112416
- **Related target files**: docs/03_rag_01_system_overview.md, docs/adr/ADR-010-rag-fallback.md, config/rag_pipeline_mcp_server.toml, config/agent.toml
