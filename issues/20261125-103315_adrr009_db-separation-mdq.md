# Extend the database separation checker to mdq.sqlite

## Priority
Medium

## Summary
`tools/check_db_separation.py` registers five stores and omits `mdq.sqlite`, so ADR-008 INV-19 (six-store separation) stays Partial.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issue 016):
- Confirmed: the store table lists the platform stores plus `mcp_dedup` (`tools/check_db_separation.py:95`) and no `mdq` store; the only `mdq` entry maps `mdq_mcp_server.toml`'s `db_path` to the dedup store (`:136`). The checker currently reports "No violations found".
- Confirmed: the MDQ schema owner exists at `scripts/mcp_servers/mdq/db_schema.py` (tables `documents`, `chunks`, `chunks_fts`, `index_state`).
- ADR-008 states INV-19 is Partial until `mcp_dedup.sqlite` and `mdq.sqlite` are covered.

## Problem
Ownership, path uniqueness, ATTACH, schema-qualified access, and cross-store FK violations involving `mdq.sqlite` cannot be detected.

## Reason for Change
The ADR claims six-store separation; the checker enforces five.

## Implementation Intent
Register the MDQ tables and schema owner, extend the existing checks to the sixth store, add violation fixtures, and update ADR evidence only when all six stores are covered.

## Target Files or Areas
- `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`
- `scripts/mcp_servers/mdq/db_schema.py` (read-only), `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`

## Required Changes
- Register MDQ tables, canonical schema owner, and the MDQ path in the checker.
- Add MDQ checks for path uniqueness, ATTACH, schema-qualified access, and cross-store FKs.
- Add fixtures with intentional MDQ violations that fail.
- Update ADR-008 INV-19 evidence only after the six-store coverage passes.

## Constraints
- Existing five-store behavior must not change; the module-size gate for `tools/check_db_separation.py` must still pass (check `wc -c` before editing).

## Acceptance Criteria
- All six stores are checked; intentional MDQ violations fail; INV-19 moves from Partial only with complete evidence.

## Testing Expectations
MDQ ownership, duplicate-path, cross-store access, schema-qualified access, and ATTACH-negative tests; `uv run python tools/check_db_separation.py` on the repository; the tool gates for changed files.

## Documentation Impact
ADR-008 INV-19 evidence and the `tools/TOOL_DESCRIPTIONS.md` row if the tool's behavior description changes.

## Out of Scope
- Changing MDQ schema or database location.

## Dependencies
- N/A: none (no open issue overlaps; `mdqmcp004` concerns file identity, not store separation).

## Unresolved Questions
- `不明`: the path of `mdq.sqlite` per server configuration (to be read from `config/mdq_mcp_server.toml` during implementation).

## AI Implementation Instruction
Extend, do not restructure, the checker; report any real MDQ violation the new check finds instead of fixing it in this issue.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103315
- **Related target files**: `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`, `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`
