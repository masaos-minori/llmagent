## Goal

Re-register the dedup store path from the shared `mcp_dedup.toml` to the ten per-server `[dedup]` tables (REQ-004).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Same-phase with seq 23; verified 2026-11-22: `DB_PATH_REGISTRATIONS` maps `("mcp_dedup.toml", "db_path")` (line ~127 area) and the reader block (lines ~224-229) parses the file.

## Design decisions
- Replace the single registration with the ten `("*_mcp_server.toml", "db_path")` entries (explicit per-file keys, not a glob, keeping the dict's exactness property); the reader tolerates a missing `[dedup]` table only where the separation check does not require it — after Phase 4 all ten must carry one and a missing table is a finding.

## Alternatives considered
- Registering one representative server file: rejected — the checker's purpose is per-file path hygiene; ten entries match the ten processes.

## Implementation
### Target file
`tools/check_db_separation.py`
### Procedure
1. Update `DB_PATH_REGISTRATIONS` (line ~17-26): drop the `mcp_dedup.toml` entry, add one entry per `config/*_mcp_server.toml` mapping `db_path` → the `mcp_dedup` database name.
2. Update the reader block (lines ~224-229) to iterate those files' `[dedup].db_path` values instead of the single file.
3. Update the module docstring mentions (lines 5, 14).
### Method
Mechanical registration change; check the tools/ size baseline before/after (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — baseline only shrinks).
### Details
- `tools/TOOL_DESCRIPTIONS.md` has no `mcp_dedup` entry (measured 2026-11-22): no description edit needed, but run the tools checkers per `rules/tool-gates.md`.

## Compatibility considerations
- The `*_db_path` regex already covers Agent-side db keys; only the bare `db_path` registrations change.

## Security considerations
- The separation check keeps catching a server `db_path` pointed at another database — same guarantee, finer registration.

## Rollback considerations
- N/A: revert the commit (checker is read-only over the repo).

## Validation plan
- `uv run python tools/check_db_separation.py` exit 0 against the post-Phase-4 tree; `uv run pytest tests/tools/test_check_db_separation.py -q` (seq 44); tools-scope checkers from `rules/tool-gates.md`.

## Completion criteria
- No `mcp_dedup.toml` registration remains; all ten server files are registered and the checker exits 0.

## Out of Scope
- Test file itself (seq 44); config contents (seqs 13-22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update registrations and reader | Pending | — | — | |
| 2 | Update docstring mentions | Pending | — | — | |
| 3 | Run the validation sequence and tools checkers | Pending | — | — | |

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
- **Requirement ID**: REQ-004; AC-003
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `tools/check_db_separation.py`
