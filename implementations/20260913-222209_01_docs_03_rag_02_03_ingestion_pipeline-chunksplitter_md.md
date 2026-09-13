## Goal

Remove the exact-duplicate "ChunkSplitter" section (`## 3a.`) from `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, and renumber the subsequent, non-duplicate "ChunkSplitter" continuation section (`## 3b.`) to restore a clean, sequential section numbering, per REQ-001 and REQ-002.

## Scope

- In-Scope: Deleting the duplicate `## 3a. ChunkSplitter` section (including its surrounding repeated nav-header block, `Related Documents`, and `Keywords` sub-sections) and renumbering the surviving `## 3b.` section to `## 3a.` for numbering continuity
- Out-of-Scope: Rewriting or correcting any content within the surviving sections (only the duplicate is removed; the Issue's own claim that the content is "identical" is accurate); restructuring the file's overall frontmatter/title ("ChunkSplitter Detail (Part 1)") or related/source fields; fixing any other documentation issue in this file not related to this duplication

## Assumptions

- No other document or code file references section `3a`/`3b` by heading number or anchor link (only whole-file references were found in this file's own related/source frontmatter, which is unaffected by an in-file heading renumbering)
- The Issue's Recommended Action's literal instruction ("retain only the first instance") is corrected by this Plan to "retain the first instance and the non-duplicate continuation" — the Issue's underlying intent (remove the accidental duplicate) is preserved; only the mechanical detail (a third, non-duplicate section exists and must survive) is corrected

## Design decisions

1. Renumber `3b` → `3a` (rather than leaving a `3`/`3b` gap, or renumbering to some other scheme) — this is the minimal change that restores sequential numbering without needing to renumber `3b`'s own internal sub-section numbers (`3.1.3`, `3.1.4`, `3.2`, ...), which remain valid as sub-numbers of the section now labeled `3a`
2. Delete the entire repeated nav-header block (the second "# RAG Ingestion Pipeline" + links + `---`) along with the duplicate section body, not just the `## 3a.` heading and its immediate content — leaving a stray, unlabeled nav block would itself be a documentation defect

Evidence grounding:
- `grep -n "^## "` confirms three-section structure: `## 3. ChunkSplitter` (line 32), `## 3a. ChunkSplitter` (line 107), `## 3b. ChunkSplitter` (line 182)
- `diff` between sections `3`/`3a` shows only heading-text differences (4 lines)
- `diff` between sections `3`/`3b` shows substantial content differences (212 lines), confirming `3b` is not a duplicate

## Alternatives considered

- **Leave `3b` as-is after deleting `3a`**: Rejected because it would leave a numbering gap (`3`, then `3b`, with no `3a`).
- **Renumber `3b` → `3c`**: Rejected because it doesn't restore sequential numbering and adds unnecessary complexity.
- **Delete both `3a` and `3b`**: Rejected because `3b` contains genuine continuation content (Markdown-heading chunking behavior, splitting-strategy details) that is not a duplicate of `3`.

## Implementation
### Target file
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Verify current state of overlapping sections
2. Confirm exact deletion boundaries
3. Delete the duplicate section
4. Rename the surviving section
5. Run validation sequence

### Method
Inline text deletion and heading rename within the existing documentation file.

### Details
1. **Phase 1: Preparation — Confirm exact deletion boundaries**
   a. Locate the three ChunkSplitter sections in `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`:
      - `## 3. ChunkSplitter` (lines 32-99)
      - `## 3a. ChunkSplitter` (lines 107-174) — byte-for-byte duplicate of section 3
      - `## 3b. ChunkSplitter` (lines 182-324) — genuine continuation, NOT a duplicate
   
   b. Re-confirm lines 100-174 are the complete extent of the duplicate nav-block + `3a` section + its `Related Documents`/`Keywords` sub-sections, with line 175 being the start of the next (`3b`) section's own nav block
   
   c. Verify the `diff` between sections `3`/`3a` shows only heading-text differences (4 lines)

2. **Phase 2: Core Logic — Delete and renumber**
   a. Delete lines 100-174 in their entirety:
      ```markdown
      <!-- Before: -->
      # RAG Ingestion Pipeline
      
      ## 3a. ChunkSplitter
      
      [duplicate content identical to section 3]
      
      ## Related Documents
      
      ## Keywords
      
      <!-- After: -->
      # RAG Ingestion Pipeline
      
      ## 3b. ChunkSplitter
      ```
   
   b. Rename the heading `## 3b. ChunkSplitter (...)` to `## 3a. ChunkSplitter (...)`:
      ```markdown
      <!-- Before: -->
      ## 3b. ChunkSplitter
      
      <!-- After: -->
      ## 3a. ChunkSplitter
      ```

3. **Phase 3: Verification**
   a. Run `rg -n "^## 3"` against the file and confirm exactly two ChunkSplitter headings remain (`3`, `3a`), with no duplicate content
   b. Manual diff review to verify no unintended changes to section 3 or the renamed section 3a

## Compatibility considerations

- A cross-reference elsewhere in the repository could link directly to the `3b` anchor (e.g. `#3b-chunksplitter`) and break after renumbering — mitigated by checking for external references before renaming; updating any found
- Deleting the wrong line range could accidentally remove part of section `3`'s or `3b`'s unique content — mitigated by Phase 1 explicitly re-confirming the exact boundary (line 175 = start of the next section) before Phase 2 executes the deletion

## Security considerations

N/A: Documentation update only, no security impact.

## Rollback considerations

Simple revert of the text deletion and heading rename — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual — diff review + heading count check | `rg -n "^## 3"` | Exactly 2 matches: `## 3.` and `## 3a.` |

## Completion criteria

- [ ] `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` contains exactly one "ChunkSplitter" section numbered `3` and one numbered `3a` (no `3b`, no duplicate `3a` content)
- [ ] The content of the (renumbered) `3a` section is unchanged from the current `3b` section's content except for the heading number
- [ ] No content from the current `3` section is altered
- [ ] All existing cross-references/links to this file remain valid (the file's own path and its related/source frontmatter fields are unchanged)

## Out of scope

- Modifying any source code files
- Modifying other documentation files beyond `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- Restructuring the file's overall frontmatter/title ("ChunkSplitter Detail (Part 1)") or related/source fields
- Fixing any other documentation issue in this file not related to this duplication

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm lines 100-174 are the complete extent of the duplicate nav-block + 3a section + its Related Documents/Keywords sub-sections | Pending | — | — | Record exact wording |
| 2 | Delete lines 100-174 in their entirety | Pending | — | — | Include repeated nav-header block |
| 3 | Rename ## 3b. ChunkSplitter to ## 3a. ChunkSplitter | Pending | — | — | Restore sequential numbering |
| 4 | Run rg -n "^## 3" and confirm exactly two ChunkSplitter headings remain | Pending | — | — | Verify no duplicate content |

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
- **Requirement ID**: REQ-001, REQ-002 — remove duplicate ChunkSplitter section and renumber surviving section
- **Source issue**: issues/20260913-183002_duplicate_section_headers_chunksplitter.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-202903_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-222209
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
