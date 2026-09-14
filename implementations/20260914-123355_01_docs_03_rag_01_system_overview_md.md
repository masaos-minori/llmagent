## Goal

Append a new subsection to `docs/03_rag_01_system_overview.md` immediately after the "Constraints" table (after line 179, before the `---` at line 181), with one entry per constraint stating: what happens if violated, and whether enforcement is programmatic or assumed/operational — each backed by the specific code/ADR citation found in Background above. Per REQ-001.

## Scope

- Append exactly one new subsection into `docs/03_rag_01_system_overview.md`
  after line 179 (end of Constraints table) and before line 181 (`---`)
- Cover seven items requested in the Issue's Recommended Action:
  (1) Language Detection violation behavior and enforcement;
  (2) Chunk Size violation behavior and enforcement;
  (3) Chunk Overlap violation behavior and enforcement;
  (4) Embedding Dimension violation behavior and enforcement;
  (5) Crawl Depth/MAX Pages Per Site violation behavior and enforcement;
  (6) Database constraint violation behavior and enforcement;
  (7) No invented rationale for 5 unanswerable values
- Each item backed by the specific code/ADR citation found in Reference Files — no invented guidance beyond what the existing code pattern supports

## Assumptions

- The Issue's Evidence (quoting a "Constraint | Reason" table format with an "Embedding server must be available..." row) is stale — the current Constraints table (lines 163-173) has a different structure and content; this Plan documents the 7 constraints as they currently exist, per Step 2's adversarial verification finding
- `docs/03_rag_05_1-configuration-reference.md`'s existing documentation of chunk-size/overlap/crawl-depth/max-pages behavior (lines 26, 31, 35, 39, 48-50) is current and correct, and is cited rather than re-verified line-by-line beyond the spot-checks already performed for this Plan

## Design decisions

- Append the new subsection immediately after the Constraints table (line 179) and before the `---` separator (line 181)
- Quote or closely paraphrase each constraint's enforcement mechanism rather than summarizing loosely, minimizing near-term drift risk if source files are edited later
- Cite the specific file:line locations in Reference Files above
- Do NOT invent additional rationale beyond what the existing code/ADR evidence supports

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — appending after the Constraints table keeps it as a natural continuation of the constraint definitions rather than a disconnected addition
- Deriving new distinguishing rules for exception selection instead of citing docstrings: rejected — the Issue's Recommended Action asks for connecting existing accepted evidence, not inventing new claims

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. **Locate the insertion point** — between line 179 (end of Constraints table) and line 181 (`---`)

2. **Insert the new subsection** covering all seven acceptance criteria with explicit citations

### Method

1. Read `docs/03_rag_01_system_overview.md` around lines 179-181
2. Read reference files: `scripts/db/store_protocols.py` lines 38-47, `scripts/rag/ingestion/crawler_utils.py` lines 130-141, `scripts/rag/ingestion/chunk_splitter.py` lines 70-71/168-169/185-186, `scripts/rag/ingestion/crawler.py` lines 61/66
3. Insert the new subsection after line 179
4. Verify all seven acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 179-181:
```
| Database | SQLite single node only | Architecture |

---
```

**Step 2 — Insert the new subsection:**

After edit, lines 179-200:
```
| Database | SQLite single node only | Architecture |

### Constraint Violation Behavior and Enforcement

Each constraint below states what happens when violated and whether enforcement is programmatic or operational.

**Language Detection** — Enforced programmatically in `detect_lang()` (`crawler_utils.py` lines 130-141): text under 100 characters returns `None` (falls back to hint language); CJK ratio ≥ 0.10 triggers `ja`, otherwise `en`. No error is raised — the fallback path handles short-text edge cases gracefully.

**Chunk Size** — Enforced programmatically in `chunk_splitter.py`: sub-minimum chunks (< 40 chars) are discarded as noise (confirmed at lines 168-169: `if len(section) >= self._min_chunk`); over-maximum sections (> 500 chars) are split further via sentence-level chunking (line 174: `self._chunk_english(section)`). See `docs/03_rag_05_1-configuration-reference.md` line 39 for the discard-on-noise policy.

**Chunk Overlap** — A configured value applied programmatically via sliding-window logic in `merge_text_items()` (`chunk_splitter.py` lines 185-186). There is no "violation" concept — any config value is accepted and applied without validation.

**Embedding Dimension** — Strictly enforced programmatically via `validate_embedding_blob()` (`store_protocols.py` lines 38-47): raises `TypeError` if blob is not bytes, `ValueError` if blob length does not match expected dimensions. Changing the embedding model requires a corresponding code change (not a config change), since the dimension is a code-level constant defined in `get_embedding_dims()`.

**Crawl Depth / Max Pages Per Site** — Operational limits enforced by stopping BFS traversal at the limit. Neither constitutes a "violation" in the sense of an error — exceeding the limit simply ends the crawl for that site. Values are read from `config/crawler.toml` (`crawler.py` lines 61, 66).

**Database** — An architectural assumption per `ADR-008` (Assumptions section: "対象環境：単一Host、複数プロセス"; Rationale section: Operability/Performance/Data Integrity/Correctness, lines 91-101). Not per-request enforced code; reconsidering it requires the ADR's own "Reconsideration Conditions".

---
```

## Compatibility considerations

- Documentation-only change: no production code affected
- Restating enforcement mechanisms could drift from actual behavior if source files are edited later without a corresponding doc update (documented as a risk in the Plan)
- If a future code change adds validation for chunk overlap or other previously-unvalidated config values, this subsection's AC-3 guidance would become stale (documented as a risk in the Plan)

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md | No new structural/formatting findings |
| docs/03_rag_01_system_overview.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link or drift findings |

## Completion criteria

- [ ] New subsection appended after line 179 and before line 181
- [ ] AC-1: States Language Detection violation behavior — CJK-ratio check enforced programmatically in `detect_lang()`, text under 100 chars returns None (hint-language fallback)
- [ ] AC-2: States Chunk Size violation behavior — sub-minimum chunks discarded as noise, over-maximum sections split further, both enforced programmatically
- [ ] AC-3: States Chunk Overlap — no "violation" concept, any config value accepted and applied
- [ ] AC-4: States Embedding Dimension — strictly enforced programmatically via `validate_embedding_blob()`, raising TypeError/ValueError on mismatch; changing embedding model requires code change
- [ ] AC-5: States Crawl Depth/MAX Pages Per Site — operational limits enforced by stopping BFS traversal, not errors
- [ ] AC-6: States Database — architectural assumption per ADR-008, not per-request enforced code
- [ ] AC-7: No invented rationale for CJK ratio threshold, chunk size/overlap values, or crawl depth/max-pages values
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/db/store_protocols.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/crawler.py`, or any other source code
- Adding Needs Confirmation entries to `docs/00_governance_03_issue-and-uncertainty-management.md` (covered by a separate implementation procedure)
- Determining or documenting the actual rationale/historical reason for why the CJK ratio threshold is 0.10, why chunk size is 40/500 characters, why chunk overlap is 50 characters, or why crawl depth/max-pages operational values are 3/200

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation validated by tooling |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Source issue**: issues/20260913-183041_missing_system_overview_constraints_explanation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-094055_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-123355
- **Related target files**: docs/03_rag_01_system_overview.md
