# Introduce a machine-readable Canonical Source Registry

## Priority
Medium

## Summary
Create one machine-readable registry that maps each decision target and claim type to its canonical source. The registry must become the single system of record for canonical-source ownership.

## Background
Area-level Primary and Secondary tables do not identify what each document is primary for. Multiple documents can therefore be labeled Primary without a deterministic way to resolve overlapping claims.

## Problem
A machine-readable registry is required to enforce the rule that each decision-target and claim-type pair has at most one canonical source.

## Reason for Change
Without a single system of record, canonical-source ownership stays distributed across hand-maintained area tables that can silently drift out of sync with each other and with the target-based resolution model (`M-01-02`).

## Implementation Intent
Provide a single registry that can be validated by CI and consumed by documentation tools without duplicating authority mappings across area guides.

### Proposed model

Use a structure equivalent to the following. The exact file format may be adjusted to match repository conventions, but semantic fields must remain explicit.

    version: 1
    targets:
      agent.tool-routing:
        architecture-decision:
          source: docs/adr/ADR-003-runtime-tool-registry-routing-authority.md
        functional-requirement:
          source: docs/05_agent_03_runtime-tool-routing.md
        runtime-behavior:
          sources:
            - scripts/shared/runtime_tool_registry.py
            - scripts/shared/route_resolver.py

### Required registry fields

At minimum, support:

- Registry schema version
- Decision-target identifier
- Claim type
- Canonical source path or explicitly permitted source set
- Source kind
- Owning area
- Optional validation reference

Use a single `source` for normative document claims. Permit `sources` only for claim types whose canonical implementation necessarily spans multiple files, such as runtime behavior. Do not use `sources` to permit multiple competing normative documents.

## Target Files or Areas
Suggested locations, subject to repository conventions:

- `config/documentation_canonical_sources.yaml`
- `config/documentation_canonical_sources.schema.json`
- `docs/00_governance_01_documentation-policy.md`
- `docs/00_governance_04_documentation-checks.md`
- Area document guides
- Documentation generation tools, if registry tables are generated

## Required Changes
1. Select a repository-consistent registry location and format.
2. Add a schema for validating the registry.
3. Define a stable naming convention for decision targets.
4. Define whether target identifiers are hierarchical.
5. Define source-path resolution from the repository root.
6. Require registered files to exist.
7. Prevent Draft documents from being registered as canonical normative sources.
8. Prevent more than one normative canonical source for the same target and claim type.
9. Define how Accepted ADR status is verified.
10. Define how generated documentation displays registry entries.
11. Make the registry the system of record.
12. Do not retain independently maintained authority tables in area guides.

### Area guide behavior

Area guides must either:

- Link to the registry, or
- Display registry-generated content

Area guides must not maintain a separate hand-edited canonical-source mapping.

## Constraints
Use a single `source` field for normative document claims; permit a `sources` list only for claim types whose canonical implementation necessarily spans multiple files (e.g. `runtime-behavior`) — never use `sources` to allow multiple competing normative documents for the same target and claim type.

## Acceptance Criteria
- [ ] One machine-readable registry is the system of record.
- [ ] The registry has a versioned schema.
- [ ] Decision targets follow a documented naming convention.
- [ ] Every entry contains a valid claim type.
- [ ] Every registered source path resolves.
- [ ] A normative target and claim type cannot have multiple canonical documents.
- [ ] Draft documents cannot be registered as normative canonical sources.
- [ ] Accepted ADR status is checked for ADR canonical entries.
- [ ] Area guides do not maintain duplicate hand-edited mappings.
- [ ] Registry parser and schema tests are included.
- [ ] Documentation validation tests pass.

## Testing Expectations
Add registry-parser and schema-validation tests (unit level); run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` against updated area guides.

## Documentation Impact
Yes — this issue creates a new machine-readable registry and updates the governance documents and area guides listed in Target Files or Areas to reference it.

## Out of Scope
- Do not fully populate every target in this issue. Complete migration is handled separately.
- Do not change application routing or runtime ownership.
- Do not use the registry to declare code compliant with design.

## Dependencies
Depends on `M-01-01`, `M-01-02`, and `M-01-03`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-01` through `M-01-03` have landed before designing the registry schema — the registry's `claim type` field must use `M-01-01`'s taxonomy, and its conflict semantics must match `M-01-02`'s resolution algorithm. Select the registry format and location based on existing repository conventions (see `rules/coding.md`, `routing.md`) rather than inventing a new convention. Do not populate the registry with every existing target in this issue — that is `M-01-06`'s scope. Do not change application routing or runtime ownership.
