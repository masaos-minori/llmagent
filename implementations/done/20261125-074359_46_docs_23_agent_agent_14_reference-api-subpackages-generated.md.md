## Goal

Regenerate the generated API reference after the new and modified reload and validation symbols, so the documented API surface matches the source rather than a hand-edited list (REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: the file contains an `AUTO-GENERATED` block guarded by `tools/generate_reference_table.py --check` (ADR-015 INV-01), so it is regenerated, never hand-edited.
- Verified against current source: the `agent_subpackages` domain has no manifest of its own and renders its guarded block from the `agent_api` manifest (`MANIFESTS_BY_DOMAIN`, `tools/generate_reference_table.py:536-539`; `_RENDER_MANIFEST`, `:558-560`), so refreshing it requires the manifest pass, not a `--type` domain run.
- Symbol scope, corrected during verification: `agent_14` covers only the `scripts/agent/` subpackages (`workflow/`, `services/`, `commands/`, `shared/`) at class and function granularity, not methods. In scope: the new modules from rows 7 and 8, the new error types from row 12, and the modified `services/` and `commands/` symbols from rows 3, 4, 5, 6, 9, 10, 11, 19, 20, 21, 22. Out of scope for this file: rows 1, 15, 16, 18 (`scripts/shared/`, which no generated-reference domain covers) and rows 13, 14, 17, 23, 24 (`scripts/agent/` top level, documented in `docs/23_agent/agent_13_reference-api-generated.md`).

## Design decisions
- Regeneration runs after the last code phase lands, so the reference reflects the final symbol set.

## Alternatives considered
- N/A: the guard fails on any hand edit.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure
Regenerate the manifest-backed reference blocks after the last code phase lands (R7, after R6), then confirm the guarded block matches the committed manifest.

### Method
- Run `uv run python tools/generate_reference_table.py --manifests` after R6 lands and commit the result. `--manifests` without `--type` writes `registry/manifests/agent_api.yaml` and re-renders every guarded doc block, including `agent_subpackages`.

### Details
- Only the `AUTO-GENERATED` block changes; the surrounding prose is untouched.
- `--type agent` refreshes only `agent_13`; `--manifests --type agent_subpackages` is rejected by the parser (`--type agent_subpackages has no contract manifests`), because that domain renders from the `agent_api` manifest written under `agent`.
- `agent_13` is not a target row of this Plan, but `build_agent_config` is listed there with its signature (`docs/23_agent/agent_13_reference-api-generated.md:48`), so any signature change row 13 makes must be checked by the same `--check` run.

## Compatibility considerations
- N/A: generated artifact.

## Security considerations
- N/A: the reference lists symbols, not values.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`

## Completion criteria
- The generated block lists the new reload, transaction, pending-state, and error symbols, and the check passes against the source.

## Out of Scope
- The symbol definitions (rows 1, 7, 8, 12) and the ownership manifest (row 45).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-211000 | 20261125-213153 | runs after Phase 6 R7 run 20261125: guarded block re-rendered from the agent_api manifest; the reload, transaction, pending-state, and undo symbols are listed; --check reports no drift and the docs checkers pass |
| 2 | Run the generated-artifact check (`rules/tool-gates.md`) | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: guarded block re-rendered from the agent_api manifest; the reload, transaction, pending-state, and undo symbols are listed; --check reports no drift and the docs checkers pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The regenerated index grew past the `SIZE_EXCEPTIONS` ceiling for this file four times across the release units (33078 to 36973), because each phase added public symbols to the `scripts/agent/` subpackages. Re-accepted at 36973 in `tools/check_docs_structure.py`, each step recorded with its reason | Yes | 2026-11-25 |
| 1 | That re-acceptance pushed `tools/check_docs_structure.py` past its recorded size ceiling (25584 to 27059), which the tools size baseline reports as a regression. Re-recorded at 27059 in `tools/check_module_size_tools_baseline.txt` with the reason | Yes | 2026-11-25 |
| 1 | `tools/check_docstrings.py` splits the whole module docstring on the em-dash separator and requires exactly two parts, so a Responsibilities list that uses the separator makes the description empty. The transaction module's docstring now carries one em-dash in the header line and lists its responsibilities without it | Yes | 2026-11-25 |
| 2 | `--check` reports no drift and the generated block lists the reload, transaction, pending-state, and undo symbols. The one `check_docs_consistency.py --domain agent` warning (`/db` not a registered command at line 49) is identical on `master` and outside this Plan's scope | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-014
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`