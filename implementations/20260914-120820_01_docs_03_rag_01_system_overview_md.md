## Goal

Add an "Ownership Rationale" subsection to `docs/03_rag_01_system_overview.md`'s
"System Architecture" section explaining why each component owns its stated state, why
SQLite owns the vector store layer, how ownership affects modification rights, and the one
known exception already noted inline — grounded entirely in existing, already-accepted
evidence. Per REQ-001.

## Scope

- Insert exactly one new "### Ownership Rationale" subsection into
  `docs/03_rag_01_system_overview.md` after line 56 and before the `---` at line 58
- Cover four items requested in the Issue's Recommended Action:
  (1) why components own their stated state; (2) why SQLite owns the vector store layer;
  (3) how ownership affects modification rights; (4) the one known exception
- Each item backed by an existing, cited source — no new, uncited justification

## Assumptions

- ADR-005's Rationale section (Data Integrity, Operability, Portability) is the correct
  and sufficient existing justification for "why SQLite owns the vector store layer"
- The only ownership exception to document is the one already stated inline ("(retention TBD)"
  at line 47) — no other exception was found during Step 3 inspection
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Insert the new subsection immediately after the two existing Component Responsibility
  blocks (line 56) and before the `---` separator (line 58)
- Name/link the source for each of the four items (e.g., "per ADR-005's Rationale")
  rather than merely restating the reasoning in different words
- Cross-reference RAG-006 for the one known exception (note: RAG-006 was planned in a
  prior cycle of this batch but may not yet be committed to the governance doc)

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — inserting after the two
  Component Responsibility blocks keeps it as a natural continuation of the System
  Architecture discussion rather than a disconnected addition
- Deriving new rationale for SQLite's ownership instead of citing ADR-005: rejected —
  the Issue's Recommended Action asks for connecting existing accepted evidence, not
  inventing new claims

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. **Locate the insertion point** — between line 56 (end of second Component Responsibility
   block) and line 58 (the `---` separator)

2. **Insert the new subsection** covering all four acceptance criteria with explicit citations

### Method

1. Read `docs/03_rag_01_system_overview.md` around lines 44-58
2. Read `docs/adr/ADR-005-rag-source-derived-index-relationships.md` around lines 93-107
3. Insert the new subsection after line 56
4. Verify all four acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 56-58:
```
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

---
```

**Step 2 — Insert the new subsection:**

After edit, lines 56-80:
```
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

### Ownership Rationale

#### Why each component owns its stated state

Each pipeline stage runs as a separate script because failure isolation prevents one
stage's crash from affecting others; independent scaling allows write-heavy domains
(e.g., file-write-mcp) to require different resource allocation than read-only domains
(e.g., web-search-mcp); deployment independence allows individual scripts to be updated
or restarted without affecting the entire system (Reason for Process Separation). These
same principles apply to the Query Pipeline: the MCP server operates independently of
the agent lifecycle, and each stage can be updated or restarted without affecting the
entire system.

#### Why SQLite (rag.db) owns the vector store layer

Per ADR-005's Rationale, SQLite's `documents`/`chunks` tables are authoritative and
`chunks_fts`/`chunks_vec` are derived indexes for three reasons: (1) Data Integrity —
prioritizing data integrity over search performance ensures no orphaned records;
(2) Operability — prioritizing operability over real-time synchronization prevents
human operation errors; (3) Portability — the SQLite-based architecture enables
portable, self-contained deployments. These same considerations justify SQLite owning
the vector store layer specifically.

#### How ownership affects modification rights

Architecture decisions affecting multiple subsystems require joint review; cross-component
state transitions require coordinated testing when any component's contract changes
(Design Boundaries Requiring Joint Review). This means modifications to one component's
owned state must consider downstream impact on dependent components.

#### Known exception

The `rag-src/registered/` directory's retention policy is unresolved — "(retention TBD)"
as stated inline. See Known Issue `RAG-006` in `docs/00_governance_03_issue-and-uncertainty-management.md`.

---
```

Note: The cross-reference to RAG-006 assumes it has been added to the governance doc
in a prior cycle of this batch. If RAG-006 has not yet been added, the implementer
should verify whether the cross-reference resolves before committing.

## Compatibility considerations

- Documentation-only change: no production code affected
- Existing inline notes remain unchanged — they carry file/line-specific context that
  the consolidated table would otherwise have to duplicate
- Future edits to section 1.4's parameter table may drift from the new consolidated
  subsection if only one location is updated (documented as a risk in the Plan)
- The RAG-006 cross-reference could become stale if that Known Issue is later resolved
  and removed from the governance inventory (documented as a risk in the Plan)

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md | No new structural/formatting findings |
| docs/03_rag_01_system_overview.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link (ADR-005, RAG-006 references) or drift findings |

## Completion criteria

- [ ] New subsection inserted between line 56 and line 58
- [ ] AC-1: Explains why each component owns its stated state, citing existing
      "Reason for Process Separation" bullets (lines 49, 55)
- [ ] AC-2: Explains why SQLite owns the vector store layer, citing ADR-005's Rationale
      (Data Integrity, Operability, Portability) by name/link
- [ ] AC-3: Explains how ownership affects modification rights, citing existing
      "Design Boundaries Requiring Joint Review" bullets (lines 50, 56)
- [ ] AC-4: States the one known exception (`rag-src/registered/`'s "(retention TBD)",
      line 47) and cross-references Known Issue RAG-006
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Deciding the still-undecided retention policy for `rag-src/registered/`
- Modifying any source code
- Modifying `docs/adr/ADR-005-rag-source-derived-index-relationships.md` or any other ADR
- Inventing new ownership exceptions beyond the one already noted inline

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
- **Source issue**: issues/20260913-183035_missing_system_overview_component_responsibilities.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-092654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-120820
- **Related target files**: docs/03_rag_01_system_overview.md
