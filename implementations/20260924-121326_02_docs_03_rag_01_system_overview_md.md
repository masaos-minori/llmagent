# Implementation Procedure: Replace `(retention TBD)` Placeholder in System Overview

## Goal

Replace the `(retention TBD)` placeholder at line 47 in `docs/03_rag_01_system_overview.md` with the defined retention policy, per REQ-003.

## Scope

- Modify `docs/03_rag_01_system_overview.md`
- Replace `(retention TBD)` with the defined retention policy text

## Assumptions

- The placeholder exists at line 47 in the Owned State description
- The retention policy is: files are retained indefinitely for audit/debug purposes (per design rationale in the plan)
- The cleanup mechanism is out of scope for this phase (requires separate design decision)

## Design decisions

- Replace `(retention TBD)` with "Indefinite (audit trail); configurable retention planned"
- Keep the rest of the Owned State description unchanged
- Use Japanese headers consistent with the document style

## Alternatives considered

- **Remove the placeholder entirely**: Would lose important context about the unresolved retention question. Keeping it provides traceability.
- **Add a separate note**: Would fragment the Owned State description. Inline replacement keeps the context clear.

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Read the current Owned State description at line 47
2. Replace `(retention TBD)` with the defined retention policy text
3. Verify the replacement is correct

### Method

**Step 1: Locate the placeholder**

Current content at line 47:
```markdown
- **Owned State**: `crawler.py` owns crawled JSON artifacts; `chunk_splitter.py` owns chunked JSON artifacts; `rag-src/registered/` owns post-ingestion staging area (retention TBD).
```

**Step 2: Replace the placeholder**

Replace the above line with:
```markdown
- **Owned State**: `crawler.py` owns crawled JSON artifacts; `chunk_splitter.py` owns chunked JSON artifacts; `rag-src/registered/` owns post-ingestion staging area (Indefinite (audit trail); configurable retention planned).
```

### Details

- **REQ-003**: `docs/03_rag_01_system_overview.md` line 47 must no longer contain `(retention TBD)`
- **AC-003**: `docs/03_rag_01_system_overview.md` line 47 no longer contains `(retention TBD)`

## Compatibility considerations

- The update replaces a single phrase within an existing sentence — does not modify surrounding content
- Uses mixed English/Japanese consistent with the existing document style
- The new text preserves the parenthetical format of the original placeholder

## Security considerations

- No security impact — this is a documentation update only

## Rollback considerations

- To revert, restore the original line from git history

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| System overview doc | Manual: line 47 review | Read line 47 | `(retention TBD)` replaced |

## Completion criteria

- [ ] `docs/03_rag_01_system_overview.md` line 47 no longer contains `(retention TBD)`
- [ ] Replacement text documents the defined retention policy
- [ ] Existing Owned State description remains intact

## Out of scope

- Implementing a cron infrastructure for automated cleanup
- Changes to the FileRouter's routing logic
- Changes to the ingestion pipeline's core functionality
- Changes to the FTS indexing process
- Changes to the chunk storage format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260924-054355_rag006_missing-operational-guidance-rag-src-registered-file-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-080000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: docs/03_rag_01_system_overview.md
