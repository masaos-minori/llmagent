# Resolve Canonical Source Registry validation failure for eventbus.persistence-schema and stale notes paths

## Priority
High

## Summary
`uv run python tools/check_canonical_source_registry.py` currently exits with status 1 because the `eventbus.persistence-schema` entry in `config/documentation_canonical_sources.toml` registers two `source_paths` for claim type `database-schema`, while the registry contract allows multiple sources only for `runtime-behavior`. In addition, both Registry entries' `notes` fields cite document paths that no longer exist. Decide the single normative source (or a justified contract change) for the EventBus persistence schema and correct the Registry so the validator passes.

## Background
- `config/documentation_canonical_sources.toml` is the system of record for canonical-source ownership (`docs/00_governance/governance_01_documentation-policy.md`, `### Canonical Source Registry`). `Documentation only`
- The two EventBus entries were added by commit `b0a9e0c5a` ("docs: migrate EventBus canonical source declarations to registry").
- `tools/check_canonical_source_registry.py` enforces single-normative-source per claim type, exempting only `runtime-behavior` (`SINGLE_SOURCE_EXEMPTIONS`). `Explicit in code`
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` states the EventBus schema authority is split between `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL) and `scripts/eventbus/db.py` (incremental migration at service startup), citing ADR-008 INV-04. `Documentation only`

## Problem
- Validator output (2026-10-01): `multiple source_paths (2) for claim_type 'database-schema' on entry targeting 'eventbus.persistence-schema': only 'runtime-behavior' allows multiple sources`; exit status 1. `Explicit in code`
- `eventbus.core-behavior` notes cite `docs/06_eventbus_00_document-guide.md`, which does not exist; the current guide is `docs/24_eventbus/eventbus_00_document-guide.md` (to be confirmed as the intended document).
- `eventbus.persistence-schema` notes cite `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`, which does not exist; the matching content is in `docs/41_db/db_02_architecture_and_schema-schema-reference.md` (to be confirmed).
- Both notes embed document line numbers, which go stale on any edit.
- The `eventbus.persistence-schema` entry's `area` is `Shared/DB` while `eventbus.core-behavior` is `EventBus`; whether the ownership area is intended is not documented.

## Reason for Change
- The Registry is the system of record but currently fails its own validator, so any task requiring "Registry check passes" (including `canon001`) cannot complete.
- Two normative sources for one `database-schema` Decision Target is exactly the multi-source condition the governance rules prohibit, and must be resolved or explicitly justified.

## Implementation Intent
- Treat this as a `registry-mismatch` / potential `canonical-source-conflict` between the Registry, the registry contract, and `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.
- Determine the approved definition from ADR-008 and related ADRs/Specifications, not from current code behavior alone.
- Possible directions (choose based on evidence, do not pre-decide):
  - one file is the normative schema source and the other is registered under a different claim type or Decision Target (for example a migration-specific target);
  - the Decision Target is split into separately registered targets (bootstrap DDL vs. migration);
  - the registry contract itself is amended through the proper governance route, if two sources are an approved design.
- If the approved definition cannot be determined, register it in the Canonical Source Conflict part of `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and do not mark it resolved.
- Update the Registry and every document restating the schema authority in the same change.

## Target Files or Areas
- `config/documentation_canonical_sources.toml`
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` (schema authority statement)
- `docs/24_eventbus/eventbus_00_document-guide.md` (`## Canonical Source Rule`)
- `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` (if it restates schema authority)
- `docs/10_adr/ADR-008-sqlite-4db-separation.md` (read for evidence; edit only if an ADR change is explicitly approved)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 3, only if unresolved)

## Required Changes
- Decide, with ADR/Specification evidence, the single normative source(s) for `eventbus.persistence-schema` under the current registry contract, or record a Canonical Source Conflict.
- Update the `eventbus.persistence-schema` entry (and add entries if the target is split) so the validator passes.
- Replace the nonexistent paths in both entries' `notes` with current paths after confirming the referenced content, and remove embedded line numbers.
- Align `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and the EventBus Document Guide with the final Registry content.

## Constraints
- Do not change `SINGLE_SOURCE_EXEMPTIONS` or the validator simply to make the check pass; a contract change requires governance approval.
- Do not decide schema authority from code behavior or file dates alone.
- `docs/` text must follow `skills/DESIGN.md` Shared Vocabulary (English, no source-code line numbers, no concrete config values).
- No runtime code under `scripts/` may be changed.

## Acceptance Criteria
- `uv run python tools/check_canonical_source_registry.py` exits 0.
- No Registry `notes` value cites a nonexistent path or a document line number.
- Each `database-schema` Decision Target in the Registry has exactly one normative source.
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and `docs/24_eventbus/eventbus_00_document-guide.md` do not contradict the Registry.
- If the decision could not be made, a Canonical Source Conflict entry exists with Decision Target, competing sources, evidence, and required decision, and this is reported instead of claiming resolution.

## Testing Expectations
Documentation and configuration only. Run and record:
- `uv run python tools/check_canonical_source_registry.py`
- `uv run python tools/check_canonical_source_conflicts.py`
- `uv run python tools/check_docs_structure.py` and `uv run python tools/check_docs_quality.py` for edited docs
- `uv run python tools/check_issue_inventory_conformance.py` if the governance inventory is edited

## Documentation Impact
Yes. Canonical-source ownership for the EventBus persistence schema (Registry, DB schema reference, EventBus guide). Record a Canonical Source Conflict if undecidable.

## Out of Scope
- Changes to EventBus schema DDL or migration code.
- Policy `## Area Canonical Maps` cleanup (issue `canon001`).
- Fixing CANONICAL-006 false positives in `tools/check_canonical_source_conflicts.py` (issue `canon003`).
- Adding Registry entries for other areas.

## Dependencies
- Blocks `canon001` acceptance (Registry check must pass).
- Related to `canon003` (conflict checker output for the same entries).

## Unresolved Questions
- Does ADR-008 (or another accepted ADR) designate a single schema authority for `eventbus.sqlite`, or does it approve the bootstrap/migration split?
- Is `Shared/DB` the intended owning area for `eventbus.persistence-schema`?

## AI Implementation Instruction
- Read ADR-008 and the DB/EventBus schema docs before editing the Registry; cite the evidence used for the decision.
- Do not modify validator code or exemption sets.
- Keep changes to the Target Files; update Registry and referencing docs in one change.
- If evidence is insufficient, register a Canonical Source Conflict and stop; report it rather than choosing a source.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-103451
- **Related target files**: config/documentation_canonical_sources.toml, docs/41_db/db_02_architecture_and_schema-schema-reference.md, docs/24_eventbus/eventbus_00_document-guide.md, docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md, docs/10_adr/ADR-008-sqlite-4db-separation.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md
