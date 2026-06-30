## Goal
- Complete Canonical Source Rules table in `docs/03_rag_00_document-guide.md` by adding missing `03_rag_01_system_overview.md` entry for system-level documentation.

## Scope
- **In-Scope**:
  - Add `03_rag_01` row to Canonical Source Rules table in `docs/03_rag_00_document-guide.md`
  - Verify conflict resolution path references `03_rag_90`
  - Verify no active references to deleted legacy documents
- **Out-of-Scope**:
  - Legacy document restoration
  - New source mapping document creation
  - Changes to documents other than `03_rag_90`

## Findings

### 1. Canonical Source Rules table — Missing `03_rag_01`
Before: 4 rows (file formats, query pipeline behavior, config-ops, known bugs)
After: 5 rows — added "System purpose, ingestion and query pipeline overviews" → `03_rag_01_system_overview.md`

### 2. Conflict resolution path — Already correct
L65: conflict resolution references `03_rag_90_inconsistencies_and_known_issues.md` ✓

### 3. Legacy document references — No active references
- L13: Historical note about replaced files (not an active reference)
- L56: Documenting deleted legacy files (not an active reference)
- L89-L90: Listing deleted files (not an active reference)

## Conclusion
Added `03_rag_01_system_overview.md` to Canonical Source Rules table as the first row, completing the coverage of all RAG documentation files.
