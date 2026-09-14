## Goal

Add a brief "why this separation exists" note (separation of concerns, testability) to `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s existing "Generating Freshness Data (Note on Responsibility Boundaries)" subsection — the calculation vs. decision role split and their contract are already fully documented there; only the design rationale is missing (REQ-001).

## Scope

- Add one short paragraph on the design rationale (separation of concerns, testability) to the end of the existing "Generating Freshness Data (Note on Responsibility Boundaries)" subsection (`docs/03_rag_02_02_ingestion_pipeline-crawler.md:74-88`)

## Assumptions

- The existing "Generating Freshness Data" subsection's role/contract descriptions (points 1-3 of the Issue's request) are accurate and current — confirmed by this cycle's direct code reading, not merely assumed from the document's own text
- No other documentation file duplicates this same "why" gap for the same calculation/decision split (this Plan's search was scoped to the Issue's cited file)

## Design decisions

1. Extend the existing subsection rather than create a new "Responsibility Boundary: Calculation vs Decision" section as the Issue's Recommended Action literally proposes — creating a second section covering largely the same ground as the existing one would fragment this topic across two locations, which is the opposite of what a "boundary clarity" fix should do
2. Keep the added rationale brief (one paragraph) — the existing subsection is already thorough on the "what"; the "why" is a short, self-contained addition that does not need its own extensive treatment

## Alternatives considered

1. Creating a new, separately-titled section titled "Responsibility Boundary: Calculation vs Decision" as the Issue's Recommended Action literally proposes — rejected because the existing, well-developed subsection already covers 3 of the Issue's 4 requested points in detail, and creating a duplicate section would fragment this topic across two locations
2. Modifying `crawl_file()`'s or `DocumentManager._is_file_unchanged()`'s implementation — rejected because this is a documentation-only change; no code changes are needed
3. Restating the existing role-split/contract content — rejected because it is already accurate and complete; only the missing rationale is added

## Implementation

### Target file

`docs/03_rag_02_02_ingestion_pipeline-crawler.md`

### Procedure

1. Confirm the existing subsection's accuracy
2. Append the design-rationale paragraph after line 88

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `crawl_persister.py:40-88` and `document_manager.py:114-124` to confirm the existing subsection's role/contract descriptions remain accurate before adding the rationale paragraph (REQ-001; `docs/03_rag_02_02_ingestion_pipeline-crawler.md`)

Phase 2: Core Logic — add the rationale paragraph
- Append the design-rationale paragraph after line 88 (REQ-001; `docs/03_rag_02_02_ingestion_pipeline-crawler.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_02_02_ingestion_pipeline-crawler.md:74-88` states "`crawl_file()` only calculates the mtime ... it does not perform any skip/decision logic"
- Existing code `scripts/rag/ingestion/crawl_persister.py:40-88` confirms `CrawlPersister.save()` computes mtime (lines 64-67) and SHA-256 (line 68) and always writes the payload unconditionally (line 83); no skip logic exists in this path
- Existing code `scripts/rag/ingestion/document_manager.py:114-124` confirms `_is_file_unchanged()` is the actual decision point: `existing_etag == new_etag` (SHA-256 comparison)

**Phase 2:** Append the following paragraph after line 88:

```markdown
This separation exists for two reasons: (1) **separation of concerns** — `crawl_file()` / `CrawlPersister.save()` handles I/O and metadata calculation (mtime, SHA-256), while `DocumentManager._is_file_unchanged()` handles business-logic decisions based on those values; (2) **testability** — each concern can be tested independently (calculation logic without a database, decision logic without file I/O), and the freshness-decision policy can evolve (e.g. changing the skip/re-ingest rule) without touching crawl-time file reading.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns.

## Security considerations

No security impact — documentation addition only. However, accurately documenting the responsibility boundary between crawl-time and ingestion-time components helps readers understand where to look when debugging freshness-related issues.

## Rollback considerations

Simple revert: remove the added paragraph. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_02_ingestion_pipeline-crawler.md | Manual — review added paragraph for consistency and non-duplication | Manual inspection | New paragraph adds rationale without restating existing content |

## Completion criteria

- [ ] The "Generating Freshness Data" subsection states the calculation/decision split exists for separation of concerns (I/O + metadata calculation vs. business-logic decision) (REQ-001)
- [ ] The subsection states the split enables independent testability of each concern (REQ-001)
- [ ] No existing content in the subsection (role descriptions, condition table, log messages) is altered (REQ-001)

## Out of scope

- Creating a new, separately-titled section (the Issue's Recommended Action proposes a section titled "Responsibility Boundary: Calculation vs Decision" — this Plan instead extends the existing, already well-developed subsection covering the same content, per Background)
- Changing `crawl_file()`'s or `DocumentManager._is_file_unchanged()`'s implementation
- Restating the existing role-split/contract content (already accurate and complete, per Background) — only the missing rationale is added

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm existing subsection's accuracy | Pending | — | — | |
| 2 | Phase 2: Append design-rationale paragraph | Pending | — | — | |
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
- **Source issue**: issues/20260913-183017_missing_webcrawler_responsibility_boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-210034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-073439
- **Related target files**: docs/03_rag_02_02_ingestion_pipeline-crawler.md
