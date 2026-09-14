## Goal

Append a new `#### NC-033` entry to `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 inventory, tracking why file extension unconditionally determines chunking strategy and what the historical reason for this distinction is, per that section's 15-field Entry Template. Per REQ-002.

Note: The Plan's Assumption #1 provisionally used `NC-034`, but adversarial verification confirmed the highest existing entry is `NC-032` (line 763) and neither this nor the companion plan has been implemented yet, so `NC-033` remains available.

## Scope

- Append exactly one new `#### NC-033` entry to `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 "Needs Confirmation Inventory"
- Populate all 15 template fields: Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking
- Model on the existing `#### NC-027` entry (same source file, different question) and this batch's own `NC-033` entry (added for Issue 183003 earlier in this batch, same "file-extension-based design decision has no documented rationale" shape)

## Assumptions

- The next available Needs Confirmation ID is `NC-033` (confirmed via `grep -oE '^#### NC-[0-9]+' ... | sort -n | tail` showing `NC-032` as the highest entry)
- The 15-field Entry Template format is stable and can be extended with a new entry following the same pattern
- The `Question` field should specifically address file-extension-based unconditional behavior, distinct from `NC-027`'s constant-value rationale; `Related NC` field should cite `NC-027` to make the distinction explicit rather than leaving readers to infer it

## Design decisions

- Use `NC-033` (not `NC-034` as the Plan's Assumption #1 suggested) since neither this nor the companion plan has been implemented yet
- Cite `NC-027` in the `Related NC` field to make the distinction between the two entries explicit
- Set `Status` to `open`, `Assigned To` to `Unassigned`, `Priority` to `Low`, `Blocking` to `No` — consistent with other NC entries in the same section
- Set `Resolution Target` to "Next ChunkSplitter specification review" — modeled on the `NC-027` precedent's `Resolution Target` pattern

## Alternatives considered

- Using `NC-034` instead of `NC-033`: rejected — the Plan's Assumption #1 was based on the assumption that another plan had already reserved `NC-033`, but neither plan has been implemented yet, so `NC-033` remains available
- Placing the entry elsewhere in the document: rejected — appending to Part 2 "Needs Confirmation Inventory" keeps it consistent with other NC entries

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. **Locate the insertion point** — after the last existing NC entry (`#### NC-032`)

2. **Insert the new NC entry** with all 15 template fields populated

### Method

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` around lines 763-780 (last NC entry)
2. Insert the new `#### NC-033` entry after the last entry
3. Verify all 15 template fields are populated correctly

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

**Step 2 — Insert the new NC entry:**

After edit, the new entry appears between NC-032 and the next section header:
```
#### NC-033

- **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: 3.1.3 Markdown Source Detection Behavior
- **Line Number**: ~113
- **Question**: Why does file extension unconditionally determine chunking strategy for `.md`/`.markdown`/`.mdx` URLs? What is the historical reason for this distinction?
- **Evidence**: No rationale exists in code comments, docstrings, or ADRs found during Step 3 inspection. `_is_markdown_source()` (lines 138-154 of `scripts/rag/ingestion/chunk_splitter.py`) implements the extension-first check but its docstring restates the behavior without explaining *why* — only that `.md`/`.markdown`/`.mdx` files always use heading chunking regardless of `md_index_enable`. Earliest traced commits (`ee035ff5e`/`c0b578e82`, "feat: Markdown ingest standardization — production code changes") contain no explanation.
- **Impact**: Operators cannot understand why files are chunked differently based on extension alone; new developers may not realize `md_index_enable` does not apply to `.md`-extension URLs
- **Required Action**: Owner confirmation of the historical reason for the extension-based rule; if resolved, update the chunksplitter documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: NC-027 (same source file, concerns undocumented Markdown-chunking rationale; NC-027 addresses `MIN_HEADING_LINES_FOR_MARKDOWN` constant value, NC-033 addresses file-extension-based unconditional behavior)
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

### Part 3: ...
```

## Compatibility considerations

- Documentation-only change: no production code affected
- If the 15-field Entry Template format changes in a future version of the governance document, this entry would need to be updated to match the new format (documented as a risk in the Plan)
- If a future Owner review resolves the open question tracked here, the entry's `Status` field should be updated to `resolved` and the `Question` field should include the resolution evidence

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Governance inventory consistency check | uv run python tools/check_needs_confirmation_inventory.py | No new errors/warnings attributable to the new NC entry |
| docs/00_governance_03_issue-and-uncertainty-management.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link or drift findings |

## Completion criteria

- [ ] New NC-033 entry appended after the last existing NC entry (NC-032)
- [ ] AC-3: All 15 template fields populated correctly:
  - Source File: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
  - Section: 3.1.3 Markdown Source Detection Behavior
  - Line Number: ~113
  - Question: Why does file extension unconditionally determine chunking strategy for `.md`/`.markdown`/`.mdx` URLs? What is the historical reason for this distinction?
  - Status: `open`
  - Assigned To: Unassigned
  - Priority: Low
  - Related NC: NC-027
  - Resolution Target: Next ChunkSplitter specification review
  - Blocking: No
- [ ] `uv run python tools/check_needs_confirmation_inventory.py` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/rag/ingestion/chunk_splitter.py` or any file that raises/catches ChunkFormatError
- Determining or documenting the actual rationale/historical reason for why `.md`/`.markdown`/`.mdx` URLs unconditionally use heading chunking — this is an Owner/design-review decision with no answer available anywhere in the repository
- Adding a subsection to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (covered by a separate implementation procedure)

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
- **Source issue**: issues/20260913-183038_missing_chunksplitter_markdown_source_detection_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-093116_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-122358
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
