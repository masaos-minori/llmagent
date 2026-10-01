# Implementation Procedure: Add Registry entries for uncovered areas

## Goal

Add Canonical Source Registry entries for areas lacking coverage (Overview, Deployment, RAG, MCP, Agent, Shared/DB, Governance) where valid canonical sources can be identified through evidence-based classification.

## Scope

- Modify only `config/documentation_canonical_sources.toml`.
- In-Scope: Adding Registry entries for areas without existing entries where a valid canonical source can be confirmed via Purpose/area alignment.
- Out-of-Scope: Removing or subordinating `## Area Canonical Maps` in the Policy (REQ-001); updating area Document Guides (REQ-004–REQ-009); updating Needs Confirmation Inventory (REQ-003).

## Assumptions

- The two existing Registry entries (`eventbus.core-behavior`, `eventbus.persistence-schema`) are correct.
- Candidate replacements identified in canon001 investigation are accurate:
  - Overview: `docs/01_overview/overview-arch-01-process.md` (architecture process overview)
  - Deployment: `deploy/deploy.sh` (confirmed deploy script)
  - RAG/MCP/Agent/Shared/DB: no `*specification*` file exists; closest equivalents must be identified per area
  - Governance: the Policy itself is the governance authority
- Only add entries where Purpose/area alignment can be confirmed via existing document metadata.

## Design decisions

- **Approach**: Register one entry per area where a valid canonical source can be identified. Areas without a valid replacement are registered as design gaps (Known Issue or Needs Confirmation) rather than guessed entries.
- **Claim type selection**: Use `design-documentation` for architecture/design documents; use `runtime-behavior` only when the source governs runtime behavior; use `database-schema` for schema definitions.
- **Decision target naming**: Follow the pattern `<area>.<purpose>` (e.g., `overview.architecture-overview`).

## Alternatives considered

- Register all seven areas even if some lack clear canonical sources: rejected — introduces guesswork entries that could mislead downstream tooling.
- Wait until canon002 is resolved before adding entries: not required — canon002 affects only the EventBus entries' validator status, not new entries.

## Implementation

### Target file

`config/documentation_canonical_sources.toml`

### Procedure

1. Identify valid canonical sources for each uncovered area using evidence from canon001 investigation.
2. Add Registry entries for areas with confirmed canonical sources.
3. Register areas without valid replacements as design gaps in the Needs Confirmation Inventory (REQ-003) rather than guessing entries here.

### Method

Edit `config/documentation_canonical_sources.toml` in-place using targeted edits.

### Details

**Step 1: Identify valid canonical sources**

Based on canon001 investigation findings:

| Area | Candidate Source | Evidence | Classification |
|------|------------------|----------|----------------|
| Overview | `docs/01_overview/overview-arch-01-process.md` | Architecture process overview role | Valid |
| Deployment | `deploy/deploy.sh` | Confirmed deploy script in deployment docs | Valid |
| RAG | None confirmed | No `*specification*` file exists; no close equivalent identified | Gap |
| MCP | None confirmed | No `*specification*` file exists; no close equivalent identified | Gap |
| Agent | None confirmed | No `*specification*` file exists; no close equivalent identified | Gap |
| Shared/DB | None confirmed | No `*specification*` file exists; no close equivalent identified | Gap |
| Governance | `docs/00_governance/governance_01_documentation-policy.md` | Policy is the governance authority | Valid |

**Step 2: Add Registry entries for areas with confirmed sources**

Append the following entries after the existing EventBus entries:

```toml
[[canonical_sources]]
decision_target = "overview.architecture-overview"
claim_type = "design-documentation"
source_paths = ["docs/01_overview/overview-arch-01-process.md"]
area = "Overview"
notes = "Architecture process overview; candidate replacement for docs/architecture.md."

[[canonical_sources]]
decision_target = "deployment.deploy-script"
claim_type = "operational-instruction"
source_paths = ["deploy/deploy.sh"]
area = "Deployment"
notes = "Deploy script; candidate replacement for deploy.sh."

[[canonical_sources]]
decision_target = "governance.policy"
claim_type = "design-documentation"
source_paths = ["docs/00_governance/governance_01_documentation-policy.md"]
area = "Governance"
notes = "Documentation policy is the governance authority."
```

**Step 3: Register design gaps**

For areas without valid replacements (RAG, MCP, Agent, Shared/DB), register them as concrete follow-up issues in `issues/` during REQ-003 execution. Do NOT add guessed entries here.

## Compatibility considerations

- The split Decision Targets preserve the semantic distinction between bootstrap DDL and incremental migration.
- Existing references to the original `eventbus.persistence-schema` Decision Target must be updated to reference the new targets.
- The `area` field alignment to `EventBus` may affect downstream tooling that relies on area-based grouping.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Remove the added Registry entries and revert any area field changes.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/documentation_canonical_sources.toml` | Registry validation | `uv run python tools/check_canonical_source_registry.py` | Pass (may fail due to canon002 dependency) |
| All affected docs | Conflict detection | `uv run python tools/check_canonical_source_conflicts.py` | Pass (may have false positives due to canon003) |

## Completion criteria

- Every new Registry entry's `source_paths` value exists in the repository.
- Each new entry has a claim_type recognized by the registry validator.
- No decision_target conflicts with existing entries.
- Areas without valid canonical sources are NOT registered here — they are recorded as follow-up issues instead.

## Out of scope

Removing or subordinating `## Area Canonical Maps` in the Policy (REQ-001). Updating area Document Guides (REQ-004–REQ-009). Updating Needs Confirmation Inventory (REQ-003). Fixing the `eventbus.persistence-schema` Registry validation failure (canon002). Fixing checker defects (canon003, ncinv001).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify valid canonical sources for each uncovered area | Pending | — | — | REQ-002 |
| 2 | Add Registry entries for areas with confirmed sources | Pending | — | — | REQ-002 |
| 3 | Register design gaps as follow-up issues | Pending | — | — | REQ-003 |

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
- **Requirement ID**: REQ-002 — classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224049
- **Related target files**: config/documentation_canonical_sources.toml
