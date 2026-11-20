## Goal

- Extend ARCH-002's asserted config keys to cover the EventBus host and restate its code-guard half (ungated), and — only after maintainer approval — land the reversed edge, the two target registrations, and the three new `Reference` edges in the authority model.

## Scope
**Release unit**: model-regen

- REQ-007 (ARCH-002 `config_keys`/`current_value` update) — ungated, lands with Phase 1.
- REQ-021 (edge reversal), REQ-022 (`platform.config-isolation`), REQ-023 (`agent.tool-approval` supplemental), REQ-024 (three `Reference` edges) — gated on the Phase 3 approval.

## Assumptions
- Verified current state (Step 2): `[[architecture_assumption]] ARCH-002` has `config_keys = ["mcp_servers.*.url"]` only (lines 333-339 area); `agent.tool-approval` primary is `ADR-003` with supplemental `ADR-012` only (lines 45-50 area); 36 `[[adr_edge]]` rows, no duplicate `(from, to)` pair; no authority row names ADR-002; ADR-010 appears in no row.
- The ungated REQ-007 edit and the Phase 1 core validator (`eventbus.host` support) must land in the same commit, otherwise the core fail-closes on the unknown pattern `eventbus.host` (Plan Risk mitigation).
- Gated edits use the Plan's P2-P5 proposal texts verbatim; they land in one commit with the Index regeneration (release unit model-regen).

## Design decisions
- The ungated `current_value` wording records the server-side loopback guarantee as a code guard (`scripts/mcp_servers/server.py` pre-bind allow-list; no server toml carries a host key) that the config-check does not police — the assertion half is EventBus-only (Plan Assumption, verified).
- Gated additions follow the decision-owner direction semantics of P1: the new `Requires` edge points from the dependent ADR (ADR-004) to the owner (ADR-001).

## Alternatives considered
- Registering `platform.config-isolation` under ADR-004 as primary — rejected by the Plan: ADR-002 owns the isolation decision; ADR-004's supplemental is limited to failure classification (P3).

## Implementation
### Target file
`config/adr_authority.toml`
### Procedure
- Ungated (same commit as the core change): set ARCH-002 `config_keys = ["mcp_servers.*.url", "eventbus.host"]` and restate its `current_value` to name the EventBus loopback default and the server-side code guard (REQ-007).
- Gated (after the approval record only), all four together in one commit with the Index regeneration (REQ-026):
  - P2: replace `ADR-001 --Requires--> ADR-004` with `ADR-004 --Requires--> ADR-001`; preserve the bidirectional pair by flipping the `Reference` half to `ADR-001 --Reference--> ADR-004` with `intentional = true` and the ownership-split note (REQ-021).
  - P3: add `decision_target = "platform.config-isolation"`, `primary_adr = "ADR-002"`, supplemental `ADR-004` limited to "failure classification of Config Isolation violations only" (REQ-022).
  - P4: add supplemental `{ adr = "ADR-001", limit = "workflow-level approval gate mandatoriness only; tool-level approval semantics stay under ADR-003" }` to `agent.tool-approval` (REQ-023).
  - P5: add `Reference` edges `ADR-004 -> ADR-006`, `ADR-004 -> ADR-008`, `ADR-005 -> ADR-009` (REQ-024).
### Method
- TOML edits preserving the file's existing row ordering and note style; the core's model load and both downstream checkers verify every edit.
### Details
- After the reversal, the `by_pair` bidirectional check sees `ADR-004 -> ADR-001` (Requires) paired with the flipped `ADR-001 -> ADR-004` `Reference` (intentional); confirm the pair count enumerated by `adr-intentional-cycles` stays consistent (ADR-016 wording is covered by its own document).
- `ADR-004 -> ADR-006` / `ADR-004 -> ADR-008` / `ADR-005 -> ADR-009` are forward `Reference` edges alongside the existing reverse edges; `Reference` pairs are exempt from the acyclic authority-graph rule only through the intentional-cycle mechanism — confirm `check_adr_authority.py` stays exit 0 after the additions.

## Compatibility considerations
- `tools/check_adr_authority.py` and `tools/generate_adr_authority.py --check` run against this file on every change; the ungated REQ-007 commit is valid only once the core supports the new pattern (Phase 1 single-commit rule).

## Security considerations
- The `eventbus.host` key registration makes the EventBus loopback assumption machine-checked; a non-loopback value must fail `check_adr_authority.py`.

## Rollback considerations
- Ungated half: revert the single commit together with the core change. Gated half: revert the whole model-regen package atomically (config + ADR/Index/front matter edits + regeneration).

## Validation plan
- `uv run python tools/check_adr_authority.py` — exit 0 with the new keys (AC-1) and after the gated additions (AC-6).
- `uv run python tools/generate_adr_authority.py --check` — drift only after regeneration in the same commit (AC-6).
- `uv run pytest tests/tools/test_adr_authority.py` — the core fixtures covering this config (companion tests of the core procedure document).

## Completion criteria
- ARCH-002 asserts both patterns and its `current_value` names the code-guard half (AC-1, AC-4).
- Gated portion (once approved and executed): the model contains the reversed edge, both target registrations, and the three forward edges, and passes both model tools (AC-6).

## Out of Scope
- Core validator implementation (`tools/_adr_authority_core.py` row), ADR/front matter list edits (their rows), and the regeneration execution itself (Index row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update ARCH-002 `config_keys` and `current_value` in the same commit as the core `eventbus.host` validator (REQ-007) | Completed | 20261120 | 20261120 | — |
| 2 | Apply P2-P5: edge reversal, `platform.config-isolation`, `agent.tool-approval` supplemental, three `Reference` edges (REQ-021..REQ-024) | Completed | 20261120 | 20261120 | Approved 2026-11-20 by ADR-016 Approval Record amendment; reference-only pair form added (P5 relaxation); lands with regeneration |
| 3 | Run `check_adr_authority.py` and `generate_adr_authority.py --check` | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-007 (ARCH-002 key registration), REQ-021 (edge reversal), REQ-022 (Config Isolation target), REQ-023 (tool-approval supplemental), REQ-024 (forward `Reference` edges)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `config/adr_authority.toml`
