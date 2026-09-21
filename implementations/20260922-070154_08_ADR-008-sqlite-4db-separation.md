## Goal

Repair or remove broken internal Markdown links in docs/adr/ADR-008-sqlite-4db-separation.md to restore navigational integrity.

## Scope

- Repair or remove 9 broken internal links identified by tools/check_docs_structure.py
- Preserve link anchor text where possible
- Do not modify external HTTP links

## Assumptions

- Broken links indicate either renamed/deleted documents or typos — not intentional cross-references
- Some documents may have been intentionally deleted; deletion intent should be confirmed before removing links
- The checker's link resolution logic is correct and does not need modification

## Design decisions

- For each broken link, check git history to determine if the target exists under a different name
- If found, update the link reference to point to the current filename
- If not found, remove the link and add a TODO comment noting the missing document
- Preserve link text (anchor text) where possible

## Alternatives considered

- Creating new documents to replace deleted ones — out of scope per Plan
- Renaming documents to match old link targets — out of scope per Plan
- Ignoring broken links — unacceptable per REQ-005

## Implementation

### Target file

docs/adr/ADR-008-sqlite-4db-separation.md

### Procedure

Repair or remove broken internal links in ADR-008.

### Method

For each broken link in the file:
1. Check if the target document exists under a different name via git history:
   ```bash
   git log --all --diff-filter=D -- "**/<filename>"
   ```
2. If the target was renamed/moved, update the link to point to the current location
3. If the target was deleted, remove the link and add a TODO comment
4. Preserve the original anchor text in the replacement

### Details

Broken links found in this file:

1. `[90_shared_04_02_db_architecture_and_schema-schema-reference.md](90_shared_04_02_db_architecture_and_schema-schema-reference.md)` — Check if this document exists under a different name
2. `[90_shared_05_04_db_api_and_operations-recovery-and-reference.md](90_shared_05_04_db_api_and_operations-recovery-and-reference.md)` — Check if this document exists under a different name
3. `[03_rag_04_02_rag-persistence.md](03_rag_04_02_rag-persistence.md)` — Check if this document exists under a different name
4. `[03_rag_04_03_rag-recovery.md](03_rag_04_03_rag-recovery.md)` — Check if this document exists under a different name
5. `[05_agent_04_01_agent-session-persistence.md](05_agent_04_01_agent-session-persistence.md)` — Check if this document exists under a different name
6. `[06_eventbus_03_persistence_schema_and_replay.md](06_eventbus_03_persistence_schema_and_replay.md)` — Check if this document exists under a different name
7. `[06_eventbus_04_dlq_offsets_and_delivery_semantics.md](06_eventbus_04_dlq_offsets_and_delivery_semantics.md)` — Check if this document exists under a different name
8. `[05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)` — Check if this document exists under a different name
9. `[00_governance_03_issue-and-uncertainty-management.md](00_governance_03_issue-and-uncertainty-management.md)` — Check if this document exists under a different name

For each link:
- Run `git log --all --diff-filter=D -- "**/90_shared_04_02_db_architecture_and_schema-schema-reference.md"` to check if it was moved/deleted
- If found under a new name, update the link: `[anchor text](new/path/to/file.md)`
- If deleted, remove the link entirely and add: `<!-- TODO: Document '90_shared_04_02_db_architecture_and_schema-schema-reference.md' was deleted -->`

## Compatibility considerations

- No code changes required — documentation-only task
- Link repairs must preserve the original anchor text to maintain readability
- Removed links should include TODO comments to preserve historical context

## Security considerations

N/A: Documentation-only change with no security impact

## Rollback considerations

- Revert link updates if they were incorrect (pointing to wrong documents)
- Restore removed links if the target document was found during rollback verification
- TODO comments added for deleted documents can be removed if the document is later recreated

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/adr/ADR-008-sqlite-4db-separation.md | Structural validation | `uv run python tools/check_docs_structure.py "docs/**/*.md"` | Zero broken link errors for this file |
| docs/adr/ADR-008-sqlite-4db-separation.md | Manual verification | Spot-check repaired links | Links resolve correctly |

## Completion criteria

- All 9 broken internal links are either repaired or removed with TODO comments
- `tools/check_docs_structure.py "docs/**/*.md"` reports zero broken links for this file
- Anchor text is preserved where possible
- No unintended changes to link text

## Out of scope

- Creating new documents to replace deleted ones
- Renaming documents to match old link targets
- Fixing broken links in code comments or other non-docs/ locations
- External HTTP link repair
- Link formatting improvements

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no new documentation created |

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20260922-064644_doc001_fix-broken-internal-links-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-065238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-070154
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
