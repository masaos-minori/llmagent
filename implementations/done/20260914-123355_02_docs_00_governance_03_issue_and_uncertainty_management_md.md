## Goal

Append 3 new Needs Confirmation entries to `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 inventory, tracking the undocumented rationale for the CJK ratio threshold (`0.10`), the chunk size/overlap values (`40`/`500`/`50`), and the crawl depth/max-pages operational values (`3`/`200`) — per that section's 15-field Entry Template. Per REQ-002.

Note: The Plan's Assumption #1 provisionally used `NC-035`-`NC-037`, but adversarial verification confirmed the highest existing entry is `NC-032` (line 763) and neither this nor the companion plans have been implemented yet, so `NC-033`, `NC-034`, `NC-035` remain available.

## Scope

- Append exactly 3 new `#### NC-033`, `#### NC-034`, `#### NC-035` entries to `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 "Needs Confirmation Inventory"
- Populate all 15 template fields for each entry: Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking
- Group 5 unrationale'd values into 3 NC entries by their config-file proximity:
  - NC-033: CJK ratio threshold (`crawler_utils.py`)
  - NC-034: Chunk size/overlap values (`chunk_splitter.py`/`config/chunk_splitter.toml`)
  - NC-035: Crawl depth/max-pages operational values (`config/crawler.toml`)

## Assumptions

- The next available Needs Confirmation IDs are `NC-033`, `NC-034`, `NC-035` (confirmed via `grep -oE '^#### NC-[0-9]+' ... | sort -n | tail` showing `NC-032` as the highest entry)
- The 15-field Entry Template format is stable and can be extended with new entries following the same pattern
- Each of the 3 entries' `Question` field names its config-file-proximate group explicitly (e.g. "chunk size AND overlap, both in `config/chunk_splitter.toml`"), keeping the grouping rationale visible rather than silently conflating unrelated values

## Design decisions

- Use `NC-033`, `NC-034`, `NC-035` (not `NC-035`-`NC-037` as the Plan's Assumption #1 suggested) since neither this nor the companion plans have been implemented yet
- Set `Status` to `open`, `Assigned To` to `Unassigned`, `Priority` to `Low`, `Blocking` to `No` — consistent with other NC entries in the same section
- Set `Resolution Target` to appropriate review type for each entry (language-detection logic review, ChunkSplitter specification review, crawler operations review)
- Do NOT invent an answer to any of the three `Question` fields

## Alternatives considered

- Using `NC-035`-`NC-037` instead of `NC-033`-`NC-035`: rejected — the Plan's Assumption #1 was based on the assumption that other plans had already reserved `NC-033` and `NC-034`, but neither plan has been implemented yet, so `NC-033`-`NC-035` remain available
- Placing the entries elsewhere in the document: rejected — appending to Part 2 "Needs Confirmation Inventory" keeps it consistent with other NC entries

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. **Locate the insertion point** — after the last existing NC entry (`#### NC-032`)

2. **Insert the 3 new NC entries** with all 15 template fields populated

### Method

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` around lines 763-780 (last NC entry)
2. Insert the 3 new `#### NC-033`, `#### NC-034`, `#### NC-035` entries after the last entry
3. Verify all 15 template fields are populated correctly for each entry

### Details

**Step 1 — Locate the insertion point:**

Current content around the last NC entry (NC-032):
```
#### NC-032

- **Source File**: `03_rag_05_4-error-handling-reference.md`
...
- **Blocking**: No

### Part 3: ...
```

**Step 2 — Insert the 3 new NC entries:**

After edit, the 3 new entries appear between NC-032 and the next section header:
```
#### NC-033

- **Source File**: `crawler_utils.py`
- **Section**: detect_lang() / _CJK_RATIO_THRESHOLD constant
- **Line Number**: ~26
- **Question**: Why is the CJK character ratio threshold set to 0.10? What is the historical reason for this specific value?
- **Evidence**: No rationale comment in `crawler_utils.py`; no ADR or governance entry found. `_CJK_RATIO_THRESHOLD = 0.1` (line 26) enforces the rule that text with ≥10% CJK characters is classified as Japanese, but no explanation exists for why 0.10 was chosen over any other threshold.
- **Impact**: Operators cannot understand why the language detection boundary is set at 10% CJK; new developers may not realize this threshold determines the ja/en classification boundary
- **Required Action**: Owner confirmation of the historical reason for the 0.10 threshold; if resolved, update the chunksplitter documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next language-detection logic review
- **Blocking**: No

#### NC-034

- **Source File**: `chunk_splitter.py` / `config/chunk_splitter.toml`
- **Section**: min_chunk / max_chunk / chunk_overlap constants
- **Line Number**: ~70-71, 168-169, 185-186
- **Question**: Why is the minimum chunk size 40 characters, maximum chunk size 500 characters, and overlap 50 characters? What is the historical reason for these specific values?
- **Evidence**: No rationale comment in `chunk_splitter.py` or `config/chunk_splitter.toml`; no ADR or governance entry found. `_min_chunk` (line 70), `_max_chunk` (line 71), and `_chunk_overlap` (line 74) enforce the constraint boundaries documented in `docs/03_rag_05_1-configuration-reference.md` line 39, but no explanation exists for why 40/500/50 were chosen over any other values.
- **Impact**: Operators cannot understand why sub-40-char chunks are discarded as noise, why sections exceeding 500 chars are split further, or why overlap is set to 50 characters
- **Required Action**: Owner confirmation of the historical reason for these specific values; if resolved, update the chunksplitter documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-035

- **Source File**: `crawler.py` / `config/crawler.toml`
- **Section**: max_depth / max_pages operational limits
- **Line Number**: ~61, 66
- **Question**: Why is the crawl depth limited to 3 hops from the start URL, and why is the maximum pages per site limited to 200? What is the historical reason for these specific operational values?
- **Evidence**: No rationale comment in `crawler.py` or `config/crawler.toml`; no ADR or governance entry found. `_max_depth` (line 61) and `_max_pages` (line 66) read from `config/crawler.toml` and stop BFS traversal at the limit, but no explanation exists for why 3 and 200 were chosen over any other values.
- **Impact**: Operators cannot understand why crawlers stop after 3 hops or 200 pages per site; new developers may not realize these are operational limits rather than technical constraints
- **Required Action**: Owner confirmation of the historical reason for these specific operational values; if resolved, update the crawler documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next crawler operations review
- **Blocking**: No

### Part 3: ...
```

## Compatibility considerations

- Documentation-only change: no production code affected
- If the 15-field Entry Template format changes in a future version of the governance document, these entries would need to be updated to match the new format (documented as a risk in the Plan)
- If a future Owner review resolves any of the open questions tracked here, the corresponding entry's `Status` field should be updated to `resolved` and the `Question` field should include the resolution evidence

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Governance inventory consistency check | uv run python tools/check_needs_confirmation_inventory.py | No new errors/warnings attributable to the 3 new NC entries |
| docs/00_governance_03_issue-and-uncertainty-management.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link or drift findings |

## Completion criteria

- [ ] 3 new NC entries appended after the last existing NC entry (NC-032)
- [ ] AC-8: All 15 template fields populated correctly for each entry:
  - NC-033: Source File `crawler_utils.py`, Section `detect_lang() / _CJK_RATIO_THRESHOLD constant`, Question about 0.10 threshold
  - NC-034: Source File `chunk_splitter.py` / `config/chunk_splitter.toml`, Section `min_chunk / max_chunk / chunk_overlap constants`, Question about 40/500/50 values
  - NC-035: Source File `crawler.py` / `config/crawler.toml`, Section `max_depth / max_pages operational limits`, Question about 3/200 values
  - Status: `open` for all three
  - Assigned To: Unassigned for all three
  - Priority: Low for all three
  - Resolution Target: Appropriate review type for each entry
  - Blocking: No for all three
- [ ] `uv run python tools/check_needs_confirmation_inventory.py` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/db/store_protocols.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/crawler.py`, or any other source code
- Determining or documenting the actual rationale/historical reason for why the CJK ratio threshold is 0.10, why chunk size is 40/500 characters, why chunk overlap is 50 characters, or why crawl depth/max-pages operational values are 3/200
- Adding a subsection to `docs/03_rag_01_system_overview.md` (covered by a separate implementation procedure)

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260913-183041_missing_system_overview_constraints_explanation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-094055_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-123355
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
