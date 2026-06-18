---
name: 20260618-150339_04_mcp_90_inconsistencies_and_known_issues.md
description: Add MISSING-01 entry to MCP inconsistencies doc to reflect current mdq-mcp state
metadata:
  type: implementation
---

# Goal

Add a `MISSING-01` entry to `docs/04_mcp_90_inconsistencies_and_known_issues.md` that accurately documents the resolved inconsistency: mdq-mcp was previously believed to be a stub but is actually FTS5-functional; the inconsistency is now between old documentation and actual code.

# Scope

- **File:** `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- **Change:** Append new `MISSING-01` section after the existing `SPEC-01` entry
- **Out of scope:** SPEC-01 entry, other inconsistency entries

# Assumptions

1. The current file has only `SPEC-01` (24 lines total) — no `MISSING-01` exists.
2. The entry format matches existing `SPEC-01` format: type, impact scope, description, current safe interpretation, recommended action.
3. The "missing" issue is: documentation claimed stub behavior, but code has real FTS5 implementation — the inconsistency is now a resolved doc-code mismatch.

# Implementation

## Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

## Procedure

1. Append a new `### MISSING-01` section at the end of the file.
2. Follow the same structure as `SPEC-01`.

## Method

Append to end of file.

New section:
```markdown
### MISSING-01: mdq-mcp documentation claimed stub behavior but FTS5 is functional

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `docs/04_mcp_04_server_catalog.md`, `scripts/mcp/mdq/tools.py`, `scripts/mcp/mdq/server.py`
- **Statement A:** Documentation (catalog) stated "All tools return stub strings. No actual data operations occur."
- **Statement B:** Code (`MdqService`) implements real FTS5 search/indexing using SQLite virtual tables (`sections_fts`).
- **Resolution:** Statement B is correct. The service layer is functional. Tools are marked `"status": "stub"` (metadata only) to signal the server is not production-validated, not that it is non-functional.
- **Current safe interpretation:** mdq-mcp performs real FTS5 search/indexing. It is experimental and not production-validated. Prefer `rag-pipeline-mcp` for production workloads.
- **Recommended action:** Completed — catalog updated to reflect FTS5 is functional; tool status set to `"stub"` as metadata signal.
```

## Details

- No code change in this step — documentation only.
- The entry is marked as "resolved" to close the inconsistency tracking.

# Validation plan

| Check | Command | Expected |
|---|---|---|
| Entry exists | `grep "MISSING-01" docs/04_mcp_90_inconsistencies_and_known_issues.md` | 1 match |
| Format consistent | manual review against SPEC-01 structure | matches |
