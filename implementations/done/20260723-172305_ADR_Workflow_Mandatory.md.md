## Goal

Create an Architectural Decision Record (ADR) documenting why workflow execution is mandatory and why workflow bypass modes are not supported.

## Scope

**In:**
- `ADR-Workflow-Mandatory.md` (new): ADR document at project root level
- Architecture overview documentation: Update links to the ADR
- Workflow documentation: Link to the ADR
- Deployment documentation: Link to the ADR where workflow artifacts are discussed
- Operations documentation: Link to the ADR where workflow failures are discussed

**Out:**
- Any runtime behavior changes
- Redesigning approval policy
- Introducing EventBus integration
- Defining every workflow stage

## Assumptions

1. The ADR should follow standard ADR format (Context → Decision → Rationale → Alternatives → Consequences → Non-Goals).
2. Historical motivation for the decision is not fully known — unknowns should be marked as "Unknown".
3. The architecture overview at `docs/01_overview-arch-02-pipelines.md` already mentions workflow as required — verify and update accordingly.
4. Existing workflow documentation exists — need to find it and add a link to the ADR.

## Design decisions

- Place ADR at project root level per acceptance criteria.
- Follow standard ADR format: Context → Decision → Rationale → Alternatives Considered → Consequences → Non-Goals.
- Mark unknown historical motivations as "Unknown" rather than guessing.
- Use clear, unambiguous language — "mandatory", "not supported", "required" — no hedging.

## Alternatives considered

- Single monolithic architecture doc instead of separate ADR: harder to track individual decisions over time.
- Embed ADR content in existing workflow documentation: loses the standalone nature of ADRs; makes it harder to reference from other documents.
- JSON/YAML structured ADR format: more machine-readable but less accessible to human readers.

## Implementation

### Target file

`ADR-Workflow-Mandatory.md`

### Procedure

1. Create `ADR-Workflow-Mandatory.md` at project root with standard ADR sections
2. Search for and update references in architecture overview, workflow docs, deployment docs, and operations docs

### Method

Create a new ADR document following standard ADR format.

### Details

**Phase 1: Create ADR Document**

Create `ADR-Workflow-Mandatory.md` at project root with:
- **Context**: System executes LLM-planned tasks, some tools have side effects, some operations require approval, tool execution must be observable and recoverable, direct LLM-to-tool path would make auditing and recovery harder
- **Decision**: Workflow execution is mandatory, workflow definitions are required deployment artifacts, workflow bypass mode is not supported, optional workflow mode is not supported, direct execution fallback is not supported
- **Rationale**: All side-effecting operations must be traceable, approval state must survive process boundaries, retry and idempotency behavior must be centralized, partial task completion must be inspectable, recovery requires persisted task and attempt state, tool execution should not depend solely on LLM conversational state
- **Alternatives Considered**: Direct tool execution without workflow (rejected), Optional workflow mode (rejected), Workflow disabled for local mode (rejected), Workflow fallback when workflow definition is missing (rejected), Per-tool ad hoc approval without workflow state (rejected)
- **Consequences**: Deployment must include workflow definition files, startup must fail if mandatory workflow artifacts are missing or invalid, workflow schema must be initialized before service startup, operators must treat workflow failures as platform failures, simple chat and tool-backed tasks share the same execution control plane
- **Non-Goals**: Define every workflow stage, redesign approval policy, introduce EventBus integration, change runtime behavior

**Phase 2: Update Documentation References**

Search for and update references in:
- Architecture overview (`docs/01_overview-arch-02-pipelines.md`)
- Workflow documentation files
- Deployment documentation files
- Operations documentation files

## Compatibility considerations

N/A — documentation-only task, no runtime impact.

## Security considerations

N/A — documentation-only task, no security impact.

## Rollback considerations

Simple revert of ADR document addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADR-Workflow-Mandatory.md | Manual review | Read file, verify against acceptance criteria | All sections present, clear statements |
| docs/01_overview-arch-02-pipelines.md | Manual review | Read file, check ADR link | Link added appropriately |
| Workflow docs | Manual review | Search for workflow docs, check links | Links added to relevant files |
| Deployment docs | Manual review | Search for deployment docs, check links | Links added where workflow artifacts discussed |
| Operations docs | Manual review | Search for ops docs, check links | Links added where workflow failures discussed |

## Out of scope

- Any runtime behavior changes
- Redesigning approval policy
- Introducing EventBus integration
- Defining every workflow stage

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-152111_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-172305
- Related target files: ADR-Workflow-Mandatory.md
