## Goal
Correct ADR-015's deferred-manifest sentence and its generated-document list, with a pending approval record (`REQ-001`, `REQ-008` / `AC-1`, `AC-8`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `registry/manifests/component_mandatoriness.yaml` and `config/adr_authority.toml` exist; `architecture_assumptions` appears only in `schemas/contract_manifest.json` (checked against the repository).
- UNK-01 (is an `adr_authority` manifest wanted) is open: the text states that the source landed and no manifest is produced.
- Line numbers drift; locate by text: the sentence beginning `Deferred manifests (` and the generated-document list in Implementation Notes.

## Design decisions
- The sentence states per manifest: `component_mandatoriness` produced, `architecture_assumptions` still deferred, `adr_authority` source landed and no manifest produced pending UNK-01.
- Add `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` to the list with its `mandatoriness` rendering.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`

### Procedure
1. Rewrite the `Deferred manifests` sentence, and add `component_mandatoriness` to the fact-manifest list.
2. Add the `agent_08_04` entry to the generated-document list.
3. Append one `Current Decision Approval (pending)` line to the Approval Record.

### Method
- Replace the sentence with: the `component_mandatoriness` manifest is produced from `scripts/shared/component_mandatoriness.py`; `adr_authority` has its source (`config/adr_authority.toml`) and no manifest (maintainer decision pending); the architecture-assumptions manifest remains deferred.
- List entry form: `mandatoriness` — `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, matching the existing `- <name> — <path>` bullets.
- Approval line wording: `Current Decision Approval (pending)`: the manifest-status and generated-document-list correction awaits maintainer approval; approver, date, and scope are 不明 (recorded as pending, not resolved); tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); none is written on a maintainer's behalf (UNK-04).
- Do not change any Decision, invariant, or reference; `check_adr_preservation.py` should report only the manifest sentence and the list as changed.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (only the intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/generate_reference_table.py --check` — no drift.

## Completion criteria
- ADR-015 no longer calls `component_mandatoriness` deferred and lists `agent_08_04` as generated.
- A marked pending approval line exists; the checkers pass.

## Out of Scope
- The `agent_08_04` front matter (row 03); inventing an `adr_authority` manifest (UNK-01); approval records for a maintainer.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-170434 | 20261112-170434 | Changed: docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md. Step 3a/3b: also added agent_08_04 to the front matter related list (the structure checker requires it for a referenced document), added component_mandatoriness to the Fact manifests list, and omitted plan IDs from the new text; pending approval line added, no approval recorded |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-170434 | 20261112-170434 | ADR structure/authority/matrix/reference, known-deviation-sync, docs quality/content-policy strict/japanese/structure pass; check_adr_preservation reports only the intended front matter and Approval changes (ERROR by design); generate_reference_table --check runs with seq 03 |

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
- **Requirement ID**: `REQ-001` / `REQ-008` — truthful manifest status and generated-document list; pending approval record
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`