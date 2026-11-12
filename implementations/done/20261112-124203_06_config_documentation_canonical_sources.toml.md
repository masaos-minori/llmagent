## Goal
Register the posture-failure, empty-token, DLQ promotion threshold, and offset monotonicity decision targets in `config/documentation_canonical_sources.toml` with their normative ADR (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The registry holds 10 `[[canonical_sources]]` entries (verified 2026-11-12), none ADR-sourced; `check_canonical_source_registry.py` requires `Accepted` under `## Status` for every `source_paths` entry of an `architecture-decision` claim, and one source path for each non-exempt claim type (`SINGLE_SOURCE_EXEMPTIONS` covers only `runtime-behavior`) (verified). `ADR-004`, `ADR-006`, and `ADR-017` all read `## Status` → `Accepted`.
- UNK-04 (resolved 2026-11-12 by maintainer decision): the empty-token source is `ADR-017` (`docs/10_adr/adr_02_03_017_mcp-authentication.md`, Accepted). The earlier "ADR-017 does not exist yet, default to ADR-007" premise is stale — the adrrev011 procedures created it, and `config/adr_authority.toml` lists `mcp.authentication` → `ADR-017`. Registering in `config/documentation_canonical_sources.toml` mirrors, and does not replace, that authority entry (ADR-016).
- Targets mirror existing names where `config/adr_authority.toml` has them (for example `eventbus.persistence`); `mcp.empty-token-handling`, `agent.posture-failure-handling`, `eventbus.dlq-promotion-threshold`, and `eventbus.offset-monotonicity` are narrower sub-targets and are new in both registries.

## Design decisions
- Four entries, each `source_paths` one ADR file, `claim_type` from `VALID_CLAIM_TYPES` (`architecture-decision` for the decision text; do not invent a type).

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`config/documentation_canonical_sources.toml`

### Procedure
1. Append four `[[canonical_sources]]` entries.
2. Run `check_canonical_source_registry.py` and `check_canonical_source_conflicts.py`.

### Method
- `agent.posture-failure-handling` -> `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, area `Agent`.
- `mcp.empty-token-handling` -> `docs/10_adr/adr_02_03_017_mcp-authentication.md`, area `MCP`.
- `eventbus.dlq-promotion-threshold` and `eventbus.offset-monotonicity` -> `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, area `EventBus`.
- `claim_type = "architecture-decision"` for all four; add a `notes` line naming the ADR decision.

### Details
- If the registry check rejects two entries with the same source path, report it and fold the two EventBus entries into one target instead of changing the checker.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_canonical_source_registry.py`, `uv run python tools/check_canonical_source_conflicts.py` — pass.
- `uv run pytest tests/tools/test_check_canonical_source_registry.py -q` — pass.

## Completion criteria
- The four targets are registered with Accepted ADR sources and the registry checks pass.

## Out of Scope
- Editing the registry tools; mirroring into `config/adr_authority.toml`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the four entries | Completed | 20261112-215716 | 20261112-221114 | 4 entries appended with claim_type architecture-decision and notes naming the ADR decision; the two EventBus entries sharing one source path were accepted (no fold needed) |
| 2 | Run `uv run python tools/check_canonical_source_registry.py` and `check_canonical_source_conflicts.py` | Completed | 20261112-221114 | 20261112-221114 | check_canonical_source_registry.py: Registry validation passed; check_canonical_source_conflicts.py exit 0; 25 registry tests pass; full suite 12167 pass |

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
- **Requirement ID**: `REQ-005` — register four decision targets with their owning ADR
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `config/documentation_canonical_sources.toml`