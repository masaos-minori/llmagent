## Goal
Make ADR-014's Decision and INV-02 name the same producer (`Orchestrator` constructs the single `LlmTurnExecutor`; the WorkflowEngine side is the logical owner of the loop) (`REQ-004`, `REQ-008` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Decision already says the `Orchestrator` is the construction owner and the WorkflowEngine side the logical owner; INV-02 says 'the one component that actually drives the ... loop' — the two differ (checked).
- The single construction site is `scripts/agent/orchestrator.py:121` (`self._llm_executor = LlmTurnExecutor(`); the INV-02 test row cites `tests/agent/test_orchestrator.py`.
- Overlap: adrrev016 edits this ADR's front matter and Related ADRs, not INV-02 or the Decision.

## Design decisions
- Reword INV-02 to name the `Orchestrator` as the creator and the single holder, keeping the WorkflowEngine side as logical owner of the loop; do not change the INV-02 number or its test row.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`

### Procedure
1. INV-02 (Invariants list): name `Orchestrator` as the sole creator of the `LlmTurnExecutor` instance.
2. Decision paragraph on `LlmTurnExecutor`: keep construction and logical ownership consistent with INV-02.
3. Append one `Current Decision Approval (pending)` line.

### Method
- INV-02 new text: `Creation of the `LlmTurnExecutor` instance is centralized in the `Orchestrator`, which constructs exactly one and injects it; the WorkflowEngine side is the logical owner of the loop. No other component holds unused or duplicate `LlmTurnExecutor` instances.`
- Decision: verify the sentence already matches; adjust only if it names a different producer.
- Approval line wording as in the sibling ADR procedures (approver, date, scope 不明; tracked by adrrev012).

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); none is written on a maintainer's behalf (UNK-04).
- Reflect the new INV-02 wording in the index row for ADR-014 INV-02 only through the index procedure (row 08), not here.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (only the intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- The Decision and INV-02 name the same producer; INV-02's test row is unchanged; a marked pending approval line exists.

## Out of Scope
- Front matter and Related ADRs (adrrev016); the index row (row 08); code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-171455 | 20261112-171455 | Changed: docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md. Step 3a: Decision text (line 58 and the Implementation paragraph) already names the Orchestrator as constructor and the Workflow Engine side as logical owner, so only INV-02 was reworded; pending approval line added without plan name |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-171455 | 20261112-171455 | ADR checkers, docs checkers pass; preservation reports only the intended INV-02 and Approval changes (ERROR by design); tests/agent/test_orchestrator.py 135 passed (INV-02 test row unchanged) |

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
- **Requirement ID**: `REQ-004` / `REQ-008` — one named producer of `LlmTurnExecutor`; pending approval
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`