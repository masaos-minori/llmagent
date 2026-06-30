## Goal
- Confirm FTS rebuild command naming is consistent across docs — no `fts-rebuild` (hyphenated) references, and `/db rag rebuild-fts` is the canonical form.

## Scope
- **In-Scope**:
  - Verify `scripts/agent/commands/cmd_db.py` dispatch key is `rebuild-fts`
  - Verify `/db rebuild-fts` alias documentation (removed at L277 of CLI docs)
  - Verify `docs/03_rag_05_configuration_and_operations.md` uses `/db rag rebuild-fts`
  - Verify no `fts-rebuild` notation in docs
- **Out-of-Scope**:
  - `/db` command architecture redesign
  - Unrelated DB maintenance command changes

## Findings

### 1. cmd_db.py dispatch key — Correct
- L65: `"rebuild-fts": self._db_rebuild_fts` — correct key
- L106: `["rag rebuild-fts", ...]` — full command name
- L152: `["rebuild-fts", ...]` — short form (within rag subcommand)

### 2. `/db rebuild-fts` alias — Correctly documented as removed
- L270-L284: `/db rebuild-fts` listed under "Removed flat alias commands" with replacement `/db rag rebuild-fts`

### 3. `docs/03_rag_05_configuration_and_operations.md` — Already uses canonical form
- L335: `/db rag rebuild-fts` ✓
- L353: `/db rag rebuild-fts` ✓
- L354: `/db rag rebuild-fts` ✓
- L358: `/db rag rebuild-fts` ✓

### 4. `fts-rebuild` notation — Only found in MCP tool names (not CLI commands)
- MCP tool name is `fts_rebuild` (underscore, not hyphen) — correct as MCP tool identifier
- No `fts-rebuild` or `fts.rebuild` CLI command references found

## Conclusion
No changes needed. The FTS rebuild command naming is consistent across all docs:
- Canonical form: `/db rag rebuild-fts`
- Removed alias: `/db rebuild-fts` (documented as removed at L277)
- No `fts-rebuild` or `fts.rebuild` CLI command references exist
