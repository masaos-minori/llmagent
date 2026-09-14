## Goal

Add a note after `docs/03_rag_01_system_overview.md`'s Constraints table stating that no rationale (empirical basis, trade-off analysis) for these specific values is recorded in code, config, or ADRs, and that tuning any of them should be verified empirically (search quality/performance testing) rather than assumed — without inventing a rationale or quality-impact analysis that does not exist (REQ-001).

## Scope

- Add one note after the Constraints table stating (1) no rationale for these specific values is recorded anywhere in the repository, and (2) tuning guidance requires empirical verification, which this documentation set does not currently provide

## Assumptions

- The `grep -rl` search across `docs/adr/` for each value's associated term found the complete set of ADR references, if any existed
- No config file comment or code docstring elsewhere in the repository (beyond the two files checked) records a rationale for these specific values — this Plan's search was scoped to the values' originating locations, not an exhaustive repository-wide sweep for every possible place a rationale could be recorded

## Design decisions

1. State the absence of rationale as a fact, not silence — this tells a future operator not to keep searching for design documentation that doesn't exist, and sets expectations that tuning needs its own verification
2. Recommend empirical verification rather than offer speculative quality-impact guidance — a wrong guess presented as documented guidance could lead an operator to make a tuning change with unintended quality regressions, which is worse than no guidance at all

## Alternatives considered

1. Fabricating a rationale, quality-impact analysis, or tuning guidance not backed by evidence — rejected because the Issue's Recommended Action requests exactly this kind of content — per user direction, this Plan states the gap rather than inventing content to fill it
2. Running actual experiments/benchmarks to establish real tuning guidance — rejected because it is a substantial, separate effort requiring benchmark infrastructure and quality-evaluation methodology, not a documentation-only fix
3. Writing new ADRs to retroactively justify these values — rejected because this would invent a rationale that does not exist in the repository's history

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Re-confirm no rationale exists
2. Add the note after the Constraints table

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-run `grep -rl` across `docs/adr/` for each constraint's associated term to reconfirm no ADR references them (REQ-001; `docs/03_rag_01_system_overview.md`)

Phase 2: Core Logic — add the note
- Add the note after the Constraints table (REQ-001; `docs/03_rag_01_system_overview.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_01_system_overview.md:163-174` contains the Constraints table:
  - Language Detection: CJK ratio ≥ 0.10 → `ja`; otherwise `en`; fallback to hint if < 100 chars
  - Chunk Size: Min 40 chars, Max 500 chars
  - Chunk Overlap: 50 character sliding window
  - Embedding Dimension: Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB
  - Crawl Depth: Operational value is 3 (max 3 hops from start URL, `config/crawler.toml`'s `max_depth`). Differs from code fallback; use operational config
  - Max Pages Per Site: Operational value is 200 (max 200 pages per site, `config/crawler.toml`'s `max_pages`). Code fallback is 500; use operational config
  - Database: SQLite single node only
- No ADR references any of the 6 constraint values (confirmed via `grep -rl` across `docs/adr/` for "CJK ratio", "chunk_overlap", "min_chunk", "max_chunk", "max_depth", "max_pages" — no match)
- The originating code itself carries no rationale comment: the CJK ratio threshold (`scripts/rag/ingestion/crawler_utils.py:26`, `_CJK_RATIO_THRESHOLD: float = 0.1`) has only a one-line description comment ("CJK character ratio threshold above which text is classified as Japanese"), not a justification for why `0.1` specifically; `config/chunk_splitter.toml`'s `min_chunk`/`max_chunk`/`chunk_overlap` values carry no comments at all beyond the file-level header

**Phase 2:** Append the following note after line 174 (after the Constraints table):

```markdown
Note: No empirical basis or trade-off analysis for these six constraint values is recorded in this repository's code, configuration files, or ADRs (as of this cycle's search). If these values are tuned, verify the change against actual retrieval quality/performance for your intended use case rather than assuming a known-good adjustment — this documentation set does not currently provide quality-impact guidance for any of them.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the absence of rationale for constraint values helps operators understand what tuning decisions require their own verification rather than relying on undocumented assumptions.

## Security considerations

No security impact — documentation addition only. However, accurately documenting the absence of rationale for constraint values helps operators avoid making tuning changes based on unverified assumptions about their impact on search quality.

## Rollback considerations

Simple revert: remove the added note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Manual — review added note for accuracy | Manual inspection | Note accurately states the absence of recorded rationale |

## Completion criteria

- [ ] The note states no empirical basis or trade-off rationale for the 6 Constraints table values is recorded in code, config, or ADRs (REQ-001)
- [ ] The note states any tuning of these values should be verified against actual retrieval quality/performance rather than assumed (REQ-001)
- [ ] The Constraints table itself is unmodified

## Out of scope

- Fabricating a rationale, quality-impact analysis, or tuning guidance not backed by evidence (the Issue's Recommended Action requests exactly this kind of content — per user direction, this Plan states the gap rather than inventing content to fill it)
- Running actual experiments/benchmarks to establish real tuning guidance (a substantial, separate effort requiring benchmark infrastructure and quality-evaluation methodology, not a documentation-only fix)
- Writing new ADRs to retroactively justify these values

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm no rationale exists | Pending | — | — | |
| 2 | Phase 2: Add note after Constraints table | Pending | — | — | |
| 3 | Verification: manual review | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183021_missing_system_overview_constraints_explanation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-211147_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-092407
- **Related target files**: docs/03_rag_01_system_overview.md
