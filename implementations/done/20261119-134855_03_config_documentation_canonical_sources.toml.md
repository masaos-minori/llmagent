## Goal

- Align the five defective rows of `config/documentation_canonical_sources.toml` with the governing ADRs and the Resolution Matrix per the Plan: `REQ-014` bootstrap DDL source path, `REQ-015` posture-failure-handling note, `REQ-016` governance.policy row, `REQ-019` overview claim type; the `mcp.component-mandatoriness` row stays unchanged (`REQ-017` is approval-gated).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: row edits in the target file for `REQ-014`, `REQ-015`, `REQ-016`, `REQ-019`.
- Out of scope: the `mcp.component-mandatoriness` row (lines 66–71) — proposal only, owned by seq 05.

## Assumptions

- Current-Specification-Only (Plan Assumptions): the ADR bodies and the Resolution Matrix are the specification; the rows are corrected toward them, never the reverse.
- The corrected file must pass all three consumers with exit 0 (`AC-12`, `T12`): both checkers and `tools/check_canonical_document_prose.py`.

## Design decisions

- `REQ-019`/`REQ-016` final values are an UNK-04 decision taken against the Matrix rows at implementation time, then pinned by the fixture test in seq 09:
  - Preferred option for `governance.policy` (lines 31–36): the Matrix `documentation-metadata` row (governance_01 line 135) assigns that claim type's canonical source kind to `docs/00_governance/governance_02_documentation-metadata.md`; a row with `claim_type = "documentation-metadata"` (line 33) pointing at `governance_01_documentation-policy.md` (line 34) contradicts it — re-point the source to the documentation-metadata document, or re-type the claim to a Matrix row whose canonical kind covers the governance policy document, recording the chosen Matrix row in the commit message.
  - For `overview.architecture-overview` (lines 17–22): the claim registered is "this overview document is the canonical architecture-overview reference" — a claim about a documentation asset. `architecture-decision` is not available because the Matrix names Accepted ADRs as that claim type's canonical kind, and `docs/01_overview/overview_01_01-arch-process.md` is not an ADR. Apply the same option set as above and record the chosen Matrix row.
  - The fixture test pins the chosen outcome; do not leave either row silently "as-is".

## Alternatives considered

- Delete the two disputed rows instead of correcting them — rejected: the Plan's `AC-12` requires the corrected rows to pass the checkers, and deleting a canonical registration is a governance gap the Plan does not authorize here.

## Implementation
### Target file
`config/documentation_canonical_sources.toml`
### Procedure
1. `REQ-014`: in the `eventbus.persistence-schema.bootstrap-ddl` row (lines 10–15), replace `source_paths = ["scripts/db/schema_sql.py"]` (line 13) with `["scripts/eventbus/schema.sql"]` — the only DDL definition for that Decision Target per `docs/41_db/db_02_architecture_and_schema-schema-reference.md` line 58 (file exists, 2892 B, verified 2026-11-19).
2. `REQ-015`: in the `agent.posture-failure-handling` row (lines 73–78), rewrite the notes (line 78) to match ADR-004 Group 1 item 1 (single common failure-handling policy across environments; environment-specific fail-open policy banned, Alternative A rejected) — drop the "fail-open in development" wording.
3. `REQ-016` and `REQ-019`: apply the Matrix-aligned option chosen per Design decisions for the rows at lines 31–36 and 17–22.
4. Leave lines 66–71 untouched (`REQ-017` blocked on approval).

### Method
- One row per edit, re-running the three consumer commands after each edit so any regression is attributable to a single row.

### Details
- The notes on the `eventbus.persistence-schema.bootstrap-ddl` row remain accurate after the source change ("Bootstrap DDL for eventbus.sqlite schema, backed by ADR-008").
- Registry entry validation requires every `source_paths` entry to exist under the repo root (`tools/check_canonical_source_registry.py` `RegistryEntry.validate`), so each new path must be checked before commit.

## Compatibility considerations

- The file is consumed by `tools/check_canonical_source_registry.py` (GV-020), `tools/check_canonical_source_conflicts.py` (GV-019/GV-021), and `tools/check_canonical_document_prose.py` (same `DEFAULT_REGISTRY_PATH`); all three must stay green (`AC-12`).
- rsynced by the deploy flow; no new deploy copy lines (Plan Assumptions).

## Security considerations

- N/A: configuration data-only change.

## Rollback considerations

- Single-commit revert of the TOML rows; no generated artifacts or database state are touched.

## Validation plan

- `uv run python tools/check_canonical_source_registry.py` — exit 0.
- `uv run python tools/check_canonical_source_conflicts.py` — exit 0.
- `uv run python tools/check_canonical_document_prose.py` — exit 0.
- Fixture-registry run via the tests in seq 09: the four fixture-confirmed conflicts disappear after the fixes (`AC-12`, `T12`).
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- `AC-12` holds: all three consumers exit 0 on the corrected registry; the four defective rows cite the Matrix/ADR-aligned claim types, sources, and notes; lines 66–71 are byte-identical to the pre-change file.

## Out of Scope

- `REQ-017` Matrix owner change (seq 05; approval-gated).
- Checker code fixes (seq 01/02) and the adrchk011 governance work.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix `eventbus.persistence-schema.bootstrap-ddl` source path (`REQ-014`) | Completed | 2026-11-19 | 2026-11-19 | `["scripts/eventbus/schema.sql"]` (2892 B, exists); three consumers re-run after the edit: all exit 0 |
| 2 | Fix `agent.posture-failure-handling` notes (`REQ-015`) | Completed | 2026-11-19 | 2026-11-19 | Notes rewritten to ADR-004 Group 1 item 1 wording; environment-specific fail-open wording dropped; consumers re-run: all exit 0 |
| 3 | Fix `governance.policy` and `overview.architecture-overview` rows (`REQ-016`, `REQ-019`) | Completed | 2026-11-19 | 2026-11-19 | UNK-04 decided (see record below); T12 corrected-rows test unskipped and passing |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-19 | 2026-11-19 | Three consumer commands exit 0; conflicts test file 201 passed / 0 skipped; TOML-only change (lint/type tools have no TOML scope; full suite runs at batch end) |

### Decision record (UNK-04, 2026-11-19)
- Chosen option for both disputed rows: re-point `source_paths` to `docs/00_governance/governance_02_documentation-metadata.md`, keeping `claim_type = "documentation-metadata"`. Chosen Matrix row: the Resolution Matrix `documentation-metadata` row (`governance_01_documentation-policy.md`, "Documentation Metadata … Canonical source kind `docs/00_governance/governance_02_documentation-metadata.md`"). The alternative (re-typing the claims) was rejected because no Matrix row names a canonical source kind that covers `governance_01_documentation-policy.md` or `docs/01_overview/overview_01_01-arch-process.md`; re-typing to `architecture-decision` would additionally require Accepted-ADR sources per the Matrix.
- `git diff` confirms exactly four rows changed; lines 66–71 (`mcp.component-mandatoriness`) are byte-identical (`REQ-017` stays approval-gated for seq 05).

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
- **Requirement ID**: `REQ-014` (bootstrap DDL path), `REQ-015` (posture notes), `REQ-016` (governance.policy row), `REQ-019` (overview claim type)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `config/documentation_canonical_sources.toml`
