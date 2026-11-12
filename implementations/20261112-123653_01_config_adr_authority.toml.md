## Goal
Add the `rag.fts-text-selection` and `eventbus.network-binding` decision targets, the ADR-006 to ADR-008 intentional `Reference` pair, and the ADR-014 edges the body supports, so the model matches the ADR front matter (`REQ-001`, `REQ-002`, `REQ-009` / `AC-1`, `AC-2`, `AC-9`).

## Scope
**Release unit**: authority-model

## Assumptions
- Current model (checked 2026-11-12): 14 `[[authority]]` targets (the Plan said 13; `security.posture-contract` was added since), ARCH-001 to ARCH-004, and an `ADR-008 -> ADR-006` Reference edge with no reverse edge; `ADR-012 -> ADR-007` already exists.
- UNK-01: ADR-006 is primary for `eventbus.network-binding` by evidence (INV-15 and its test live there); swapping primary and supplemental is a two-line change.
- UNK-02 resolved in Step 3a: ADR-014's body links itself to ADR-002, ADR-003, and ADR-004 (Security Posture sentence and the Agent-side posture row), so the model gets `ADR-014 -> ADR-003`, `ADR-014 -> ADR-002`, and `ADR-014 -> ADR-004` as `Reference` edges (ADR-003 is already a supplemental of `agent.component-responsibility`).
- Must be executed with the ADR front-matter rows 05, 07, and 09 (one release unit): a front-matter `related` entry without its edge fails `FRONTMATTER_DIVERGENCE`.
- Overlap judgments are in the Plan's Assumptions (compatible); edit only the region named here and locate it by text, not line number, because other Plans also edit this file.

## Design decisions
- New targets follow the existing `[[authority]]` shape with an explicit `limit` on each supplemental.
- The new bidirectional pair is flagged `intentional = true` with an ownership-split note, per ADR-016 INV-02.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`config/adr_authority.toml`

### Procedure
1. Run `uv run python tools/check_adr_authority.py` and `tests/tools/test_adr_authority.py` for a baseline.
2. Append the two `[[authority]]` targets after the existing targets.
3. Add the `ADR-006 -> ADR-008` Reference edge (intentional, with note) and the three `ADR-014` Reference edges.
4. Update the `six bidirectional pairs` comment to the count the regenerated section lists.

### Method
- `rag.fts-text-selection`: primary `ADR-009`; supplemental `{ adr = "ADR-005", limit = "FTS synchronization and rebuild operations only" }`.
- `eventbus.network-binding`: primary `ADR-006`; supplemental `{ adr = "ADR-013", limit = "authentication layered on top of the loopback binding" }`.
- Edge `ADR-006 -> ADR-008`, `edge_type = "Reference"`, `intentional = true`, note: ADR-008 owns the database separation; ADR-006 owns the event store use of it.
- Edges `ADR-014 -> ADR-002`, `ADR-014 -> ADR-003`, `ADR-014 -> ADR-004`, `edge_type = "Reference"` (not intentional: no reverse edge).

### Details
- Count after the change: the generated `Intentional Circular References` section lists five pairs today; with the new pair it lists six. Write the comment count from the regenerated list, not from this document.
- If an existing fixture in `tests/tools/test_adr_authority.py` breaks, stop and amend the Plan (`tools/amend_plan.py`, fallout class); do not edit the test here.

## Compatibility considerations
N/A: data file read by `tools/_adr_authority_core.py`; adding targets and edges cannot break a consumer unless a rule fails, which `check_adr_authority.py` reports.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_adr_authority.py -v`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/generate_adr_authority.py --check` (after row 02) — pass.

## Completion criteria
- Both targets have exactly one primary; the new pair is registered as intentional with a note; the ADR-014 edges exist; the authority and front-matter checks pass.

## Out of Scope
- Checker semantics; `.github/workflows/ci.yml` and `.pre-commit-config.yaml`; a separate assumption registry; ADR-010 edges.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two `[[authority]]` targets | Pending | — | — | |
| 2 | Add the ADR-006/ADR-008 intentional pair and the ADR-014 edges; update the pair-count comment | Pending | — | — | |
| 3 | Run `uv run pytest tests/tools/test_adr_authority.py -v`, `check_adr_authority.py`, and `check_adr_reference.py` (after rows 05, 07, 09) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` / `REQ-002` / `REQ-009` — register two decision targets; add ADR-006/ADR-008 pair and ADR-014 edges
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `config/adr_authority.toml`
