## Goal

Correct the classification and ownership of `mcp_dedup.sqlite` in `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` so the doc states, consistently, that the dispatcher-owned dedup store is a **disposable derived cache** and never a *system of record*. This is the documentation half of `REQ-001` (the dispatcher owns `mcp_dedup.sqlite` as a disposable cache behind the dispatcher boundary).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The plan `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` is frozen; edits stay byte-scoped to the three locations below. No prose is rewritten outside them.
- `ADR-008` already classifies `mcp_dedup.sqlite` as a derived/disposable store; this doc must agree with that ADR, not redefine the four-database model.
- `ADR-004` seq 11 (this plan) registers the post-open write-failure exception separately; this doc's job is only the ownership/classification wording, not the fail-open policy text.
- The `pending_timeout_minutes` config reference is intentionally left untouched here (see Open items); a follow-up doc edit owns that change.

## Design decisions

- Reframe `mcp_dedup.sqlite` from "system of record" to "disposable dedup-log cache" in the `tool_call_state` ownership bullet, and make `workflow.sqlite` `tool_call_state` the explicit system of record. Two in-doc statements currently contradict each other; both are aligned to "disposable cache".
- Drop the citation to the archived producer-wiring issue `issues/20261031-175803_toolstate001_tool-call-state-producer.md` (adrrev008 settles the producer-ownership question; the issue is archived under `issues/done/` and its content survives there).

## Alternatives considered

- Keep the archived-issue citation with a parenthetical "settled by adrrev008": rejected; the plan explicitly drops it and the archived issue retains its full content elsewhere.
- Rewrite the whole `## The Standalone \`mcp_dedup.sqlite\` Store` section: rejected; out of scope, risks `stale_detector` line-citation drift, and the contradiction is confined to two spots.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (existing; not `(new)`)

### Procedure

1. **Ownership bullet (lines 97-100).** Replace the sentence "the dispatcher's `mcp_dedup.sqlite` store is a separate system of record behind the dispatcher boundary" with wording that names `workflow.sqlite` `tool_call_state` as the system of record and `mcp_dedup.sqlite` as a disposable dedup-log cache behind the dispatcher boundary. Remove the trailing clause that tracks the producer wiring on the archived follow-up issue; replace with one clause noting adrrev008 settled that question. Resulting bullet:

   `- Ownership: the agent executor path writes these rows through the `StateStore` facade (`scripts/agent/workflow/tool_call_state_ops.py`). `workflow.sqlite` `tool_call_state` is the system of record. The dispatcher's `mcp_dedup.sqlite` store is a disposable dedup-log cache behind the dispatcher boundary, not a system of record (adrrev008 settled the producer-ownership question the archived issue tracked).`

   Cited symbols exist today: `StateStore`, `scripts/agent/workflow/tool_call_state_ops.py`, `workflow.sqlite`, `tool_call_state`. No `(new)` symbols.

2. **Adoption-path wording (lines 147-148).** Change "recovery for this file is recreating it: the store is a `replay cache`" to "the store is a `disposable cache`". One-token change; keeps the surrounding "recreating it ... a fresh empty store only means the next call of each key runs for real" sentence intact.

3. **Stale cross-reference note (lines 150-151).** Delete the two-line Note block at lines 150-151 that states db_08 does not yet list the dedup store among the live database files and that no frozen procedure row owns that edit. It becomes false once seq 14 adds the store; removing it here avoids a dangling self-reference. Coordinate this removal with seq 14 (db_08), which runs immediately after and performs the complementary edit.

4. **Do NOT edit lines 72-76 or 108-110.** They still reference `dedup.pending_timeout_minutes` (10) as the agent-side stale-pending timeout source. adrrev008 moves that key to `agent.toml`; documenting that move is a follow-up doc task outside this frozen procedure. Flag it as an open item (below), not a silent expansion of scope.

### Method
Docs-only, single commit. Apply the three byte-scoped edits with the edit tool (exact-string match on the current lines), then run `tools/stale_detector.py` on the file. Any single mismatch aborts; fix before committing.

### Details

- All edits are in unguarded body/Context sections; `check_adr_preservation.py` does not apply (this is not an ADR file).
- After step 2 the doc uses "disposable cache" in both the ownership bullet and the adoption path, matching `ADR-008`'s derived-store language.
- Line numbers above are from the current committed HEAD (`78d6ec16c`); re-read the file if the working tree changed since.

## Compatibility considerations
N/A: documentation-only; no runtime, config, or schema impact.

## Security considerations
N/A: no change to access control, fail-open/fail-closed behavior, or data handling.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Run `uv run python tools/stale_detector.py docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`; expect zero findings (all cited symbols/files resolve).
- Grep the edited file: assert "system of record" no longer applies to `mcp_dedup.sqlite` (only to `workflow.sqlite` `tool_call_state`), assert "disposable cache" appears in both the ownership bullet and adoption path, and assert the `db_08 ... does not yet list` note is gone.
- Confirm no other doc references the dropped archived-issue id in a way this edit breaks (the id lives only in this doc among `docs/`; it persists in `issues/done/`).

## Completion criteria

- `mcp_dedup.sqlite` is described exactly once as a "system of record" — never; `workflow.sqlite` `tool_call_state` is the sole system of record.
- "disposable cache" (or "derived store") labels the dedup store in both the ownership bullet and the adoption path.
- The stale `db_08 does not yet list` note is removed.
- `stale_detector.py` reports no findings on the file.

## Out of Scope

- The `dedup.pending_timeout_minutes` config-source references at lines 72-76 and 108-110 (follow-up doc task; beyond this frozen scope).
- Any change to `ADR-008` itself (seq 10 owns that).
- Config or code changes to `mcp_dedup.sqlite` schema/lifecycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the three byte-scoped doc edits in Procedure | Pending | — | — | |
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
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Open items

- **`pending_timeout_minutes` config source (lines 72-76, 108-110).** These state `dedup.pending_timeout_minutes` (10) is the agent-side stale-pending timeout source. adrrev008 moves this key to `agent.toml`; the resulting config-source change belongs to a follow-up doc edit, not this frozen procedure. Do not edit here.
- **`db_08_active_databases.md` coordination.** This procedure removes the "not yet listed" note (step 3); seq 14 adds `mcp_dedup.sqlite` to `db_08`, making the removal correct. If seq 14 is deferred, restore the note before committing.
