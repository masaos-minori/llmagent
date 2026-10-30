# Implementation Procedure: contract_manifest.json schema

## Goal

Create the JSON Schema that every `registry/manifests/*.yaml` contract manifest must
validate against (REQ-005: manifests are schema-validated; plan Context "follows
doc_front_matter.json convention").

## Scope

**In scope:**
- New schema file with the manifest envelope: `manifest` (new), `version` (new), `generated_by` (new),
  `sources` (repo-relative paths), `deferred` flag (REQ-007), and `entries` (array of
  objects; per-manifest entry shape via a `manifest` const branch or `oneOf` (new)).
- Follow the structural style of the existing `schemas/doc_front_matter.json` and
  `schemas/event_envelope.json`.

**Out of scope:**
- Per-manifest dedicated schemas (the seven entry shapes live as branches inside this
  one file to keep a single validation entry point).
- Validator code (doc 05 consumes this schema).

## Assumptions
- Needs Confirmation: the plan row says `tools/schemas/contract_manifest.json`, but the
  repository has no `tools/schemas/` directory; the two existing schemas live at repo
  root `schemas/` (`schemas/doc_front_matter.json`, `schemas/event_envelope.json`).
  This document adopts root `schemas/contract_manifest.json` to follow the actual
  convention; confirm before implementation.
- Verified: `jsonschema>=4.0` is already a project dependency (pyproject.toml), so
  validation needs no new install.
- `registry/manifests/` was created as an empty scaffold during procedure generation
  (the YAML files themselves are generated artifacts of docs 05+).

## Design decisions
- Draft-07 schema keyed by a required `manifest` enum (`tool_ownership`,
  `mcp_endpoints` (new), `eventbus_route_roles` (new), `db_schema_versions`, `config_ownership`,
  `health_contracts`, `invariant_coverage`) so one file validates all seven and rejects
  unknown manifest names (deferred names are added by their own plans, REQ-007).
- `sources` is required and non-empty: every manifest must declare the live-code files
  it was generated from — this is what the manifest↔source drift check (doc 05) re-reads.

## Alternatives considered
- One schema file per manifest: rejected — seven files, seven registration points, no
  gain; the checker in doc 05 loads exactly one path.
- YAML schema (JSON Schema in YAML): rejected — existing schemas are JSON.

## Implementation
### Target file
`schemas/contract_manifest.json` (new)

### Procedure
1. Model the envelope after `schemas/doc_front_matter.json` (required fields,
   `additionalProperties: false`).
2. Envelope required keys: `manifest` (enum), `version` (integer), `generated_by` (new)
   (const `tools/generate_reference_table.py`), `sources` (array of strings),
   `generated_at` (string, excluded from drift comparison), `entries` (array).
3. Entry shapes per manifest enum value via `allOf` (new)/`if-then` branches; each entry
   keyed by a stable natural key (tool name, server key, route, db name, config field,
   contract name, invariant id).

### Method
Hand-written JSON Schema; validated by doc 05's manifest writer on every generation.

### Details
- Keep each entry shape minimal: identity fields plus the facts rendered into the doc
  blocks; free-text evidence stays in the matrix/docs, not in manifests.

## Compatibility considerations
New file only; no consumer exists until doc 05 lands.

## Security considerations
N/A: static schema file.

## Rollback considerations
N/A: delete the file (single target).

## Validation plan
- Validated through doc 05's manifest tests (schema-rejection fixture cases) and
  `uv run python tools/generate_reference_table.py --manifests` against the live repo.

## Completion criteria
All seven generated manifests validate against this schema; an entry with a missing key
or an unknown manifest name is rejected.

## Out of Scope
Generator code, manifest files themselves, CI wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm target path (`schemas/` vs plan's `tools/schemas/`) with the requester | Pending | — | — | Needs Confirmation above |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (schema-validated manifest outputs)
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tools/schemas/contract_manifest.json` (plan row path; adopted target `schemas/contract_manifest.json` — see Assumptions)
