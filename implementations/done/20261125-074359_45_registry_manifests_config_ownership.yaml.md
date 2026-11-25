## Goal

Regenerate the config ownership manifest from the modified field registry, so the generated artifact
matches the registry's `hot_reloadable` and validator wiring rather than a hand-edited list (REQ-003,
startup-only fields stay pending; REQ-010, registry completeness; REQ-014, documentation).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: `registry/manifests/config_ownership.yaml` is generated from `scripts/agent/services/config_field_registry.py` (`CONFIG_FIELD_REGISTRY_SRC`, `tools/generate_reference_table.py:63`; `_MANIFEST_SOURCES["config_ownership"]`, `:523`); it is never hand-edited.
- Verified against current source: `config_ownership` is an unbound manifest — it has no guarded doc block of its own (`UNBOUND_MANIFESTS`, `tools/generate_reference_table.py:546-550`) — so it is refreshed only by the manifest pass, not by a `--type` domain run.
- The registry gains `field_type` and `allow_empty` in row 4, so the regenerated manifest is the record of that change.

## Design decisions
- The manifest is regenerated after the registry lands, so the artifact and the source cannot disagree.
- No manifest field is added by hand; a new column would require changing the generator, which is out of
  scope here.

## Alternatives considered
- Hand-editing the manifest to match the plan — rejected: the generator is the source of truth.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`

### Procedure
Regenerate the manifest after row 4 lands, in the R7 run, then confirm the committed artifact matches the registry.

### Method
- Run `uv run python tools/generate_reference_table.py --manifests` after row 4 lands and commit the result. `--manifests` without `--type` writes every registered manifest, including the unbound `config_ownership`.

### Details
- The regenerated file must show every entry with a validator and the hot-reloadable subset unchanged in membership except for the fields row 4 declares.
- `--type config_ownership` is not a valid invocation: `config_ownership` is a manifest name, not a doc-backed domain.

## Compatibility considerations
- N/A: generated artifact; consumers read it as data.

## Security considerations
- N/A: the manifest records field ownership, not values.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` (no `--type`: the unbound-manifest drift check only runs when `--type` is omitted; `--check` takes precedence over `--manifests` in `main()`, so combining them is misleading)

## Completion criteria
- The check passes against the modified registry, and the committed manifest differs from the previous
  version only by the registry change row 4 made.

## Out of Scope
- The registry itself (row 4).
- The generated API reference (row 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-211000 | 20261125-213153 | runs after row 4 R7 run 20261125: manifest refreshed by the manifest pass; the committed artifact differs from the previous version only by the 18 entries that gained a validator name; generate_reference_table --check reports no drift |
| 2 | Run the generated-artifact check (`rules/tool-gates.md`) | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: manifest refreshed by the manifest pass; the committed artifact differs from the previous version only by the 18 entries that gained a validator name; generate_reference_table --check reports no drift |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The manifest pass depends on the generator change that landed with row 4: `tools/generate_reference_table.py::_config_ownership_entries` accepted only 3-4 positional args and no keywords, so the registry's new `field_type` positional and `allow_empty` keyword raised "unexpected ConfigFieldRegistry call shape". The generator now accepts 3-5 positional args and an `allow_empty` keyword, validates each as a literal, and leaves both out of the emitted entry | Yes | 2026-11-25 |
| 1 | That generator growth pushed `tools/generate_reference_table.py` past its recorded size ceiling (52080 to 52945), which the tools size baseline reports as a regression. Re-recorded at 52945 in `tools/check_module_size_tools_baseline.txt` with the reason, following the precedent of the earlier re-record commit | Yes | 2026-11-25 |
| 2 | `--check` reports no drift, and the committed manifest differs from the previous version only by the 18 entries that gained a validator name where the registry previously had none | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-010 (registry completeness), REQ-014 (documentation); AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `registry/manifests/config_ownership.yaml`