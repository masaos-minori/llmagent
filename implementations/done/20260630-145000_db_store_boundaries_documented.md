## Goal
- Document DB store public API boundaries across 3 doc files

## Findings
- `90_shared_05_db_api_and_operations.md` §1a: Basic import boundary table exists but missing extension workflow and anti-pattern warning
- `90_shared_04_db_architecture_and_schema.md` §2: Directory structure exists but missing import boundary note
- `90_shared_00_document-guide.md`: AI Query Routing Table missing DB store module boundaries entry

## Changes Made
1. Added "How to extend the DB store" 3-step workflow + anti-pattern warning to `docs/90_shared_05_db_api_and_operations.md:L25-L35`
2. Added "Import boundary" note to `docs/90_shared_04_db_architecture_and_schema.md:L40` referencing §1a
3. Added routing entry to AI Query Routing Table in `docs/90_shared_00_document-guide.md:L54`

## Conclusion
Code changes already complete. Documentation improvements applied across 3 files.
