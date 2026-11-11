## Goal

Register the `security.posture-contract` decision target in `config/adr_authority.toml` with ADR-004 as its primary authority, so the authority model has a registered owner for the posture contract, conforming to the ADR-016 schema.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The authority model is defined by ADR-016 (`docs/10_adr/adr_02_07_016_adr-authority-model.md`); this file is an index only, and ADR bodies remain normative.
- Existing `[[authority]]` rows use a dotted-namespace `decision_target` (for example `agent.tool-routing`, `mcp.transport`, `db.recovery-separation`) with exactly one `primary_adr` and optional supplemental_adrs list entries. `security.posture-contract` follows the same shape.
- ADR-004 currently appears only inside a `supplemental_adrs` list entry and is not yet the `primary_adr` of any decision target, so registering `security.posture-contract` under ADR-004 makes ADR-004 a primary authority for the first time.
- No `security.` / `posture` token currently exists in the file.
- Whether an owning `[[adr_edge]]` is required is an open design question resolved by reading ADR-016 and running `check_adr_authority.py`, not by inventing a shape.

## Design decisions
- Add a single `[[authority]]` row; do not introduce a new top-level table or key whose shape ADR-016 does not already define.
- Place the new row inside the authority-matrix section (before the `# --- Typed ADR edges ---` header), preserving the existing comment structure and ordering.
- Treat `check_adr_authority.py` as the arbiter of correctness; iterate on the edit until it reports clean.

## Alternatives considered
- N/A: single-row config addition; no design space worth recording.

## Implementation
### Target file
`config/adr_authority.toml`

### Procedure
1. Read `docs/10_adr/adr_02_07_016_adr-authority-model.md` (ADR-016) to confirm the exact `[[authority]]` schema and whether an owning `[[adr_edge]]` is expected for a newly registered primary.
2. Insert a new `[[authority]]` block in the authority-matrix section:
   ```toml
   [[authority]]
   decision_target = "security.posture-contract"
   primary_adr = "ADR-004"
   ```
   Add a supplemental_adrs entry only if ADR-016 or the checker indicates one is required.
3. Run `uv run python tools/check_adr_authority.py`.
4. If the checker flags a missing owning edge (or any finding tied to the new entry), add the minimal `[[adr_edge]]` that models the ownership and keeps the non-Reference edges acyclic; re-run the checker. If the checker is clean without an edge, leave the edges unchanged.
5. Do not modify any existing `[[authority]]`, `[[adr_edge]]`, or `[[assumption]]` row.

### Method
- Locate the authority-matrix section (between `version = "1"` and the `# --- Typed ADR edges ---` header).
- Append the new `[[authority]]` block after the last existing authority row.
- Match the existing TOML formatting (blank line between `[[authority]]` blocks).

### Details
- Current file has no `security.` / `posture` token; the nearest namespace analog is `mcp.transport` (primary ADR-007) and the `agent.*` governance namespaces.
- `check_adr_authority.py` must report no `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, or `ASSUMPTION_DRIFT`, and `security.posture-contract` must resolve to `primary_adr = "ADR-004"`.

## Compatibility considerations
- N/A: additive config entry; no existing entry changes. Confirm the authority graph stays acyclic if an edge is added.

## Security considerations
- Additive authority ownership only; no behavioral or cryptographic change. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Authority-schema consistency: `uv run python tools/check_adr_authority.py` — no `DUP_PRIMARY`/`DANGLING_ADR`/`AUTHORITY_CYCLE`/`ASSUMPTION_DRIFT`; `security.posture-contract` resolves to ADR-004.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` if any prose comment is added (English only).

## Completion criteria
- `security.posture-contract` is registered with `primary_adr = "ADR-004"` and `check_adr_authority.py` passes.
- No existing authority-matrix, edge, or assumption row changed.

## Out of Scope
- Changing any ADR body (covered by their own rows).
- Adding a distinct subprocess exit status or structured log line (code change out of scope).
- Re-classifying any server as non-required.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-100408 | 20261111-100408 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-100408 | 20261111-100408 | check_adr_authority.py OK no findings (security.posture-contract -> primary ADR-004, no edge needed); check_docs_japanese.py pass |

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
- **Requirement ID**: `REQ-005` — register `security.posture-contract` with primary ADR-004 in `config/adr_authority.toml`
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `config/adr_authority.toml`