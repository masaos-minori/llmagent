# Implementation Procedure: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

## Goal

State in ADR-004 where the machine-readable mandatoriness registry lives and that configuration cannot weaken it (plan row: state where the registry lives; config cannot weaken it).

## Scope

- Two sentence-level edits in `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`: Group 3 item 13 (:80) and a pointer sentence near the Fail-Fast list item 14 (:85).
- Criteria text (items 9-12, :76-79) unchanged — the registry records classifications; the ADR remains the sole criteria source (issue Constraint: no competing copy).

## Assumptions

- Lightweight row: docs-only prose edits.
- Needs Confirmation (plan U-1): adrauth001's ADR-016 authority model may designate a different authoritative home for classification data. Default wording: name `registry/component_mandatoriness.yaml` as the machine-readable registry and add "until superseded by the ADR authority model" so a later ADR edit is an amendment, not a rewrite. Land this row after adrauth001's ADR-016 procedure decisions are known if that information is available at implementation time (plan Dependencies: "ADR-004 doc row sequencing").

## Design decisions

- Item 13 (:80): extend the existing sentence "Approved classification of each MCP server is recorded in the classification table of `agent_08_04`" with "in machine-readable form at `registry/component_mandatoriness.yaml`; the `agent_08_04` table is generated from it" — keeping the existing chain (criteria here, classification there, config effective-only) intact.
- Item 14 (:85): append to "Undeterminable component mandatoriness" a parenthetical "(no matching entry in the mandatoriness registry)" so the Fail-Fast entry names its detection source; do not add new Fail-Fast items.

## Alternatives considered

- N/A: docs-only change (plan lightweight row).

## Implementation

### Target file

`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure

1. Edit item 13 (:80) per Design decision 1.
2. Edit item 14 (:85) per Design decision 2.

### Method

In-place sentence extension; no heading or item-number changes (ADR structure checkers forbid reordering).

### Details

- Wording must not introduce implementation detail (symbol names, loader functions) beyond the registry path — Docs content policy (`skills/DESIGN.md`).
- The ADR is content-preservation checked (`check_adr_preservation.py` compares changed ADRs against a Git ref): additions only, no removals of existing clauses.

## Compatibility considerations

- `check_adr_structure.py` and `check_docs_consistency.py --domain mcp` must pass; the registry path string here becomes a docs-claim that row 8's checker keeps true.

## Security considerations

- N/A: documentation of an existing fail-closed rule.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_docs_consistency.py --domain mcp`, `check_docs_quality.py`, `check_docs_content_policy.py` (routing.md docs checker set).

## Completion criteria

- A reader of item 13 finds the registry path and the generated-table relationship; item 14's mandatoriness entry names its detection source; all ADR checkers green.

## Out of Scope

- Registry file (row 1), table conversion (row 26), any criteria changes (plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two item edits per Procedure | Pending | — | — | U-1 sequencing check first |
| 3 | Run the docs/ADR checker set | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | adrauth001 ADR-016 authority decision (plan Dependencies) — wording is amendment-safe either way | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002/REQ-005 (registry placement statement; classification authority chain)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
