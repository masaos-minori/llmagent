# Remove history-style comments and notes

## Priority
Low

## Summary
Change history is written into current documents and configuration, which breaks the Current-Specification-Only policy.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-L01`; merged from ADRCHK-L12 (round 2 and round 5 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
History text remains in ADR-017 (a commit reference), ADR-010 (a rename note), governance_05 (a removal note), `config/agent.toml` NOTE blocks (removal dates), and the canonical registry (a replacement note). Claims come from the review (`Documentation only`).

The comment-cleanup part of the `agent.toml` reduction backlog (`memo-issue.md`, Issue 5) adds two confirmed items (`Explicit in code`, by `rg`): `config/agent.toml` carries a move note ("Moved from config/mcp_dedup.toml ...", line 28) and a search-result note ("grep for ... is empty", line 53), and `config/rag_pipeline_mcp_server.toml` carries a NOTE that names removed keys with a removal date and a re-add instruction (lines 24-30).

## Reason for Change
- The Current-Specification-Only policy and the `check_docs_quality` rules forbid history in active documents.
- History text makes readers think the old behavior still matters. Nothing makes the change time-sensitive.

## Implementation Intent
- Active documents and configuration describe only the current specification. History stays in git and in the plans.

## Target Files or Areas
- `docs/10_adr/adr_02_03_017_mcp-authentication.md`
- `docs/10_adr/adr_02_06_010_rag-fallback.md`
- `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
- `config/agent.toml`
- `config/rag_pipeline_mcp_server.toml`
- `config/documentation_canonical_sources.toml`

## Required Changes
- Remove or rewrite each history statement as a statement of the current specification.
- In both agent and RAG Pipeline MCP configuration files, delete removed-key names, removal dates, search results, past file names, and move history from comments; keep a short comment for each current field that states its purpose, unit, special values, security meaning, and restart requirement.

## Constraints
- If ADR-010 is withdrawn or moved by the governance issue, skip that file.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Keep every configuration value, including values equal to the code default: they are the explicit deployment contract.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- `uv run python tools/check_docs_quality.py` passes, and the files contain no removal or rename history.

## Testing Expectations
Run `tools/check_docs_quality.py`, `tools/check_compat_shims.py`, and the docs checkers; for `config/agent.toml` run `tools/generate_reference_table.py --check`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The listed documents and configuration comments.

## Out of Scope
- Behavior changes.
- Files outside the Target Files.

## Dependencies
- `issues/done/20261110-171040_rmcompat007_history-comment-sweep.md` covers overlapping text; re-verify against current source whether it already removed these statements before editing.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` may withdraw ADR-010 (skip that file if so).
- Related: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`, `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`, `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`, and `issues/20261120-114212_agentcfg004_config-ownership-split.md` edit `config/agent.toml`; there is no required order, and the later change re-runs the history searches.

## Unresolved Questions
- `不明`: the reduction backlog proposed moving needed history to migration notes, release notes, or ADR amendments. This issue keeps history in git and plans only; guidance for removed keys belongs in the migration table of `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`.
- The memo says to coordinate with `rmcompat007` under `issues/`; it is archived under `issues/done/`, so whether it already removed these statements is `不明`.

## AI Implementation Instruction
- Re-run the history searches first; skip any statement already gone and record the evidence.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123022
- **Related target files**: `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/10_adr/adr_02_06_010_rag-fallback.md`; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; `config/agent.toml`; `config/rag_pipeline_mcp_server.toml`; `config/documentation_canonical_sources.toml`
