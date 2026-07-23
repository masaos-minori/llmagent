## Goal

Create a centralized document explaining failure modes, degradation behavior, and capability-oriented readiness to replace scattered failure documentation.

## Scope

**In:**
- `docs/05_failure_modes_and_operational_readiness.md` (new): Centralized failure modes and readiness document
- Operations documentation: Update links to the new document
- Index documents: Update links to the new document

**Out:**
- Any runtime behavior changes
- Implementing readiness reporting infrastructure
- Modifying existing failure handling code

## Assumptions

1. The document should follow a consistent structure: failure categories → per-service behavior → capability readiness model → operator examples.
2. The capability readiness model uses four states: healthy, degraded, unavailable, unknown.
3. Each capability has: Required services, Optional services, Degraded conditions, Unavailable conditions, Recovery actions.
4. MCP failure behavior varies by startup_mode (none, persistent, subprocess).
5. Memory layer has four activation modes: disabled, fts-only, degraded, hybrid.

## Design decisions

- Use capability-oriented language throughout ("Repository Operations unavailable" vs "git-mcp down") — operators care about what they can do, not which service is down.
- Include both service-level and capability-level views — operators need both for diagnosis and communication.
- Provide concrete operator-facing examples — helps operators quickly understand their situation.

## Alternatives considered

- Single monolithic document instead of separate ADRs: harder to navigate, but easier to keep in sync.
- Embed readiness model in existing deployment docs: loses the standalone nature; makes it harder for operators to find.
- JSON/YAML structured readiness data with generated Markdown: more machine-readable but less accessible to human readers.

## Implementation

### Target file

`docs/05_failure_modes_and_operational_readiness.md`

### Procedure

1. Create `docs/05_failure_modes_and_operational_readiness.md` with failure modes and readiness content
2. Search for and update references in operations documentation and index documents

### Method

Create a new documentation file following the specified structure.

### Details

**Phase 1: Create Centralized Document**

Create `docs/05_failure_modes_and_operational_readiness.md` with:
- **Section 1**: Failure Mode Overview (8 categories)
- **Section 2**: MCP Failure Behavior (per startup_mode + fail-fast/fail-open)
- **Section 3**: Workflow Failure Behavior (6 scenarios)
- **Section 4**: RAG Failure Behavior (6 scenarios + degraded behavior)
- **Section 5**: Memory Layer Failure Behavior (4 activation modes)
- **Section 6**: Capability Readiness Model (4 states × 10 capabilities)
- **Section 7**: Operator-Facing Examples (concrete user-facing messages)

**Phase 2: Update Documentation References**

Search for and update references in operations documentation and index documents.

## Compatibility considerations

N/A — documentation-only task, no runtime impact.

## Security considerations

N/A — documentation-only task, no security impact.

## Rollback considerations

Simple revert of document addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/05_failure_modes_and_operational_readiness.md | Manual review | Read file, verify against acceptance criteria | All sections present, all capabilities covered |
| Operations docs | Manual review | Search for ops docs, check links | Links added appropriately |
| Index docs | Manual review | Search for index docs, check links | Links added appropriately |

## Out of scope

- Any runtime behavior changes
- Implementing readiness reporting infrastructure
- Modifying existing failure handling code

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-152248_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-172446
- Related target files: docs/05_failure_modes_and_operational_readiness.md
