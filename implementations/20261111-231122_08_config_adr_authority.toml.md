## Goal

Register ADR-017 in the authority model: add a `mcp.authentication` decision target (primary ADR-017), narrow the ADR-007 supplemental limit under `mcp.technical-safety` (authentication moves out to ADR-017), and add typed ADR edges (`REQ-004`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `config/adr_authority.toml` is an index only; ADR bodies remain normative (per ADR-016).
- `mcp.technical-safety` currently lists ADR-007 as supplemental with limit "transport, authentication, and health-check responsibilities"; once ADR-017 owns authentication, that limit narrows to "transport and health-check responsibilities".
- The authority graph (non-Reference edges) must stay acyclic; Reference edges may form intentional bidirectional pairs flagged with `note`.

## Design decisions
- Add a new `[[authority]]` block `mcp.authentication` with `primary_adr = "ADR-017"` and no supplemental entries.
- Narrow the existing `mcp.technical-safety` ADR-007 supplemental `limit` string to drop "authentication" (now owned by ADR-017), preserving "transport and health-check responsibilities".
- Add typed ADR edges for ADR-017 (for example `ADR-012 -> ADR-017` and `ADR-007 <-> ADR-017` Reference pairs with `intentional = true` + `note`), keeping the graph acyclic.

## Alternatives considered
- Leaving ADR-007's limit unchanged: would still claim authority over authentication that ADR-017 now owns. Rejected: narrow the limit.

## Implementation
### Target file
`config/adr_authority.toml`

### Procedure
1. Add a `[[authority]]` block: `decision_target = "mcp.authentication"`, `primary_adr = "ADR-017"`, `supplemental_adrs = []`.
2. Edit the `mcp.technical-safety` block's ADR-007 supplemental `limit` from "transport, authentication, and health-check responsibilities" to "transport and health-check responsibilities".
3. Add `[[adr_edge]]` blocks for ADR-017 (Reference pairs flagged `intentional = true` with a `note`; one non-Reference edge if warranted), verifying the graph stays acyclic.
4. Run `uv run python tools/generate_adr_authority.py`, then `--check`.
5. Run `uv run python tools/check_adr_authority.py` and `uv run pytest tests/tools -q`.

### Method
- Insert the new `[[authority]]` block near the other `mcp.*` entries; insert `[[adr_edge]]` blocks in the typed-edge section.

### Details
- `check_adr_authority.py` is the CI `lint` gate; every change here must pass it. If the graph becomes cyclic or an unknown edge_type appears, adjust before committing.
- UNK-02 (the exact decision-target name and narrowed limit) is confirmed by `check_adr_authority.py` passing; the maintainer confirms the split at approval.

### Companion test files
N/A.

## Compatibility considerations
- `generate_adr_authority.py` renders the guarded sections of `adr_01_index.md` from this file (row 06); add both together.

## Security considerations
- Registers which ADR governs MCP authentication (ADR-017); no token values introduced.

## Rollback considerations
Revert the commit; the file is regenerated/validated by the tooling.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `adr_authority.toml` | Graph integrity | `uv run python tools/check_adr_authority.py` | Pass |
| Generated drift | `--check` | `uv run python tools/generate_adr_authority.py --check` | Pass |
| Authority unit tests | Unit | `uv run pytest tests/tools -q` | Pass |

## Completion criteria
- ADR-017 appears as the primary ADR for `mcp.authentication`, the ADR-007 supplemental limit under `mcp.technical-safety` no longer claims authentication, and `check_adr_authority.py` passes.

## Out of Scope
- Any authority target unrelated to MCP authentication.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `mcp.authentication` decision target (primary ADR-017) | Pending | — | — | |
| 2 | Narrow the ADR-007 supplemental limit and add typed ADR edges | Pending | — | — | |
| 3 | Run `generate_adr_authority.py`, `check_adr_authority.py`, `tests/tools` (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — ADR-017 registered in `config/adr_authority.toml`.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `config/adr_authority.toml`
