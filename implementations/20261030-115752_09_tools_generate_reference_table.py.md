# Implementation Procedure: `tools/generate_reference_table.py`

## Goal

Add a mandatoriness guard-block generator so the `agent_08_04` Component Criticality Classification table is rendered from the registry (REQ-005: `agent_08_04` table becomes an AUTO-GENERATED guard block via this tool, ADR-015 pattern).

## Scope

- `tools/generate_reference_table.py`: new domain entry `mandatoriness` in the existing domain maps (`DOMAIN_GENERATORS` block :296-307, `DOMAIN_DOCS` :310-316, `DOMAIN_GUARDS` :317-322, `DOMAIN_WELCOME_LINES` :324-331, `DOMAIN_HEADING` :333-338) and a new generator function.
- No rendered-doc edits in this row (the `agent_08_04` conversion is row 26).

## Assumptions

- Row 1's registry file exists with the `rationale` field so the table's third column renders from the registry (row 1 Design decision).
- Cross-plan collision (four Frozen plans target this file: adrauth001 row 11, dlqbox001 row 14, adrcov001 row 05, this row): landing order adrcov001 row 05 (manifest-IR refactor) → this row. If this row lands first, implement with the plain domain-map pattern below and let adrcov001 row 05 re-express it as a manifest. Needs Confirmation: final sequencing at implementation time (recorded in both plans' Dependencies; adrcov001 is blocked by this plan for its component-mandatoriness manifest, so a conflict here is coordination work, not a merge race).
- adrcov001 U-2 (whether contract manifests consume this registry file directly): if adrcov001 row 05 landed, register the registry as a manifest source instead of reading YAML ad hoc (Details).

## Design decisions

- Follow the existing domain pattern exactly: marker constant `GUARD_START_MANDATORINESS` (new) = `<!-- AUTO-GENERATED: generate_reference_table.py component-mandatoriness-classification -->`, reusing `GUARD_END` (:50); wire into all five `DOMAIN_*` maps so `--type mandatoriness`, `--check`, and `--all` handle it like the other domains (the CLI already iterates the maps; no new flag plumbing).
- Generator `generate_mandatoriness_table()` (new): `load_component_mandatoriness()` (row 2) → sort entries by `component_id` (new) → render the three-column markdown table (`Server (`config/agent.toml` key) | Classification | Rationale`) exactly matching the current hand-written table shape in `agent_08_04` :56-66 so row 26's conversion is a copy-under-markers, not a re-render surprise.
- `DOMAIN_HEADING["mandatoriness"]` = `#### Component Criticality Classification` — the existing heading at `agent_08_04` :41 becomes the guard-block heading row's match target (verify how `render_updated_doc` (:342) anchors heading vs body before wiring; adjust so the heading stays outside the markers if the renderer anchors on body text only).

## Alternatives considered

- A dedicated standalone script for this one table — rejected: plan REQ-005 names `tools/generate_reference_table.py`'s guard-block pattern (ADR-015) explicitly, and a second generator duplicates the drift machinery row 8 then has to cross-check.
- Rendering the table from `config/agent.toml` `required` values — rejected: config is the effective-value side; the registry is the authority (ADR-004 item 13).

## Implementation

### Target file

`tools/generate_reference_table.py`

### Procedure

1. Add `GUARD_START_MANDATORINESS` (new) next to the sibling markers (:47-56).
2. Implement `generate_mandatoriness_table()` (new) near the other domain generators; import the row-2 loader (`load_component_mandatoriness` (new), (new) until row 2 lands).
3. Register `mandatoriness` in the five `DOMAIN_*` maps with a welcome line: "Generated from `registry/component_mandatoriness.yaml`. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type mandatoriness` to refresh."
4. Verify `check_drift` (:357) covers the new domain through the maps (it iterates domains; no edit expected).

### Method

Extension by registration into the existing map-driven design; keep the `--check` output contract (`DRIFT:` lines, exit 1) unchanged for CI.

### Details

- If adrcov001 row 05's manifest IR (`build_manifest` (new)/`load_manifest` (new), both (new) at current HEAD) is present, add a `component_mandatoriness` (new) manifest entry so the table generator and drift checker share the manifest layer; otherwise read the YAML via the row-2 loader directly. Either path renders the same markdown.
- Table cell escaping: rationale text contains no pipes today; still pipe-escape generically.

## Compatibility considerations

- `--check` is already a CI step (`.github/workflows/ci.yml:35`); after row 26 converts `agent_08_04`, `--check` will demand the guarded table — land 09 and 26 in the same commit group to avoid a red `--check` between them.
- adrcov001 row 05 reorganizes the same maps; rebase semantics: keep this row's registrations additive and conflict-free.

## Security considerations

- Generated table is the drift-checked authority surface for operator classification reading (row 8 check 3 verifies it stays generated).

## Rollback considerations

- Remove the domain registrations + generator; must be reverted together with row 26 (docs revert re-introduces the hand-written table).

## Validation plan

- `uv run python tools/generate_reference_table.py --type mandatoriness` renders; `--check` exits 0 after row 26 lands.
- `uv run ruff check tools`, `uv run mypy scripts` per `rules/toolchain.md`; existing generator tests under `tests/tools/` stay green (adrcov001 row 18 adds generator tests — coordinate: keep this domain covered there too, Needs Confirmation at merge).

## Completion criteria

- `--check` proves the rendered table equals the registry-derived output, and removing/altering any registry entry changes the rendered table (plan AC-4 precondition; drift checker row 8 then enforces the three-way match).

## Out of Scope

- `agent_08_04` file conversion (row 26), the drift checker (row 8), registry content (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add marker, generator, domain registrations per Procedure | Pending | — | — | Needs rows 1, 2 |
| 2 | Generator test coverage (coordinate with adrcov001 row 18) | Pending | — | — | Needs Confirmation |
| 3 | Run `--type mandatoriness` + `--check` + toolchain gates | Pending | — | — | `--check` green only with row 26 |
| 4 | N/A: doc conversion is row 26 | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Registry + loader (rows 1-2) must exist; sequence vs adrcov001 row 05 refactor needs coordination | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (classification table becomes a generated guard block from the registry)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tools/generate_reference_table.py`
