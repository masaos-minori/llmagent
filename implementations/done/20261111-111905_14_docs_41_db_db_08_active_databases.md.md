## Goal

Add `mcp_dedup.sqlite` to `docs/41_db/db_08_active_databases.md` as an inventory section that classifies it as a **disposable derived cache** owned by the dispatcher, consistent with `ADR-008`'s derived-store model and with the corrected wording in `db_03_07` (seq 13). This documents `REQ-001` (the dispatcher owns `mcp_dedup.sqlite` as a disposable cache behind the dispatcher boundary).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The plan `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` is frozen; edits stay byte-scoped to the two locations below.
- `db_03_07` (seq 13) removes its "db_08 does not yet list the store" note in the same change set; this section makes that note false-correct. Coordinate ordering: seq 13 then seq 14.
- `db_08` is a regular design doc, not an ADR: `check_adr_preservation.py` does not apply. Only `stale_detector.py` governs cited symbols/lines.
- Schema authority is `scripts/shared/mcp_dedup.py`: `_SCHEMA` (`CREATE TABLE IF NOT EXISTS tool_call_state`) is executed by `DedupStore.__init__` (verified at `scripts/shared/mcp_dedup.py:240`).

## Design decisions

- Model the new section on the existing `## mdq.sqlite` section (owner / config source / schema authority / lifecycle / rebuild), since mdq is the one other dispatcher-adjacent derived store already documented here.
- Classify under "Rebuild" as a disposable derived store rebuildable from live dispatch decisions, with recovery = recreation per `ADR-008`. Do NOT claim it is rebuildable from another SQLite database (unlike mdq's Markdown sources): its data is dispatch decisions, whose system of record is `workflow.sqlite`.

## Alternatives considered

- Place the section after `eventbus.sqlite` (before `mdq.sqlite`): rejected; the plan directs placement immediately before `## Related ADRs`, and grouping the newest store last matches the doc's chronological add pattern.
- Add `mcp_dedup.sqlite` to the four-database narrative in `ADR-008` here too: rejected; `ADR-008` is seq 10 and is byte-guarded.

## Implementation
### Target file
`docs/41_db/db_08_active_databases.md` (existing; not `(new)`)

### Procedure

1. **Add a `## mcp_dedup.sqlite` section immediately before `## Related ADRs`.** Insert the following block between the end of the `## mdq.sqlite` section and the `## Related ADRs` heading (current lines 63-65). Modeled on `mdq.sqlite`:

   ```markdown
   ## mcp_dedup.sqlite

   - **Owner**: the shared MCP dispatcher (`scripts/mcp_servers/dispatch.py`)
   - **Config source**: `db_path` in `config/mcp_dedup.toml` only; `agent.toml` carries no dedup path
   - **Schema authority**: `scripts/shared/mcp_dedup.py` (`_SCHEMA`, `CREATE TABLE IF NOT EXISTS tool_call_state`); `DedupStore.__init__` executes it on first use
   - **Lifecycle**: Created on first dispatch use via `open_dedup_store`; persists until deleted
   - **Rebuild**: disposable derived store, rebuildable from live dispatch decisions; backup and rotation helpers do not cover it. Recovery is recreation per ADR-004. See [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) (Derived Stores Outside the Four Domains)
   ```

   All cited symbols resolve today: `scripts/mcp_servers/dispatch.py`, `config/mcp_dedup.toml`, `scripts/shared/mcp_dedup.py`, `DedupStore`, `open_dedup_store`, `ADR-008`. No `(new)` symbols.

2. **Add the keyword.** In `## Keywords`, add `- mcp_dedup.sqlite` after `- mdq.sqlite` and before `- WAL` (current lines 76-77), keeping the database-name grouping together.

3. **Do not touch** `## Related ADRs`, the front matter, or any other section.

### Method
Docs-only, single commit. Apply both edits with the edit tool (exact-string match on current lines), then run `tools/stale_detector.py` on the file. Any single mismatch aborts; fix before committing.

### Details

- Line numbers are from the current committed HEAD; re-read the file if the working tree changed since.
- The "Rebuild" bullet mirrors `mdq.sqlite`'s structure so readers see the parallel disposable-store treatment at a glance.

## Compatibility considerations
N/A: documentation-only; no runtime, config, or schema impact.

## Security considerations
N/A: no change to access control, fail-open/fail-closed behavior, or data handling.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Run `uv run python tools/stale_detector.py docs/41_db/db_08_active_databases.md`; expect zero findings.
- Grep the edited file: assert a `## mcp_dedup.sqlite` section exists, that it never calls the store a "system of record", and that `mcp_dedup.sqlite` appears in `## Keywords`.
- Confirm the section sits before `## Related ADRs` and the keyword sits before `WAL`.

## Completion criteria

- `mcp_dedup.sqlite` is inventoried as a dispatcher-owned disposable derived store with a rebuild/recovery note referencing `ADR-008`.
- It appears in `## Keywords`.
- `stale_detector.py` reports no findings on the file.

## Out of Scope

- Any `ADR-008` change (seq 10 owns that).
- The `pending_timeout_minutes` config-source move to `agent.toml` (follow-up doc task; beyond this frozen scope).
- Config or code changes to `mcp_dedup.sqlite` schema/lifecycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `mcp_dedup.sqlite` section and keyword per Procedure | Pending | — | — | |
| 2 | Run `stale_detector.py` on the edited file | Pending | — | — | docs-only row; no test-add step |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — dispatcher owns `mcp_dedup.sqlite` as a disposable cache behind the dispatcher boundary
- **Source issue**: `issues/done/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `docs/41_db/db_08_active_databases.md`

### Open items

- **`pending_timeout_minutes` config source.** `db_08` lists config sources per database; once adrrev008 moves `dedup.pending_timeout_minutes` to `agent.toml`, the config-source line for other stores may need a follow-up pass. Out of scope for this frozen procedure.
- **`db_03_07` coordination.** seq 13 removes its "not yet listed" note; this section makes that removal correct. If seq 13 is deferred, this section still stands on its own.
